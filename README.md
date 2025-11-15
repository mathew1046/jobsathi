# JobSathi 🎙️

AI-powered audio transcription using **AI4Bharat** models - IndicWhisper for ASR and IndicTrans2 for translation.

## Features

- 🔍 **Auto Language Detection** - Automatically detects Indian languages
- 🎯 **AI4Bharat Models** - State-of-the-art for Indian languages
- 🌐 **IndicTrans2 Translation** - High-quality translation to English
- 📱 **Drag & Drop UI** - Modern, responsive interface
- 🚀 **CPU Optimized** - Runs on CPU without GPU

## Supported Languages

Hindi • Bengali • Telugu • Marathi • Tamil • Gujarati • Kannada • Malayalam • Punjabi • Odia • English

## Quick Start

```bash
# Clone repository
git clone https://gitlab.com/mathew1046/jobsathi.git
cd jobsathi

# Run setup (installs all dependencies)
./setup.sh

# Start application
./start_all.sh
```

Access at `http://localhost:3000`

## Tech Stack

**Backend:**
- FastAPI
- AI4Bharat IndicWhisper (vasista22/whisper-hindi-large-v2)
- AI4Bharat IndicTrans2 (indictrans2-indic-en-1B)
- PyTorch (CPU mode)

**Frontend:**
- React + Vite
- Modern UI with drag-and-drop

## Manual Setup

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r backend/app/requirements.txt

# Frontend
cd frontend && npm install

# Run
./start_all.sh
```

## How It Works

1. Upload audio file (any Indian language)
2. **IndicWhisper** transcribes with auto language detection
3. **IndicTrans2** translates to English
4. View both original and English text

## Note

⚠️ Models download on first use (~3GB). First transcription may take 2-3 minutes as models load into memory.

## License

MIT
