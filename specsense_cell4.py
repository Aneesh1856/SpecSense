# ============================================================
#  SpecSense — Cell 4: Extraction Agents
#  Depends on: Cell 2 (FAISSIndexBuilder, chunks), Cell 3 (LLM Helpers)
# ============================================================

from typing import List, Dict, Any

# ── 1. Extraction Agent Class ─────────────────────────────────
print("═" * 60)
print("  STEP 1 — Defining ExtractionAgent Class")
print("═" * 60)

class ExtractionAgent:
    """
    An agent dedicated to extracting specific information from a 
    document section using FAISS retrieval and Mistral-7B JSON extraction.
    """

    def __init__(
        self, 
        agent_name: str, 
        target_section: str, 
        extraction_queries: List[str]
    ) -> None:
        self.agent_name = agent_name
        self.target_section = target_section
        self.extraction_queries = extraction_queries

    def _build_context(self, search_results: List[Dict]) -> str:
        """
        Formats FAISS search results into a single context string for the LLM.
        """
        context_parts = []
        for rank, chunk in enumerate(search_results, start=1):
            # Include page number to help LLM cite the source
            context_parts.append(
                f"[Document Page: {chunk['page']}]\n{chunk['text']}"
            )
        return "\n\n---\n\n".join(context_parts)

    def extract(
        self, 
        faiss_index: Any, 
        chunks: List[Dict], 
        builder: Any, 
        top_k: int = 6
    ) -> List[Dict]:
        """
        Executes extraction queries against the document.

        Parameters
        ----------
        faiss_index : faiss.Index built in Cell 2
        chunks      : List of all chunk dicts built in Cell 2
        builder     : FAISSIndexBuilder instance to perform the search
        top_k       : Number of chunks to retrieve per query

        Returns
        -------
        List of extraction result dicts.
        """
        print(f"\n🚀 Starting {self.agent_name} ({len(self.extraction_queries)} queries)")
        results: List[Dict] = []

        for query in self.extraction_queries:
            # 1. Search FAISS for relevant chunks
            search_results: List[Dict] = builder.search(
                query=query, 
                faiss_index=faiss_index, 
                chunks=chunks, 
                top_k=top_k
            )

            # 2. Filter / Prioritize chunks based on target_section
            # Note: We keep chunks that match the section, or high similarity general chunks
            # For simplicity, we'll just sort the retrieved chunks, bringing target section to the top.
            search_results.sort(
                key=lambda x: (x.get("section_label") == self.target_section, x.get("similarity_score", 0)), 
                reverse=True
            )
            
            context: str = self._build_context(search_results)

            # 3. Build strict extraction prompt
            prompt: str = f"""You are a construction specification analyst. Read the following passages from a 
construction specification document and extract ONLY information that is explicitly 
stated in the text. Do NOT add any information from your general knowledge.
If the information is not present in the passages, respond with: {{"value": "NOT_FOUND"}}

PASSAGES:
{context}

QUESTION: {query}

Respond ONLY with valid JSON in this exact format:
{{
  "value": "the extracted information exactly as stated",
  "source_page": <page number as integer>,
  "source_clause": "the clause or section reference e.g. 4.1.1.3",
  "verbatim_snippet": "the exact sentence or phrase from the text that supports this"
}}"""

            # 4. Call LLM
            print(f"  🔍 Query: {query}")
            extracted_json = llm_extract_json(prompt)

            # 5. Process Result
            if extracted_json:
                results.append({
                    "agent": self.agent_name,
                    "field": query,
                    "value": extracted_json.get("value", "NOT_FOUND"),
                    "source_page": extracted_json.get("source_page", -1),
                    "source_clause": extracted_json.get("source_clause", ""),
                    "verbatim_snippet": extracted_json.get("verbatim_snippet", ""),
                    "confidence": 0.9 if extracted_json.get("value") != "NOT_FOUND" else 0.0 # Placeholder for confidence
                })
            else:
                results.append({
                    "agent": self.agent_name,
                    "field": query,
                    "value": "JSON_PARSE_ERROR",
                    "source_page": -1,
                    "source_clause": "",
                    "verbatim_snippet": "",
                    "confidence": 0.0
                })

        return results

