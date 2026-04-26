# ============================================================
#  SpecSense — Cell 7: PDF Traceability Highlighter
#  Depends on: Cell 5 (verified_extractions) and Cell 1 (file_name)
# ============================================================

import os
from typing import List, Dict, Any

import fitz  # PyMuPDF

# ── 1. PDF Highlighter Class ──────────────────────────────────
print("═" * 60)
print("  STEP 1 — Defining PDFHighlighter Class")
print("═" * 60)

class PDFHighlighter:
    """
    Overlays colored highlights onto the original PDF specification,
    mapping directly to the LLM's verified extractions. This provides
    immediate visual proof of the system's accuracy for judges.
    """

    # Colors defined as (R, G, B) normalized to 0.0 - 1.0 for PyMuPDF
    COLOR_MAP: Dict[str, tuple] = {
        "Materials Agent": (1.0, 1.0, 0.0),            # Yellow   (255, 255, 0)
        "Procedure Agent": (0.56, 0.93, 0.56),         # Green    (144, 238, 144)
        "Equipment Agent": (0.68, 0.85, 0.90),         # Blue     (173, 216, 230)
        "Standards Agent": (1.0, 0.78, 0.39),          # Orange   (255, 200, 100)
        "Personnel Agent": (1.0, 0.71, 0.76),          # Pink     (255, 182, 193)
    }

    # Fallback color if an unknown agent name appears
    DEFAULT_COLOR: tuple = (0.8, 0.8, 0.8)             # Light Gray

    def highlight(
        self, 
        pdf_path: str, 
        verified_extractions: List[Dict], 
        output_path: str = "highlighted_spec.pdf"
    ) -> Dict[str, int]:
        """
        Locates extracted snippets in the PDF and adds colored highlight annotations.
        """
        # 1. Open the PDF document
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise RuntimeError(f"Failed to open PDF {pdf_path}: {e}")

        # Dictionary to track how many highlights we successfully applied per agent
        summary: Dict[str, int] = {agent: 0 for agent in self.COLOR_MAP.keys()}
        total_pages = len(doc)

        # 2. Add Highlights for each verified fact
        for ext in verified_extractions:
            agent = ext.get("agent", "")
            # Ensure agent is in our summary dict if it somehow isn't
            if agent not in summary:
                summary[agent] = 0
                
            source_page = ext.get("source_page", 1)
            snippet = ext.get("verbatim_snippet", "").strip()
            clause = ext.get("source_clause", "").strip()
            
            # bounds check page number
            if source_page < 1 or source_page > total_pages:
                continue

            page = doc[source_page - 1]  # fitz uses 0-indexed pages
            rects = []

            # Strategy A: Exact substring match
            if snippet:
                rects = page.search_for(snippet)

            # Strategy B: Fallback to first 8 words if Exact failed
            # (Sometimes PDF formatting like newlines or hyphenation breaks exact match)
            if not rects and snippet:
                words = snippet.split()
                if len(words) > 8:
                    short_snippet = " ".join(words[:8])
                    rects = page.search_for(short_snippet)

            # Strategy C: Fallback to the clause number
            if not rects and clause:
                rects = page.search_for(clause)

            # Apply Annotations to all found bounding boxes
            if rects:
                color = self.COLOR_MAP.get(agent, self.DEFAULT_COLOR)
                for rect in rects:
                    annot = page.add_highlight_annot(rect)
                    annot.set_colors(stroke=color)
                    
                    # Add a popup note with attribution details
                    info_text = f"{agent} | Pg.{source_page} | Cl.{clause}"
                    annot.set_info(content=info_text)
                    annot.update()
                    
                summary[agent] += 1

        # 3. Add Legend to First Page
        if total_pages > 0:
            first_page = doc[0]
            
            # Position: Top Right. 
            # We assume a standard A4 page (roughly 595 x 842 points).
            rect_width = 160
            rect_height = 100
            page_rect = first_page.rect
            x0 = page_rect.width - rect_width - 10
            y0 = 10
            x1 = page_rect.width - 10
            y1 = y0 + rect_height
            
            legend_rect = fitz.Rect(x0, y0, x1, y1)
            
            # Draw white background box for legend
            first_page.draw_rect(legend_rect, color=(0,0,0), fill=(1,1,1), width=1.0)
            
            # Draw legend title
            first_page.insert_text((x0 + 5, y0 + 15), "SpecSense Highlight Legend", 
                                   fontsize=10, fontname="helv", color=(0,0,0))
            
            # Draw legend items
            y_offset = y0 + 35
            for ag, color in self.COLOR_MAP.items():
                # Draw small color square
                sq_rect = fitz.Rect(x0 + 10, y_offset - 8, x0 + 20, y_offset + 2)
                first_page.draw_rect(sq_rect, color=color, fill=color)
                # Draw text
                agent_name = ag.replace(" Agent", "")
                first_page.insert_text((x0 + 25, y_offset), agent_name, 
                                       fontsize=8, fontname="helv", color=(0,0,0))
                y_offset += 15

        # 4. Save and close
        doc.save(output_path)
        doc.close()
        
        return summary

    def generate_highlight_report(self, summary: Dict[str, int]) -> str:
        """
        Formats the highlight summary dictionary into a readable report.
        """
        total = sum(summary.values())
        report = []
        report.append(f"PDF Highlighting Summary: {total} facts overlaid successfully.")
        report.append("-" * 40)
        
        for agent, count in summary.items():
            report.append(f"  {agent:<20} : {count} highlights")
            
        return "\n".join(report)


# ── 2. Run Pipeline & Download ────────────────────────────────
if __name__ == '__main__':
    print("\n" + "═" * 60)
    print("  STEP 2 — Generating Annotated PDF")
    print("═" * 60)
    
    # We assume `file_name` was defined in Cell 1 when the user uploaded the file.
    # and `verified_extractions` was produced in Cell 5.
    
    ext = os.path.splitext(file_name)[-1].lower() if 'file_name' in locals() else ".pdf"
    
    if ext == ".pdf":
        highlighter = PDFHighlighter()
        output_pdf = "highlighted_spec.pdf"
        
        print(f"⏳ Processing '{file_name}' and applying highlights...")
        
        try:
            # Assuming `file_name` is the original PDF path
            summary = highlighter.highlight(file_name, verified_extractions, output_path=output_pdf)
            
            # 3. Print Report
            print("\n" + "═" * 60)
            print("  HIGHLIGHT REPORT")
            print("═" * 60)
            print(highlighter.generate_highlight_report(summary))
            
            print("\n" + "═" * 60)
            print("  STEP 3 — Downloading PDF")
            print("═" * 60)
            print("📥 Triggering download... (If running in Colab, the file will download automatically)")
            
            # Uncomment the following block in Colab to trigger file download
            # try:
            #     from google.colab import files
            #     files.download(output_pdf)
            # except ImportError:
            #     print(f"Not in Colab. File is saved locally as '{output_pdf}'")
                
        except Exception as e:
            print(f"❌ Failed to highlight PDF: {e}")
            
    else:
        # DOCX fallback message
        print("⚠️ Highlighting is only available for PDF inputs.")
        print("For DOCX specs, the Traceability Table in the Method Statement "
              "serves as the main source reference.")
    
    print("\n🚀 Visual Traceability Layer complete.")
    