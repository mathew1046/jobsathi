import os
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from transformers import AutoTokenizer
from parler_tts import ParlerTTSForConditionalGeneration
import soundfile as sf
import io
import numpy as np

app = FastAPI(title="JobSathi TTS Service")

# Configuration
MODEL_NAME = "ai4bharat/indic-parler-tts"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model {MODEL_NAME} on {DEVICE}...")

try:
    # Load Model and Tokenizer
    model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL_NAME).to(DEVICE)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    tokenizer = None

class TTSRequest(BaseModel):
    text: str
    description: str = "A female speaker delivering a slightly expressive and animated speech with a moderate speed and pitch." # Default prompt

@app.get("/")
def health_check():
    return {"status": "active", "model": MODEL_NAME, "device": DEVICE}

@app.post("/tts")
def generate_speech(request: TTSRequest):
    if not model or not tokenizer:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        input_ids = tokenizer(request.description, return_tensors="pt").input_ids.to(DEVICE)
        prompt_input_ids = tokenizer(request.text, return_tensors="pt").input_ids.to(DEVICE)

        generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
        audio_arr = generation.cpu().numpy().squeeze()
        
        # Convert to WAV
        buffer = io.BytesIO()
        sf.write(buffer, audio_arr, model.config.sampling_rate, format='WAV')
        buffer.seek(0)
        
        return Response(content=buffer.read(), media_type="audio/wav")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
