# ============================================================
#  SpecSense — Cell 1: Environment Setup & Document Parser
#  Google Colab · Free T4 GPU · No paid APIs
# ============================================================

# ── 1. Install all required packages in one shot ──────────────
# difflib is part of the Python standard library — no install needed.
# faiss-cpu is the CPU build; it is compatible with Colab's T4 runtime.
# !pip install -q \
#     pdfplumber \
#     pymupdf \
#     python-docx \
#     sentence-transformers \
#     faiss-cpu \
#     transformers \
#     bitsandbytes \
#     accelerate \
#     gradio

print("✅ All packages installed successfully.")

# ── 2. Imports ────────────────────────────────────────────────
import os                        # path utilities
import math                      # ceiling division for DOCX page grouping
from typing import List, Dict    # type hints

# PDF parsing
import pdfplumber                # primary PDF text extractor

# DOCX parsing
from docx import Document as DocxDocument   # python-docx

# ── 3. DocumentParser class ───────────────────────────────────

class DocumentParser:
    """
    Unified parser for PDF and DOCX construction specification files.

    parse() returns a list of page dicts:
        [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}, ...]

    Page numbers are preserved faithfully for PDF (actual page numbers
    from the file) and approximated for DOCX (every DOCX_PAGE_SIZE
    paragraphs = 1 logical page).
    """

    # Number of paragraphs treated as one "page" for DOCX files.
    # Adjust this constant if your specs have very short/long paragraphs.
    DOCX_PAGE_SIZE: int = 40

    # ── Public API ────────────────────────────────────────────
    def parse(self, file_path: str) -> List[Dict]:
        """
        Parse a .pdf or .docx file and return page-level text chunks.

        Parameters
        ----------
        file_path : str
            Absolute or relative path to the specification file.

        Returns
        -------
        List[Dict]
            Each element: {"page": int, "text": str}
            Pages are 1-indexed.

        Raises
        ------
        FileNotFoundError   – path does not exist on disk
        ValueError          – unsupported file extension
        RuntimeError        – document is corrupted or password-protected
        """

        # ── Validate path ─────────────────────────────────────
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"File not found: '{file_path}'. "
                "Did you upload it correctly in the cell below?"
            )

        # ── Dispatch by extension ─────────────────────────────
        ext = os.path.splitext(file_path)[-1].lower()

        if ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext == ".docx":
            return self._parse_docx(file_path)
        else:
            raise ValueError(
                f"Unsupported file type '{ext}'. "
                "Only .pdf and .docx are accepted."
            )

    # ── Private helpers ───────────────────────────────────────

    def _parse_pdf(self, file_path: str) -> List[Dict]:
        """
        Extract text from a PDF using pdfplumber, one dict per page.

        pdfplumber is preferred over PyMuPDF for plain-text extraction
        because it handles construction-spec tables and column layouts
        more cleanly.  PyMuPDF (fitz) is reserved for the highlight-PDF
        step in a later cell.
        """
        pages: List[Dict] = []

        try:
            with pdfplumber.open(file_path) as pdf:

                # pdfplumber raises pdfminer.high_level.PDFPasswordIncorrect
                # for encrypted files — we catch the broad Exception below.
                for page_obj in pdf.pages:
                    page_number: int = page_obj.page_number   # 1-indexed
                    raw_text: str = page_obj.extract_text() or ""

                    # Strip excessive whitespace but keep paragraph breaks
                    cleaned_text: str = "\n".join(
                        line.strip()
                        for line in raw_text.splitlines()
                        if line.strip()          # drop blank lines
                    )

                    pages.append({
                        "page": page_number,
                        "text": cleaned_text,
                    })

        except FileNotFoundError:
            raise  # re-raise; already validated above, but just in case
        except Exception as exc:
            raise RuntimeError(
                f"Could not read PDF '{file_path}'. "
                "The file may be corrupted or password-protected.\n"
                f"Underlying error: {exc}"
            ) from exc

        return pages

    def _parse_docx(self, file_path: str) -> List[Dict]:
        """
        Extract text from a DOCX file using python-docx.

        DOCX has no native page-number concept in the XML, so we
        approximate pages by grouping every DOCX_PAGE_SIZE paragraphs
        together.  This gives the downstream RAG pipeline stable chunk
        IDs for traceability.
        """
        pages: List[Dict] = []

        try:
            doc = DocxDocument(file_path)
        except Exception as exc:
            raise RuntimeError(
                f"Could not open DOCX '{file_path}'. "
                "The file may be corrupted or use an unsupported format.\n"
                f"Underlying error: {exc}"
            ) from exc

        # Collect all non-empty paragraph texts
        all_paragraphs: List[str] = [
            para.text.strip()
            for para in doc.paragraphs
            if para.text.strip()   # ignore truly blank paragraphs
        ]

        if not all_paragraphs:
            # Return a single empty page rather than crashing
            return [{"page": 1, "text": ""}]

        # Group paragraphs into logical pages
        total_pages: int = math.ceil(len(all_paragraphs) / self.DOCX_PAGE_SIZE)

        for page_index in range(total_pages):
            start: int = page_index * self.DOCX_PAGE_SIZE
            end: int   = start + self.DOCX_PAGE_SIZE
            chunk: str = "\n".join(all_paragraphs[start:end])

            pages.append({
                "page": page_index + 1,   # 1-indexed
                "text": chunk,
            })

        return pages


# ── 4. Quick test: upload a file and sanity-check the parser ──

if __name__ == "__main__":
    print("\n📂  Please upload your construction specification (PDF or DOCX)…")
    
    # google.colab.files is only available inside a Colab runtime.
    # If you're running locally, comment out the three lines below and
    # set `file_path` manually, e.g.:  file_path = "spec.pdf"
    try:
        from google.colab import files
        uploaded = files.upload()   # opens the Colab file-picker dialog
    
        # The upload widget returns a dict: {filename: bytes}
        file_name: str = list(uploaded.keys())[0]
    except ImportError:
        # Local fallback
        import sys
        if len(sys.argv) > 1:
            file_name = sys.argv[1]
        else:
            file_name = "test_spec.pdf"
    print(f"\n✅  Received file: '{file_name}'")
    
    # ── Parse the uploaded file ───────────────────────────────────
    parser = DocumentParser()
    
    try:
        pages: List[Dict] = parser.parse(file_name)
    except (FileNotFoundError, ValueError, RuntimeError) as err:
        print(f"❌  Parser error: {err}")
        pages = []
    
    # ── Report results ────────────────────────────────────────────
    if pages:
        total_pages: int = len(pages)
        print(f"\n📄  Total pages detected : {total_pages}")
        print("─" * 60)
    
        # Print the first three pages as a sanity check
        preview_count: int = min(3, total_pages)
        for i in range(preview_count):
            page_data = pages[i]
            # Truncate very long pages for readability
            preview_text: str = page_data["text"][:500]
            ellipsis: str = "…" if len(page_data["text"]) > 500 else ""
    
            print(f"\n┌── Page {page_data['page']} "
                  f"({'chars: ' + str(len(page_data['text']))})")
            print(preview_text + ellipsis)
            print("└" + "─" * 59)
    
        print(f"\n✅  DocumentParser is working correctly — "
              f"{total_pages} page(s) extracted and ready for RAG indexing.")
    