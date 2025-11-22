# JobSathi – AI-Powered Employment Assistant for India’s Non-Technical Workforce

JobSathi is a multilingual, voice-first résumé builder and job-search assistant built specifically for India’s non-technical job seekers. It removes language barriers, simplifies résumé creation, and aggregates real job opportunities across platforms — all in one smooth and accessible application.

## ✨ Why JobSathi?

Millions of Indian job seekers struggle with:
- Writing résumés  
- Speaking or typing in English  
- Navigating scattered job portals  

JobSathi solves this through a **speak → auto-transcribe → auto-translate → auto-extract → résumé → jobs** pipeline.

Users only need their voice. JobSathi handles everything else.

## 🔍 Core Features

### 1. Voice-Based Data Collection
- Supports 17+ Indian languages
- Accurate ASR using AI4Bharat Indic Conformer
- Real-time audio waveform + re-record option

### 2. Automatic English Translation
- Powered by Google Gemini
- Ensures consistent, ATS-friendly content

### 3. ATS-Friendly Résumé Generator
- Clean, structured, downloadable PDF
- Auto-fills Work Experience, Skills, Education, Summary, etc.

### 4. Smart Job Search
Aggregates jobs from:
- Adzuna
- Jooble
- Google Jobs (via SerpAPI)

### 5. Session Auto-Save
- User data stored as JSON  
- Resume anytime

### 6. Modern UI
- Dark theme  
- Mobile-friendly  
- Smooth user experience  

## 🧠 How JobSathi Works

User Speaks → ASR → Translation → LLM Extraction → ATS PDF → Job Search Results

## 🗣️ Supported Languages

Assamese, Awadhi, Bengali, Bhojpuri, Bodo, Dogri, English, Konkani, Gujarati, Hindi, Kannada, Kashmiri, Maithili, Malayalam, Marathi, Manipuri, Nepali, Odia, Punjabi, Sanskrit, Santali, Sindhi, Telugu, Tamil, Urdu.

## 🏗️ Architecture

jobsathi/
├── backend/        # FastAPI + ASR + LLM + Job Search
├── frontend/       # React + Vite + Web Audio
├── docker/         # Deployment
└── scripts/        # Setup utilities

## ⚙️ Tech Stack

### Backend
FastAPI, AI4Bharat ASR, PyTorch, Torchaudio, Google Gemini, ReportLab

### Frontend
React, Vite, Web Audio API

### DevOps
Docker, GitLab CI/CD with DevSecOps (SAST, Secret Detection, Dependency Scanning)

## 🚀 Setup

### Windows
setup.bat  
start_all.bat  

### Linux / Mac
./setup.sh  
./start_all.sh  

### Required Env Variable
GEMINI_API_KEY

## 📌 API Overview

- POST /transcribe  
- POST /ask_llm  
- POST /build_profile  
- POST /search_jobs  
- POST /start_session  

## 🛠️ Troubleshooting

- ASR model download slow → needs stable internet  
- Ports 8000/5173 busy → free ports  
- Job results limited → API rate limits  

## 📅 Roadmap

- Resume templates  
- Regional language resume export  
- Interview preparation module  
- Mobile app  
- SMS/WhatsApp alerts  
- Video resumes  

## 🙏 Acknowledgments

AI4Bharat, Google Gemini, Adzuna, Jooble, SerpAPI

## 🌍 Vision

JobSathi aims to empower India’s non-technical workforce by making résumé creation and job discovery accessible, multilingual, and effortless.
