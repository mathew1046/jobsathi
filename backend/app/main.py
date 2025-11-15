# jobsathi_api.py
# ASR-only backend - Translation handled by frontend

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import asyncio
import torch
import torchaudio
from transformers import AutoModel

app = FastAPI(title="JobSathi API - ASR Only", version="5.0.0")

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

@app.get("/")
async def root():
    return {"message": "JobSathi API - ASR Only", "version": "5.0.0", "docs": "/docs"}

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
