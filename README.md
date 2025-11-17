# JobSathi 🎙️

**Voice-Powered Resume Builder** - Create professional resumes through natural voice conversations in 17+ languages.

## ✨ Features

- 🎤 **Voice-First Interface** - Answer 15 questions with your microphone
- 🧠 **AI-Powered Extraction** - LLM intelligently extracts structured data
- 🌐 **Multilingual Support** - 17+ Indian languages + English (AI4Bharat ASR)
- 🎨 **Stunning UI** - Modern design with dark mode
- 📱 **Fully Responsive** - Works on mobile, tablet, and desktop
- 💾 **JSON Export** - Download your resume in structured format
- ⚡ **Fast & Easy** - Complete in under 10 minutes

## 🎯 How It Works

1. **Select Language** - Choose your preferred speaking language
2. **Answer Questions** - Record voice answers to 15 guided questions
3. **AI Processing** - Speech-to-text + LLM extracts your info
4. **Get Resume** - Download professional JSON profile

## 🌐 Supported Languages

Hindi • Bengali • Tamil • Telugu • Malayalam • Marathi • Gujarati • Punjabi • Odia • Assamese • English • *and more*

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- Microphone access

### Installation

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r app/requirements.txt

# Frontend  
cd ../frontend
npm install
```

### Running

```bash
# Terminal 1 - Backend
cd backend/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access at `http://localhost:5173`

## 📋 Resume Questions

The system guides you through 15 comprehensive questions:

1. Personal information (name, contact, location)
2. Professional details (role, experience, summary)
3. Technical skills
4. Education & certifications
5. Languages spoken
6. Notable projects
7. Professional links (LinkedIn, GitHub, portfolio)
8. Awards & achievements

## 🏗️ Tech Stack

**Backend:**
- FastAPI (Resume Builder API)
- AI4Bharat Indic Conformer (600M multilingual ASR)
- OpenRouter API (LLM for data extraction)
- httpx (async HTTP client)
- PyTorch + Transformers

**Frontend:**
- React + Vite
- MediaRecorder API (browser microphone)
- Modern UI with dark mode
- Responsive design

## 📁 Project Structure

```
jobsathi/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app (ASR + LLM endpoints)
│       └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── AudioRecorder.jsx    # Microphone recording
│   │   ├── constants/
│   │   │   └── questions.js         # 15 Q&A questions
│   │   ├── App.jsx                  # Main app
│   │   └── App.css
│   └── package.json
└── logs/
    ├── CHANGELOG.md             # Detailed changelog
    ├── QUICK_SETUP.md           # Quick start guide
    └── FILES_SUMMARY.md         # Development summary
```

## 🔑 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/languages` | GET | Get supported languages |
| `/transcribe` | POST | Convert audio to text |
| `/ask_llm` | POST | Extract structured data from transcript |
| `/build_profile` | POST | Merge Q&A into resume JSON |

## 📦 Output Format

```json
{
  "name": "Your Name",
  "role": "Software Engineer",
  "experience_years": "5 years",
  "skills": "Python, React, ...",
  "education": "B.Tech CS",
  "email": "email@example.com",
  "summary": "Professional summary...",
  ...
}
```

## 📚 Documentation

- **logs/CHANGELOG.md** - Comprehensive development history
- **logs/QUICK_SETUP.md** - Quick start guide and troubleshooting
- **logs/FILES_SUMMARY.md** - File-by-file documentation

## 🐛 Troubleshooting

### Microphone not working?
- Grant browser microphone permissions
- Use HTTPS or localhost

### Backend errors?
```bash
pip install -r backend/app/requirements.txt
python --version  # Should be 3.8+
```

## 📄 License

MIT

---

**Version:** 6.0.0 - Voice-Driven Resume Builder
**Powered by:** AI4Bharat ASR + OpenRouter AI

