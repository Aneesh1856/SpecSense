# ============================================================
#  SpecSense — Cell 2: Semantic Chunker + FAISS Index Builder
#  Depends on: Cell 1 (DocumentParser, `pages` variable)
# ============================================================

import re                             # regex for section-label detection
import math                           # ceiling division
from typing import List, Dict, Tuple  # type hints

import numpy as np                    # vector normalisation
import faiss                          # vector similarity search
from sentence_transformers import SentenceTransformer  # free embedding model

# ══════════════════════════════════════════════════════════════
#  CLASS 1 — SemanticChunker
# ══════════════════════════════════════════════════════════════

class SemanticChunker:
    """
    Splits page-level text into overlapping word-window chunks and
    attaches a construction-domain section label to every chunk.

    Why overlapping windows?
    ────────────────────────
    A key sentence about curing temperatures might sit at the boundary
    of two non-overlapping chunks and be missed by the retriever.
    Overlapping windows ensure boundary context is always captured.
    """

    # ── Keyword map used by detect_section_label ──────────────
    # Each entry: label -> list of lowercase keyword fragments.
    # Fragments are matched as substrings (no word-boundary required)
    # so "vibrat" matches "vibration", "vibrator", "vibrating", etc.
    _KEYWORD_MAP: Dict[str, List[str]] = {
        "MATERIALS":  [
            "aggregate", "cement", "water", "admixture",
            "fly ash", "flyash", "sand", "gravel", "coarse",
            "fine aggregate", "supplementary", "additive",
        ],
        "PROCEDURE":  [
            "mixing", "placing", "placement", "compaction",
            "curing", "batching", "pouring", "pour", "vibrat",
            "casting", "finishing", "levelling", "leveling",
            "consolidat", "transportation", "discharge",
        ],
        "EQUIPMENT":  [
            "plant", "mixer", "vibrator", "pump", "transit",
            "crane", "formwork", "shuttering", "truck", "chute",
            "conveyor", "batch", "hopper", "transit mixer",
        ],
        "STANDARDS":  [
            "is:", "is 383", "is 456", "is 10262", "is 4926",
            "clause", " code", "specification", "conform",
            "standard", "astm", "bs ", "en ", "aci ", "irc",
        ],
        "PERSONNEL":  [
            "engineer-in-charge", "engineer in charge",
            "supervisor", "inspector", "quality", " qc ",
            "officer", "foreman", "technician", "site engineer",
            "project manager",
        ],
        # GENERAL is the fallback — applied when nothing else matches
    }

    # ── Public API ────────────────────────────────────────────

    def chunk(
        self,
        pages: List[Dict],
        chunk_size: int = 400,
        overlap: int = 80,
    ) -> List[Dict]:
        """
        Split every page's text into overlapping word-window chunks.

        Parameters
        ----------
        pages      : output of DocumentParser.parse()  (list of page dicts)
        chunk_size : target window size in words
        overlap    : number of words shared between consecutive chunks
                     on the same page

        Returns
        -------
        List[Dict] with keys:
            chunk_id      – globally unique int (0-indexed)
            page          – source page number (from the original document)
            text          – chunk text string
            char_start    – character offset of the first word in the page text
            char_end      – character offset after the last word in the page text
            section_label – domain label string
        """
        if chunk_size <= overlap:
            raise ValueError(
                f"chunk_size ({chunk_size}) must be greater than overlap ({overlap})."
            )

        all_chunks: List[Dict] = []
        global_chunk_id: int = 0
        step: int = chunk_size - overlap      # how far we advance each window

        for page_dict in pages:
            page_num: int  = page_dict["page"]
            full_text: str = page_dict["text"]

            # ── Tokenise by whitespace ─────────────────────────
            # We keep track of character offsets so we can highlight
            # exact spans back in the PDF in a later cell.
            words: List[str] = full_text.split()
            if not words:
                # Empty page — still emit one stub chunk so page IDs are traceable
                all_chunks.append({
                    "chunk_id":     global_chunk_id,
                    "page":         page_num,
                    "text":         "",
                    "char_start":   0,
                    "char_end":     0,
                    "section_label": "GENERAL",
                })
                global_chunk_id += 1
                continue

            # Build char-offset index: word_offsets[i] = start char of words[i]
            word_offsets: List[int] = self._build_word_offsets(full_text, words)

            # ── Slide window over words ────────────────────────
            num_words: int = len(words)
            start_idx: int = 0

            while start_idx < num_words:
                end_idx: int = min(start_idx + chunk_size, num_words)

                chunk_words: List[str] = words[start_idx:end_idx]
                chunk_text: str        = " ".join(chunk_words)

                # Character offsets within the page text
                char_start: int = word_offsets[start_idx]
                # end offset = start of last word + its length
                char_end: int   = word_offsets[end_idx - 1] + len(words[end_idx - 1])

                # Detect which construction domain this chunk belongs to
                label: str = self.detect_section_label(chunk_text)

                all_chunks.append({
                    "chunk_id":     global_chunk_id,
                    "page":         page_num,
                    "text":         chunk_text,
                    "char_start":   char_start,
                    "char_end":     char_end,
                    "section_label": label,
                })

                global_chunk_id += 1

                # Advance window; stop if we've covered all words
                if end_idx == num_words:
                    break
                start_idx += step

        return all_chunks

    def detect_section_label(self, chunk_text: str) -> str:
        """
        Heuristically classify a text chunk into a construction domain.

        Strategy: lowercase the text, then count keyword hits for each
        category.  The category with the most hits wins.  Ties are
        broken by the order in _KEYWORD_MAP (MATERIALS > PROCEDURE > …).
        Returns "GENERAL" if no keywords match.

        Parameters
        ----------
        chunk_text : raw text string of a single chunk

        Returns
        -------
        str — one of: MATERIALS | PROCEDURE | EQUIPMENT |
                       STANDARDS | PERSONNEL | GENERAL
        """
        lower_text: str = chunk_text.lower()

        best_label: str = "GENERAL"
        best_score: int = 0

        for label, keywords in self._KEYWORD_MAP.items():
            score: int = sum(
                1 for kw in keywords
                if kw in lower_text          # simple substring match
            )
            if score > best_score:
                best_score = score
                best_label = label

        return best_label

    # ── Private helpers ───────────────────────────────────────

    @staticmethod
    def _build_word_offsets(full_text: str, words: List[str]) -> List[int]:
        """
        Return the character-start index of every word inside full_text.

        We scan forward through full_text so that multi-space gaps and
        newlines are accounted for correctly.
        """
        offsets: List[int] = []
        search_start: int  = 0

        for word in words:
            # find() is O(n) but text is short enough that this is fine
            idx: int = full_text.find(word, search_start)
            offsets.append(idx)
            search_start = idx + len(word)

        return offsets


