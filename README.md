---
title: SpecSense Backend
emoji: 🏗️
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# SpecSense Backend

This is the FastAPI backend for **SpecSense**, a multi-agent construction specification intelligence system. It handles document parsing, semantic chunking, vector indexing (FAISS), and executing the multi-agent LLM pipeline (using Mistral-7B).

**Note:** The user-facing frontend is built with Next.js and deployed separately on Vercel.

## Endpoints

- `POST /upload`: Upload a specification document (PDF/DOCX) to start the parsing and indexing process in the background. Returns a `job_id`.
- `POST /run/{job_id}`: Trigger the main extraction pipeline for the uploaded document, generating a Method Statement, Traceability Report, and Annotated PDF.
- `GET /progress/{job_id}`: Server-Sent Events (SSE) stream providing real-time progress updates for the pipeline.
- `GET /download/{job_id}/{filename}`: Download generated artifacts (DOCX, PDF, XLSX).
- `POST /chat/{job_id}`: Interact with SpecBot to ask questions about the uploaded specification.

## Deployment on HuggingFace Spaces

This repository is pre-configured to run as a Docker Space on HuggingFace.

1. Ensure your Space is set up using the **Docker** SDK.
2. Port `7860` is exposed and used by Uvicorn.
3. If running on a GPU Space, update `requirements.txt` to use the standard CUDA version of `torch`.
