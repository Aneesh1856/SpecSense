# SpecSense — Multi-Agent Construction Specification Intelligence System

**SpecSense** is an end-to-end NLP pipeline designed to automatically parse complex construction specification documents, extract crucial engineering requirements using a robust **Multi-Agent LLM** approach, and format them into a standardized, compliant **Method Statement (DOCX)**.

## 🚀 Key Innovations
- **Multi-Agent Orchestration**: Specialized agents for Standards, Procedures, Equipment, Personnel, and Materials ensure high-granularity extraction.
- **Zero-Hallucination Grounding**: Every extracted fact is cross-referenced against the source text. If it's not in the spec, it doesn't make it into the report.
- **Visual Traceability**: Generates a `highlighted_spec.pdf` where extracted facts are visually overlaid on the original document, providing "proof of source" for engineers.
- **Interactive SpecBot**: A Gradio-powered chat interface allowing users to query their specifications in natural language.

## 🛠️ Tech Stack
- **LLM Engine**: HuggingFace Transformers (Llama/Mistral optimized for T4 GPUs)
- **Vector DB**: FAISS for high-speed semantic retrieval
- **Embeddings**: `all-MiniLM-L6-v2` for dense vector representation
- **Document Processing**: `pdfplumber`, `PyMuPDF`, and `python-docx`
- **UI**: Gradio for the interactive SpecBot

## 📖 How to Run (Google Colab)
This notebook is optimized for a **Free T4 GPU** environment.
1. Upload `SpecSense.ipynb` to [Google Colab](https://colab.research.google.com/).
2. Change runtime type to **T4 GPU**.
3. Run all cells. You will be prompted to upload a PDF or DOCX file.
4. The system will automatically download the generated **Method Statement** and **Highlighted PDF**.

## 📊 Accuracy & Anti-Hallucination
SpecSense integrates a dedicated **Grounding Validator** to eliminate AI hallucinations. 
Every fact extracted by the LLM contains a `verbatim_snippet`. The Validator cross-references this snippet against the original uploaded text using exact and fuzzy matching.

- **Grounding Score** = (Verified Facts / Total Extracted Facts) * 100
- **Hallucination Removal**: If a snippet doesn't exist in the source document, it is immediately discarded and omitted from the Method Statement.

## 👥 Team Information
- **Team Name**: [Your Team Name]
- **Team ID**: [Your Team ID]
- **Leader**: [Leader Name]
- **Members**: [Member 1], [Member 2], [Member 3]