# ── 2. Instantiate Agents ─────────────────────────────────────
print("\n" + "═" * 60)
print("  STEP 2 — Initialising Specialised Agents")
print("═" * 60)

# AGENT 1 — Materials
materials_agent = ExtractionAgent(
    agent_name="Materials Agent",
    target_section="MATERIALS",
    extraction_queries=[
        "What type of cement should be used and what are its requirements?",
        "What are the requirements for coarse aggregate including size and grading?",
        "What are the requirements for fine aggregate or sand?",
        "What is the maximum water-cement ratio allowed?",
        "What admixtures or fly ash can be used in concrete?",
        "What are the deleterious material limits for aggregates?"
    ]
)

# AGENT 2 — Procedure
procedure_agent = ExtractionAgent(
    agent_name="Procedure Agent",
    target_section="PROCEDURE",
    extraction_queries=[
        "What is the procedure for batching and mixing concrete?",
        "What are the requirements for placing and pouring concrete?",
        "How should concrete be compacted or vibrated?",
        "What are the curing requirements and duration for concrete?",
        "What are the minimum concrete grades or mix proportions specified?",
        "What are the requirements for formwork?"
    ]
)

# AGENT 3 — Equipment
equipment_agent = ExtractionAgent(
    agent_name="Equipment Agent",
    target_section="EQUIPMENT",
    extraction_queries=[
        "What equipment or machinery is required for concrete batching and mixing?",
        "What type of vibrators or compaction equipment is specified?",
        "What transport equipment is needed for concrete delivery?",
        "What testing equipment is required for quality control?"
    ]
)

# AGENT 4 — Standards
standards_agent = ExtractionAgent(
    agent_name="Standards Agent",
    target_section="STANDARDS",
    extraction_queries=[
        "What IS codes or Indian Standards are referenced?",
        "What CPWD specifications or clauses are referenced?",
        "What testing standards must concrete comply with?",
        "What are the acceptance criteria or tolerances specified?"
    ]
)

# AGENT 5 — Personnel
personnel_agent = ExtractionAgent(
    agent_name="Personnel Agent",
    target_section="PERSONNEL",
    extraction_queries=[
        "Who is the Engineer-in-Charge and what are their responsibilities?",
        "What quality control personnel or inspectors are required?",
        "What approvals or sign-offs are required before concreting?"
    ]
)

agents: List[ExtractionAgent] = [
    materials_agent,
    procedure_agent,
    equipment_agent,
    standards_agent,
    personnel_agent
]

if __name__ == '__main__':
    # ── 3. Run Pipeline ───────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  STEP 3 — Running Extraction Pipeline")
    print("═" * 60)
    
    all_extractions: List[Dict] = []
    
    for agent in agents:
        # Assuming `faiss_index`, `chunks`, and `builder` are available from Cell 2
        # This might take a while depending on doc size and number of queries.
        agent_results = agent.extract(faiss_index, chunks, builder, top_k=6)
        all_extractions.extend(agent_results)
    
    # ── 4. Print Summary ──────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  EXTRACTION SUMMARY")
    print("═" * 60)
    
    # Group results by agent
    summary_counts: Dict[str, Dict[str, int]] = {
        agent.agent_name: {"found": 0, "not_found": 0, "error": 0} 
        for agent in agents
    }
    
    for result in all_extractions:
        agent_name = result["agent"]
        val = result["value"]
        
        if val == "NOT_FOUND":
            summary_counts[agent_name]["not_found"] += 1
        elif val == "JSON_PARSE_ERROR":
            summary_counts[agent_name]["error"] += 1
        else:
            summary_counts[agent_name]["found"] += 1
    
    # Print the breakdown
    for agent_name, counts in summary_counts.items():
        print(f"\n🤖 {agent_name}:")
        print(f"   ✅ Found    : {counts['found']}")
        print(f"   ❌ Not Found: {counts['not_found']}")
        if counts['error'] > 0:
            print(f"   ⚠️ Errors   : {counts['error']}")
    
    # Show flags for any missing information
    print("\n" + "─" * 60)
    print("⚠️ MISSING INFORMATION (NOT_FOUND):")
    for result in all_extractions:
        if result["value"] == "NOT_FOUND":
            print(f" - [{result['agent']}] {result['field']}")
    
    print("\n✅ Cell 4 complete. Extractions stored in `all_extractions`.")
    