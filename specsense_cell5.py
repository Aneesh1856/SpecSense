# ============================================================
#  SpecSense — Cell 5: Grounding & Hallucination Validator
#  Depends on: Cell 1 (pages), Cell 4 (all_extractions)
# ============================================================

import difflib
from typing import List, Dict, Any

# ── 1. Grounding Validator Class ──────────────────────────────
print("═" * 60)
print("  STEP 1 — Defining GroundingValidator Class")
print("═" * 60)

class GroundingValidator:
    """
    Validates LLM-extracted facts by cross-referencing their 
    reported 'verbatim_snippet' back to the source text.
    
    This acts as our core anti-hallucination mechanism.
    """

    def validate(self, extractions: List[Dict], pages: List[Dict]) -> List[Dict]:
        """
        Check if the verbatim snippet actually exists in the original document page.
        """
        validated_extractions: List[Dict] = []
        
        # Build a fast lookup dictionary for page texts
        page_lookup: Dict[int, str] = {p["page"]: p["text"] for p in pages}

        for ext in extractions:
            # Create a copy so we don't mutate the original dictionary
            result = dict(ext)
            
            # Skip validation for items where no information was found or parsing failed
            if result.get("value") in ("NOT_FOUND", "JSON_PARSE_ERROR"):
                result["grounded"] = False
                result["match_score"] = 0.0
                result["status"] = "SKIPPED"
                validated_extractions.append(result)
                continue

            snippet: str = result.get("verbatim_snippet", "").strip()
            source_page: int = result.get("source_page", -1)
            
            # If the LLM didn't provide a snippet or page, it's immediately unverified
            if not snippet or source_page not in page_lookup:
                result["grounded"] = False
                result["match_score"] = 0.0
                result["status"] = "UNVERIFIED"
                validated_extractions.append(result)
                continue

            page_text: str = page_lookup[source_page]
            
            # Try 1: Exact substring match (case-insensitive)
            if snippet.lower() in page_text.lower():
                result["grounded"] = True
                result["match_score"] = 1.0
                result["status"] = "VERIFIED"
                validated_extractions.append(result)
                continue

            # Try 2: Fuzzy match (handles minor whitespace or punctuation changes)
            # SequenceMatcher gets slow on huge texts, so we compare line-by-line 
            # or chunk-by-chunk for better performance, but for Colab scale against 
            # single pages, direct comparison is usually fine.
            # We use a sliding window over the page text to find the best match.
            best_ratio: float = 0.0
            snippet_len: int = len(snippet)
            
            # Quick heuristic: if the page is extremely long, difflib might be slow.
            # We just do a standard SequenceMatcher against the whole page text.
            # But since we want to find a matching *snippet*, we can split the page into sentences/lines.
            lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            
            for line in lines:
                ratio = difflib.SequenceMatcher(None, snippet.lower(), line.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio

            if best_ratio > 0.75:
                result["grounded"] = True
                result["match_score"] = best_ratio
                result["status"] = "FUZZY_MATCH"
            else:
                result["grounded"] = False
                result["match_score"] = best_ratio
                result["status"] = "UNVERIFIED"
                
            validated_extractions.append(result)

        return validated_extractions

    def compute_grounding_score(self, validated_extractions: List[Dict]) -> Dict[str, Any]:
        """
        Computes the overall accuracy / grounding score for the hackathon submission.
        """
        # Only consider facts that were actually extracted (ignore SKIPPED)
        facts = [ext for ext in validated_extractions if ext.get("status") != "SKIPPED"]
        
        total_facts = len(facts)
        verified = sum(1 for ext in facts if ext.get("status") == "VERIFIED")
        fuzzy = sum(1 for ext in facts if ext.get("status") == "FUZZY_MATCH")
        unverified = sum(1 for ext in facts if ext.get("status") == "UNVERIFIED")
        
        grounding_score = ((verified + fuzzy) / total_facts * 100) if total_facts > 0 else 0.0
        
        # Calculate by agent
        by_agent: Dict[str, Dict[str, Any]] = {}
        for ext in facts:
            agent = ext["agent"]
            if agent not in by_agent:
                by_agent[agent] = {"total": 0, "grounded": 0}
                
            by_agent[agent]["total"] += 1
            if ext.get("status") in ("VERIFIED", "FUZZY_MATCH"):
                by_agent[agent]["grounded"] += 1
                
        # Finalize by_agent scores
        for agent, stats in by_agent.items():
            t = stats["total"]
            stats["score"] = (stats["grounded"] / t * 100) if t > 0 else 0.0

        return {
            "total_facts": total_facts,
            "verified": verified,
            "fuzzy_match": fuzzy,
            "unverified": unverified,
            "grounding_score": grounding_score,
            "by_agent": by_agent
        }

    def get_verified_extractions(self, validated_extractions: List[Dict]) -> List[Dict]:
        """
        Returns only the extractions that passed grounding validation.
        """
        return [
            ext for ext in validated_extractions 
            if ext.get("status") in ("VERIFIED", "FUZZY_MATCH")
        ]

# ── 2. Run Pipeline ───────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "═" * 60)
    print("  STEP 2 — Running Grounding Validation")
    print("═" * 60)
    
    validator = GroundingValidator()
    
    # We assume `all_extractions` and `pages` are loaded from Cell 4 & Cell 1
    validated_extractions = validator.validate(all_extractions, pages)
    
    # ── 3. Print Report ───────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  GROUNDING & HALLUCINATION REPORT")
    print("═" * 60)
    
    report = validator.compute_grounding_score(validated_extractions)
    
    # Print cleanly formatted table
    print(f"{'Metric':<30} | {'Value'}")
    print("-" * 45)
    print(f"{'Total Extracted Facts':<30} | {report['total_facts']}")
    print(f"{'Exact Matches (VERIFIED)':<30} | {report['verified']}")
    print(f"{'Fuzzy Matches (FUZZY_MATCH)':<30} | {report['fuzzy_match']}")
    print(f"{'Hallucinations (UNVERIFIED)':<30} | {report['unverified']}")
    print("-" * 45)
    
    grounded_count = report['verified'] + report['fuzzy_match']
    print(f"\nGrounding Score: {report['grounding_score']:.1f}% ({grounded_count} verified / {report['total_facts']} total facts)")
    
    print("\n── Agent Breakdown ──")
    for agent, stats in report['by_agent'].items():
        print(f"  {agent:<20} : {stats['score']:>5.1f}%  ({stats['grounded']}/{stats['total']})")
    
    # ── 4. Store Verified Facts ───────────────────────────────────
    verified_extractions = validator.get_verified_extractions(validated_extractions)
    
    print("\n" + "═" * 60)
    print("  FINAL STATUS")
    print("═" * 60)
    
    print(f"✅ Facts approved for Method Statement: {len(verified_extractions)}")
    print(f"🛡️  Potential hallucinations removed: {report['unverified']}")
    
    print("\n✅ Cell 5 complete. `verified_extractions` is ready for the Document Generator.")
    