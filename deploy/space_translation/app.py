import os
import torch
import traceback
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor

app = FastAPI(title="JobSathi Translation Service")

# Configuration
MODEL_NAME = "ai4bharat/indictrans2-en-indic-1B"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model {MODEL_NAME} on {DEVICE}...")

# Load Model and Tokenizer
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, trust_remote_code=True).to(DEVICE)
    ip = IndicProcessor(inference=True)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    traceback.print_exc()
    model = None
    tokenizer = None
    ip = None

class TranslationRequest(BaseModel):
    inputs: List[str]
    source_lang: str  # e.g., "eng_Latn"
    target_lang: str  # e.g., "hin_Deva"

@app.get("/")
def health_check():
    return {"status": "active", "model": MODEL_NAME, "device": DEVICE}

@app.post("/translate")
def translate(request: TranslationRequest):
    if not model or not tokenizer or not ip:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.inputs:
        return {"translations": []}

    try:
        print(f"Processing batch of size {len(request.inputs)} from {request.source_lang} to {request.target_lang}")
        
        # Preprocess using IndicProcessor
        batch = ip.preprocess_batch(
            request.inputs,
            src_lang=request.source_lang,
            tgt_lang=request.target_lang,
        )

        # Tokenize
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(DEVICE)

        # Generate
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=False, # Disable cache to prevent 'NoneType' object has no attribute 'shape' error
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1
            )

        # Decode
        decoded_tokens = tokenizer.batch_decode(
            generated_tokens, 
            skip_special_tokens=True
        )

        # Postprocess
        translations = ip.postprocess_batch(decoded_tokens, lang=request.target_lang)

        return {"translations": translations}

    except Exception as e:
        print(f"Translation Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
