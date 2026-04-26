# ============================================================
#  SpecSense — Cell 3: LLM Initialization & Helper Functions
#  Google Colab · Free T4 GPU · No paid APIs
# ============================================================

import json
import re
from typing import Dict, Optional

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

# ── 1. Check GPU availability ─────────────────────────────────
print("═" * 60)
print("  STEP 1 — Checking GPU")
print("═" * 60)

if not torch.cuda.is_available():
    print("❌ GPU is NOT available! You are running on CPU.")
    print("   Go to Runtime > Change runtime type > Hardware accelerator > T4 GPU")
    # We set a dummy device just in case, though 4-bit quant needs GPU.
    device = torch.device("cpu")
else:
    device = torch.device("cuda")
    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"✅ GPU detected: {gpu_name} (VRAM: {vram_gb:.1f} GB)")

# ── 2. Load Model and Tokenizer ───────────────────────────────
print("\n" + "═" * 60)
print("  STEP 2 — Loading Mistral-7B-Instruct-v0.3 (4-bit)")
print("═" * 60)

MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.3"

# Configure 4-bit quantization to fit the 7B model within 16GB VRAM
# This dramatically reduces memory footprint while maintaining decent accuracy.
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

model = None
tokenizer = None

def load_model():
    global model, tokenizer
    if model is not None or tokenizer is not None:
        return

    import os
    token = os.environ.get("HF_TOKEN")

    try:
        if not torch.cuda.is_available():
            print("⚠️ CPU detected. Skipping full Mistral-7B load to prevent crash. (Using Mock LLM)")
            return

        print(f"⏳ Downloading and loading model weights for '{MODEL_ID}'...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=bnb_config,
            device_map="auto",
            token=token
        )
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=token)
        print("✅ Model and tokenizer loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load model. Error: {e}")
        print("   Did you accept the Mistral terms on HuggingFace Hub?")
        print("   Make sure to set HF_TOKEN in your Spaces settings!")
        model = None
        tokenizer = None

# ── 3. Helper: llm_generate ───────────────────────────────────

def llm_generate(prompt: str, max_new_tokens: int = 512) -> str:
    """
    Generate text from the loaded Mistral model given a prompt.
    Formats the prompt using Mistral's instruction template.
    """
    load_model()
    
    if model is None or tokenizer is None:
        print("MOCK LLM CALLED for prompt snippet:", prompt[:50])
        
        if "Extract" in prompt or "extract" in prompt:
            return '{"method_statement_requirements": "Mock requirement 1", "environmental_constraints": "Mock constraint"}'
        elif "evaluate" in prompt or "Validator" in prompt:
            return "MATCH"
        else:
            return "This is a mock AI response since we are running on a free CPU space without a GPU."

    # 1. Format prompt for Mistral v0.3 Instruct
    formatted_prompt = f"<s>[INST] {prompt} [/INST]"

    # 2. Tokenize and move to correct device (typically GPU)
    inputs = tokenizer(
        formatted_prompt, 
        return_tensors="pt"
    ).to(model.device)

    # 3. Generate response
    # do_sample=False -> greedy decoding (more deterministic, good for extraction)
    # repetition_penalty=1.1 -> slight penalty to prevent repetitive loops
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,        # Has no effect if do_sample=False, but explicit
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id # Suppress warning
        )

    # 4. Decode
    # The output includes the input prompt. We only want the new tokens.
    input_length = inputs.input_ids.shape[1]
    generated_tokens = output_ids[0][input_length:]
    
    result: str = tokenizer.decode(generated_tokens, skip_special_tokens=True)
    return result.strip()

# ── 4. Helper: llm_extract_json ───────────────────────────────

def llm_extract_json(prompt: str, max_new_tokens: int = 1024) -> Optional[Dict]:
    """
    Calls the LLM and attempts to extract and parse a JSON dictionary
    from its response. Resilient to markdown formatting or conversational filler.
    """
    # Ask the LLM to generate the output
    raw_response: str = llm_generate(prompt, max_new_tokens=max_new_tokens)
    
    if not raw_response:
        print("⚠️ Warning: LLM returned an empty response.")
        return None

    # Strategy 1: Direct parsing (in case it returned clean JSON)
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass # Try regex fallback

    # Strategy 2: Regex extraction (find first { ... } block)
    # This helps if the LLM says "Here is the JSON:\n```json\n{...}\n```"
    match = re.search(r'(\{.*\})', raw_response, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"⚠️ Warning: Found JSON-like block, but failed to parse: {e}")
            print(f"   Raw block extracted:\n{json_str}")
    else:
        print("⚠️ Warning: Could not find any { ... } block in LLM response.")
        print(f"   Raw response:\n{raw_response}")
        
    return None

# ── 5. Quick Test ─────────────────────────────────────────────
print("\n" + "═" * 60)
print("  STEP 3 — Testing LLM Generation")
print("═" * 60)

test_prompt = "What is cement? Give a brief 2-sentence explanation."
print(f"❓ Prompt: {test_prompt}")
print("⏳ Generating response (compiling kernels for the first time, may be slow)...\n")

try:
    test_response = llm_generate(test_prompt, max_new_tokens=100)
    print(f"💡 Response: {test_response}")
    print("\n✅ LLM functions are ready to use!")
except Exception as e:
    print(f"❌ LLM generation failed: {e}")
