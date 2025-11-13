from fastapi import FastAPI, File, UploadFile, HTTPException
from faster_whisper import WhisperModel
import os

app = FastAPI()

# Load model lazily to avoid excessive memory usage at startup
model = None

def get_model():
    global model
    if model is None:
        try:
            print("Loading Whisper model...")
            model = WhisperModel("small")
            print("Model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")
    return model

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio = await file.read()
        temp_path = "temp.wav"
        with open(temp_path, "wb") as f:
            f.write(audio)
        
        model = get_model()
        segments, info = model.transcribe(temp_path, language="hi")
        text = " ".join([segment.text for segment in segments])
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}