# ══════════════════════════════════════════════════════════════
#  CLASS 2 — FAISSIndexBuilder
# ══════════════════════════════════════════════════════════════

class FAISSIndexBuilder:
    """
    Embeds chunk texts with a lightweight sentence-transformer model
    and stores them in a FAISS IndexFlatIP for cosine-similarity search.

    Model choice: "all-MiniLM-L6-v2"
    ──────────────────────────────────
    • 22 M parameters  → fits easily in Colab free RAM alongside Mistral-7B
    • 384-dimensional embeddings  → FAISS index is tiny
    • Strong performance on sentence retrieval benchmarks
    • Downloaded once; cached by HuggingFace Hub automatically
    """

    # Embedding model identifier (HuggingFace Hub)
    MODEL_NAME: str = "all-MiniLM-L6-v2"

    def __init__(self) -> None:
        print(f"⏳  Loading embedding model '{self.MODEL_NAME}'…")
        # SentenceTransformer auto-selects GPU if available (free T4 in Colab)
        self._model: SentenceTransformer = SentenceTransformer(self.MODEL_NAME)
        print(f"✅  Embedding model loaded "
              f"(dim={self._model.get_sentence_embedding_dimension()}).")

    # ── Public API ────────────────────────────────────────────

    def build(
        self,
        chunks: List[Dict],
    ) -> Tuple[faiss.Index, List[Dict]]:
        """
        Embed all chunks and build a FAISS cosine-similarity index.

        Parameters
        ----------
        chunks : list of chunk dicts from SemanticChunker.chunk()

        Returns
        -------
        (faiss_index, chunks)
            faiss_index – IndexFlatIP ready for .search()
            chunks      – same list passed in (returned for convenience
                          so caller can store both in one tuple)
        """
        print(f"🔢  Embedding {len(chunks)} chunks…")

        # Extract raw texts; FAISS needs a clean list of strings
        texts: List[str] = [c["text"] for c in chunks]

        # Encode in one batched call — SentenceTransformer handles batching
        # convert_to_numpy=True gives us a float32 ndarray directly
        embeddings: np.ndarray = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            batch_size=64,           # safe default for Colab T4
        )                            # shape: (num_chunks, embedding_dim)

        # ── Normalise to unit length ───────────────────────────
        # With L2-normalised vectors, inner-product = cosine similarity.
        # This lets us use the fast IndexFlatIP without a separate
        # cosine-distance index type.
        faiss.normalize_L2(embeddings)

        # ── Build index ────────────────────────────────────────
        embedding_dim: int = embeddings.shape[1]
        index: faiss.Index = faiss.IndexFlatIP(embedding_dim)
        index.add(embeddings)        # add all vectors at once

        print(f"✅  FAISS index built — {index.ntotal} vectors, dim={embedding_dim}.")
        return index, chunks

    def search(
        self,
        query: str,
        faiss_index: faiss.Index,
        chunks: List[Dict],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Retrieve the top-k most semantically similar chunks for a query.

        Parameters
        ----------
        query       : natural-language question or section heading
        faiss_index : index returned by build()
        chunks      : chunk list returned by build()
        top_k       : number of results to return

        Returns
        -------
        List[Dict] — copies of the matched chunk dicts, each with an
        additional key "similarity_score" (float, range 0–1 after
        normalisation; higher = more similar).
        """
        # ── Embed and normalise the query ──────────────────────
        query_vec: np.ndarray = self._model.encode(
            [query],
            convert_to_numpy=True,
        )                            # shape: (1, embedding_dim)
        faiss.normalize_L2(query_vec)

        # ── Search ─────────────────────────────────────────────
        # FAISS returns two arrays of shape (1, top_k):
        #   scores  – inner-product values (≈ cosine similarity after norm)
        #   indices – positions in the index (= chunk list positions)
        scores: np.ndarray
        indices: np.ndarray
        scores, indices = faiss_index.search(query_vec, top_k)

        # ── Build result list ──────────────────────────────────
        results: List[Dict] = []
        for rank, (score, idx) in enumerate(
            zip(scores[0], indices[0])
        ):
            if idx == -1:
                # FAISS returns -1 when fewer than top_k results exist
                continue

            # Make a shallow copy so we don't mutate the original chunk
            result: Dict = dict(chunks[idx])
            result["similarity_score"] = float(score)
            results.append(result)

        return results


# ══════════════════════════════════════════════════════════════
#  PIPELINE — Run on `pages` from Cell 1
# ══════════════════════════════════════════════════════════════

# ── Step A: Chunk the parsed pages ────────────────────────────
print("\n" + "═" * 60)
print("  STEP A — Semantic Chunking")
print("═" * 60)

chunker  = SemanticChunker()
chunks: List[Dict] = chunker.chunk(
    pages,           # `pages` variable populated by Cell 1's test harness
    chunk_size=400,  # words per window  (tune down if GPU OOM on large docs)
    overlap=80,      # words shared between consecutive windows
)

total_chunks: int = len(chunks)
print(f"\n📦  Total chunks created : {total_chunks}")

# ── Section label distribution ─────────────────────────────────
print("\n📊  Section label distribution:")
print("─" * 40)

from collections import Counter
label_counts: Counter = Counter(c["section_label"] for c in chunks)

# Sort by count descending for readability
for label, count in label_counts.most_common():
    bar: str = "█" * int(count / max(label_counts.values()) * 30)
    pct: float = count / total_chunks * 100
    print(f"  {label:<12} {count:>4} chunks  ({pct:5.1f}%)  {bar}")

# ── Step B: Build FAISS index ──────────────────────────────────
print("\n" + "═" * 60)
print("  STEP B — FAISS Index Building")
print("═" * 60)

builder = FAISSIndexBuilder()
faiss_index, chunks = builder.build(chunks)

# ── Step C: Smoke-test retrieval with a sample query ───────────
print("\n" + "═" * 60)
print("  STEP C — Retrieval Smoke Test")
print("═" * 60)

SAMPLE_QUERY: str = "What are the curing requirements for concrete?"
print(f"\n🔍  Query: \"{SAMPLE_QUERY}\"")
print("─" * 60)

results: List[Dict] = builder.search(
    query       = SAMPLE_QUERY,
    faiss_index = faiss_index,
    chunks      = chunks,
    top_k       = 3,
)

for rank, res in enumerate(results, start=1):
    preview: str = res["text"][:300].replace("\n", " ")
    ellipsis: str = "…" if len(res["text"]) > 300 else ""
    print(
        f"\n  [{rank}]  page={res['page']}  "
        f"label={res['section_label']}  "
        f"score={res['similarity_score']:.4f}\n"
        f"      {preview}{ellipsis}"
    )

print("\n✅  Cell 2 complete — `faiss_index` and `chunks` ready for Cell 3 (LLM generation).")
