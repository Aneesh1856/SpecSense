# ============================================================
#  SpecSense — Cell 8: SpecBot Interactive Chat (INNOVATION)
#  Depends on: Cell 2 (builder, faiss_index, chunks)
#              Cell 3 (llm_generate)
# ============================================================

import gradio as gr
from typing import List, Dict, Any

# ── 1. SpecBot Launch Function ────────────────────────────────
print("═" * 60)
print("  STEP 1 — Defining SpecBot & UI")
print("═" * 60)

def run_specbot(faiss_index: Any, chunks: List[Dict], builder: Any) -> None:
    """
    Launches a Gradio chat interface allowing users to ask natural 
    language questions against the indexed specification document.
    """
    
    # ── Chat Logic (RAG) ──────────────────────────────────────
    def chat(message: str, history: List) -> str:
        """
        Handles an incoming user query, searches FAISS, and generates
        a strictly grounded response using Mistral-7B.
        """
        # 1. Search the FAISS index for top 5 relevant chunks
        search_results: List[Dict] = builder.search(
            query=message, 
            faiss_index=faiss_index, 
            chunks=chunks, 
            top_k=5
        )
        
        # 2. Build context string and extract page numbers
        context_parts = []
        page_set = set()
        
        for chunk in search_results:
            page = chunk.get("page", "?")
            page_set.add(str(page))
            context_parts.append(f"[Page {page}]: {chunk.get('text', '')}")
            
        context = "\n\n".join(context_parts)
        page_numbers = ", ".join(sorted(page_set))
        
        # 3. Build strict grounding prompt
        prompt = f"""You are SpecBot, an expert assistant for construction specification documents.
Answer the user's question using ONLY the passages provided below.
If the answer is not in the passages, say: "I could not find this in the specification."
Always end your answer with the source page reference.

SPECIFICATION PASSAGES:
{context}

USER QUESTION: {message}

Answer concisely in 2-4 sentences. End with: [Source: Page {page_numbers}]"""

        # 4. Call the LLM
        print(f"🤖 SpecBot is generating a response for: '{message}'")
        response = llm_generate(prompt, max_new_tokens=256)
        
        return response

    # ── Gradio UI Definition ──────────────────────────────────
    with gr.Blocks(title="SpecBot — Construction Spec Assistant") as demo:
        gr.Markdown("## SpecBot — Ask anything about the uploaded specification")
        gr.Markdown("*Answers are grounded in the document only. No hallucination.*")
        
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(
            placeholder="e.g. What is the maximum aggregate size for RCC?", 
            label="Your question"
        )
        clear = gr.Button("Clear")
        
        # Add example questions as quick-click buttons
        gr.Examples(
            examples=[
                "What cement type should be used?",
                "What is the curing period for concrete?",
                "What IS codes are referenced?",
                "What is the maximum water-cement ratio?",
                "Who is the Engineer-in-Charge?",
                "What equipment is needed for compaction?"
            ],
            inputs=msg
        )
        
        def respond(message: str, chat_history: List):
            """Wrapper to handle Gradio's chat history state."""
            bot_response = chat(message, chat_history)
            chat_history.append((message, bot_response))
            # Return empty string to clear the textbox, and updated history
            return "", chat_history
            
        # Wire up the UI events
        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        
        # Clear button resets the chatbot UI
        clear.click(lambda: None, None, chatbot, queue=False)
        
    # ── Launch ────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  STEP 2 — Launching Gradio Web Server")
    print("═" * 60)
    print("🌍 SpecBot is starting! Click the public link below to access the UI.\n")
    
    # share=True creates a public ngrok/gradio link. 
    # Essential for Hackathon video demos / sharing with judges!
    demo.launch(share=True)


# ── 3. Run the Bot ────────────────────────────────────────────
# Assuming `faiss_index`, `chunks`, and `builder` are loaded from Cell 2
if __name__ == '__main__':
    run_specbot(faiss_index, chunks, builder)
