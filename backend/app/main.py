# jobsathi_api.py
# ASR + LLM-powered resume builder backend

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import asyncio
import torch
import torchaudio
from transformers import AutoModel
import httpx
from typing import List, Dict, Any
import json

app = FastAPI(title="JobSathi API - Resume Builder", version="6.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Device and model IDs
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
ASR_MODEL_ID = "ai4bharat/indic-conformer-600m-multilingual"

# OpenRouter LLM configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "deepseek/deepseek-chat-v3.1:free"

# -----------------------
# Globals and locks
# -----------------------
_asr_model = None
asr_lock = asyncio.Lock()

# Language maps
LANGUAGE_NAME = {
    "as": "Assamese", "awa": "Awadhi", "bn": "Bengali", "bho": "Bhojpuri",
    "brx": "Bodo", "doi": "Dogri", "en": "English", "gom": "Goan Konkani",
    "gu": "Gujarati", "hi": "Hindi", "kn": "Kannada", "kas": "Kashmiri",
    "mai": "Maithili", "ml": "Malayalam", "mr": "Marathi", "mni": "Manipuri",
    "nep": "Nepali", "or": "Odia", "pa": "Punjabi", "sa": "Sanskrit",
    "sat": "Santali", "snd": "Sindhi", "te": "Telugu", "ta": "Tamil", "ur": "Urdu"
}

# -----------------------
# Utility functions
# -----------------------
def preprocess_audio(waveform, sample_rate, target_sr=16000):
    # convert to mono
    if waveform.ndim > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    # resample if required
    if sample_rate != target_sr:
        try:
            waveform = torchaudio.functional.resample(waveform, sample_rate, target_sr)
        except Exception as e:
            print(f"Resample failed: {e}, trying transforms.Resample")
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)
            waveform = resampler(waveform)
    waveform = waveform.to(torch.float32)
    if waveform.ndim == 1:
        waveform = waveform.unsqueeze(0)
    return waveform

# -----------------------
# ASR model lifecycle
# -----------------------
async def load_asr_model():
    global _asr_model
    async with asr_lock:
        if _asr_model is None:
            print("Loading ASR model...")
            _asr_model = AutoModel.from_pretrained(ASR_MODEL_ID, trust_remote_code=True).to(DEVICE)
            print("ASR model loaded")
    return _asr_model

def unload_asr_model():
    global _asr_model
    if _asr_model:
        print("Unloading ASR model to free memory")
        del _asr_model
        _asr_model = None
        torch.cuda.empty_cache()

async def run_asr(audio_tensor, source_lang):
    model = await load_asr_model()
    try:
        with torch.inference_mode():
            out = model(audio_tensor, source_lang, "rnnt")
            if isinstance(out, dict):
                return out.get("text", "").strip()
            return str(out).strip()
    except Exception as e:
        raise RuntimeError(f"ASR failed: {e}")

# -----------------------
# Audio loader helper
# -----------------------
def save_temp_file_and_load(audio_bytes, filename_hint):
    tmp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename_hint)[1] or ".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        try:
            waveform, sr = torchaudio.load(tmp_path)
            print(f"Loaded with torchaudio (auto): shape {waveform.shape}, sr {sr}")
        except Exception as e:
            print(f"torchaudio.load auto failed: {e}. Trying mp3 format fallback.")
            waveform, sr = torchaudio.load(tmp_path, format="mp3")
            print(f"Loaded as mp3: shape {waveform.shape}, sr {sr}")
        return tmp_path, waveform, sr
    except Exception as e:
        raise

