# ============================================================
#  SpecSense — Cell 9: Master Pipeline Execution
#  Depends on: All previous cells
# ============================================================

import time
import os
from typing import Dict, List, Any

# ── 1. Master Pipeline Function ───────────────────────────────
if __name__ == '__main__':
    print("═" * 60)
    print("  STEP 1 — Defining Master Pipeline")
print("═" * 60)

def run_full_pipeline(
    file_path: str, 
    team_name: str, 
    team_id: str, 
    members: List[str], 
    leader: str
) -> Dict[str, Any]:
    """
    Executes the end-to-end SpecSense pipeline: parsing, chunking, 
    indexing, extraction, grounding validation, doc generation, 
    and PDF highlighting.
    
    Returns a dictionary of key metrics.
    """
    start_time = time.time()
    
    print("\n[1/7] Parsing Document...")
    parser = DocumentParser()
    pages = parser.parse(file_path)
    
    print("\n[2/7] Semantic Chunking & Indexing...")
    chunker = SemanticChunker()
    # Note: SemanticChunker.chunk() already applies detect_section_label internally
    chunks = chunker.chunk(pages)
    
    index_builder = FAISSIndexBuilder()
    faiss_index, chunks = index_builder.build(chunks)
    
    print("\n[3/7] Multi-Agent Extraction (Mistral-7B)...")
    # Agents are instantiated in Cell 4, but we can re-instantiate or use global ones
    # We will use the global `agents` list defined previously
    all_extractions = []
    for agent in agents:
        res = agent.extract(faiss_index, chunks, index_builder, top_k=6)
        all_extractions.extend(res)
        
    print("\n[4/7] Grounding Validation (Anti-Hallucination)...")
    validator = GroundingValidator()
    validated = validator.validate(all_extractions, pages)
    report = validator.compute_grounding_score(validated)
    verified = validator.get_verified_extractions(validated)
    
    print("\n[5/7] Method Statement DOCX Generation...")
    generator = MethodStatementGenerator(team_name, team_id, members, leader)
    generator.generate(verified, output_path="method_statement.docx")
    
    print("\n[6/7] PDF Traceability Highlighting...")
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        highlighter = PDFHighlighter()
        highlighter.highlight(file_path, verified, output_path="highlighted_spec.pdf")
    else:
        print("  Skipped: Highlighting only supported for PDF files.")
        
    print("\n[7/7] Pipeline Complete.")
    elapsed = time.time() - start_time
    
    # ── Final Summary Report ──────────────────────────────────
    filename = os.path.basename(file_path)
    total_pages = len(pages)
    total_chunks = len(chunks)
    facts_extracted = report["total_facts"]
    facts_verified = report["verified"] + report["fuzzy_match"]
    hallucinations = report["unverified"]
    grounding_score = report["grounding_score"]
    
    # Calculate unique sections filled out of 8 standard method statement sections
    # (Purpose, Scope, Acronyms, References, Procedure, Equipment, Personnel, Materials)
    # We automatically populate 3 (Purpose, Scope, Acronyms). Agents fill 5.
    agent_categories_found = len(set([ext["agent"] for ext in verified]))
    sections_filled = 3 + agent_categories_found
    
    summary = f"""
============================================
 SpecSense — Pipeline Complete
============================================
Document processed : {filename}
Total pages parsed : {total_pages}
Chunks indexed     : {total_chunks}
Facts extracted    : {facts_extracted}
Facts verified     : {facts_verified}
Hallucinations removed: {hallucinations}

GROUNDING SCORE    : {grounding_score:.1f}%
SECTION COVERAGE   : {sections_filled}/8 sections filled

OUTPUT FILES:
✓ method_statement.docx"""

    if ext == ".pdf":
        summary += "\n✓ highlighted_spec.pdf"
        
    summary += f"\n\nTime taken: {elapsed:.2f} seconds\n============================================"
    print(summary)
    
    return {
        "grounding_score": grounding_score,
        "facts_extracted": facts_extracted,
        "sections_filled": sections_filled
    }

# ── 2. Run Execution ──────────────────────────────────────────
print("\n" + "═" * 60)
print("  STEP 2 — Running Pipeline")
print("═" * 60)

# Allow users to upload file dynamically if not already set
if 'file_name' not in locals():
    print("📂 Please upload your construction specification (PDF or DOCX)…")
    try:
        from google.colab import files
        uploaded = files.upload()
        file_name = list(uploaded.keys())[0]
    except ImportError:
        import sys
        if len(sys.argv) > 1:
            file_name = sys.argv[1]
        else:
            file_name = "test_spec.pdf"

# Execute Pipeline
metrics = run_full_pipeline(
    file_path=file_name,
    team_name="SpecSense Innovators",
    team_id="TEAM-1337",
    members=["Alice Smith", "Bob Jones", "Charlie Brown"],
    leader="Alice Smith"
)

# Optional download triggers
print("\n📥 Triggering automatic downloads...")
try:
    from google.colab import files
    files.download("method_statement.docx")
    if os.path.exists("highlighted_spec.pdf"):
        files.download("highlighted_spec.pdf")
except ImportError:
    pass