# -----------------------
# Endpoints
# -----------------------

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), source_language: str = Form("hi")):
    """ASR-only endpoint - returns transcribed text for frontend translation."""
    print(f"Transcribe called with language: {source_language}, file: {audio.filename}")
    if source_language not in LANGUAGE_NAME:
        print(f"Unsupported language: {source_language}")
        raise HTTPException(status_code=400, detail="Unsupported language")

    audio_bytes = await audio.read()
    print(f"Audio bytes length: {len(audio_bytes)}")
    if not audio_bytes:
        raise HTTPException(400, "Empty audio")

    tmp_path = None
    try:
        tmp_path, waveform, sr = save_temp_file_and_load(audio_bytes, audio.filename)
        waveform = preprocess_audio(waveform, sr)
        print(f"Preprocessed waveform shape: {waveform.shape}")

        transcript = await run_asr(waveform.to(DEVICE), source_language)
        print(f"ASR transcript: {transcript}")

        if not transcript:
            unload_asr_model()
            raise HTTPException(400, "ASR returned empty")

        unload_asr_model()
        return {
            "status": "success",
            "data": {
                "original_text": transcript,
                "detected_language": source_language,
                "language_label": LANGUAGE_NAME[source_language]
            }
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
            print(f"Temp file removed: {tmp_path}")

# -----------------------
# LLM Integration
# -----------------------

async def call_openrouter(prompt: str, system_message: str = "You are a helpful assistant that extracts structured data from text.") -> Dict[str, Any]:
    """Call OpenRouter API with given prompt and return JSON response."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # Try to parse JSON from response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If response contains markdown code blocks, extract JSON
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_str)
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                    return json.loads(json_str)
                return {"raw_response": content}
    except Exception as e:
        print(f"OpenRouter API error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM API failed: {str(e)}")

@app.post("/ask_llm")
async def ask_llm(payload: Dict[str, Any] = Body(...)):
    """
    Accepts transcript and question, sends to LLM, returns structured JSON.
    Payload: { "transcript": "...", "question": "...", "field": "..." }
    """
    transcript = payload.get("transcript", "")
    question = payload.get("question", "")
    field = payload.get("field", "answer")
    
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is required")
    
    prompt = f"""Question: {question}
User's answer (in English): {transcript}

Extract the requested resume field from this text and return ONLY a small JSON object.
The JSON should have the key '{field}' with the extracted value.
If multiple values exist, use an array. Keep response concise.

Example format: {{"name": "Ramesh Kumar"}}

Return ONLY the JSON, no explanations."""
    
    result = await call_openrouter(prompt)
    return {
        "status": "success",
        "data": result
    }

@app.post("/build_profile")
async def build_profile(payload: Dict[str, Any] = Body(...)):
    """
    Accepts array of Q&A JSON responses, merges and normalizes into final profile.
    Payload: { "qa_responses": [{ "question_id": 1, "field": "name", "extracted_data": {...} }, ...] }
    """
    qa_responses = payload.get("qa_responses", [])
    if not qa_responses:
        raise HTTPException(status_code=400, detail="Q&A responses are required")
    
    # Merge all Q&A responses - extract data from nested structure
    merged_data = {}
    for item in qa_responses:
        # Each item has structure: { "question_id": 1, "field": "name", "extracted_data": {...} }
        if "extracted_data" in item and isinstance(item["extracted_data"], dict):
            merged_data.update(item["extracted_data"])
        elif "field" in item and any(k for k in item.keys() if k not in ["question_id", "field", "question", "transcript"]):
            # If data is at top level (legacy format)
            field_data = {k: v for k, v in item.items() if k not in ["question_id", "field", "question", "transcript"]}
            merged_data.update(field_data)
    
    prompt = f"""Here is raw resume data collected from a user interview:
{json.dumps(merged_data, indent=2)}

Please normalize and structure this into a clean professional resume JSON with these fields:
- name (string)
- role (string, job title/desired position)
- experience_years (number)
- experience_details (array of objects with: company, role, duration, description)
- skills (array of strings)
- languages (array of strings)
- location (string)
- education (array of objects with: degree, institution, year)
- certifications (array of strings)
- phone (string)
- email (string)
- summary (string, 2-3 sentences professional summary)
- extras (object for any additional relevant info)

Return ONLY a valid JSON object with all available fields. Use null for missing fields."""
    
    result = await call_openrouter(prompt, system_message="You are an expert resume builder that creates structured JSON profiles.")
    
    return {
        "status": "success",
        "profile": result
    }

@app.get("/")
async def root():
    return {"message": "JobSathi API - Resume Builder", "version": "6.0.0", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "JobSathi API"}

@app.get("/languages")
def list_languages():
    languages = [{"code": k, "label": v} for k, v in LANGUAGE_NAME.items()]
    return {"status": "success", "languages": languages}

@app.get("/model-status")
def model_status():
    asr_loaded = _asr_model is not None
    return {"asr_model_loaded": asr_loaded, "device": DEVICE}
