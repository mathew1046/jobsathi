# JobSathi - AI-Powered Multilingual Resume Builder

JobSathi is an intelligent voice-driven resume builder that supports **17+ Indian languages** with ASR (Automatic Speech Recognition), English translation, and ATS-optimized PDF resume generation. It also includes job search integration across multiple platforms.

**PostgreSQL setup, API contract, migrations, imports and performance reproduction:**
`docs/POSTGRESQL.md`. Job search now reads a persistent catalog; configure `DATABASE_URL`
and import listings before searching. Interview sessions also survive backend restarts.
Implementation overview: `docs/IMPLEMENTATION.md` — architecture, data provenance,
index design, verification, and rollout.
Measured indexing results: `docs/PERFORMANCE.md` — 300,000 **synthetic benchmark listings**,
realistic frontend profile HTTP median **55.965 → 3.329 ms (16.81×)**; p95 **64.462 → 3.702 ms**
on the documented warm-cache, single-client native setup. These are local fixture
measurements, not production-traffic results.

## 🌟 Features

### Core Features
- **🎤 Voice Input Support** - Record answers in any of 17+ Indian languages
- **⌨️ Text Input Support** - Type answers directly in English or any language
- **🌐 Multilingual ASR** - AI4Bharat's Indic Conformer model for accurate transcription
- **🔄 Auto Translation** - Converts all answers to English using Google Gemini
- **📄 ATS Resume Generation** - Creates professional PDF resumes optimized for Applicant Tracking Systems
- **🔍 Smart Job Search** - Searches a PostgreSQL catalog refreshed from Adzuna, Jooble, Google Jobs or JSON imports
- **💾 Session-Based Storage** - Saves complete conversation history and resume data
- **🎨 Modern Dark UI** - Stunning responsive interface with dark mode

### Technical Features
- Real-time audio waveform visualization during recording
- Audio playback and re-record functionality
- PostgreSQL session/profile persistence with JSON exports and PDF storage
- Multi-source job aggregation with relevance scoring
- Duplicate job detection and removal
- LLM-powered data extraction (no fake data generation)
- Direct PDF download with one click

### 🛡️ Security & DevSecOps
JobSathi integrates **GitLab DevSecOps** for automated security and compliance:
- **Secret Detection** - Prevents API keys from being committed
- **SAST** - Static code analysis for security vulnerabilities
- **Dependency Scanning** - Monitors for vulnerable packages
- **Container Scanning** - Scans Docker images before deployment
- **License Compliance** - Tracks open-source licenses

📖 **See [GITLAB_SETUP.md](GITLAB_SETUP.md) for 5-minute setup guide**

## 🗣️ Supported Languages

Assamese, Awadhi, Bengali, Bhojpuri, Bodo, Dogri, English, Goan Konkani, Gujarati, Hindi, Kannada, Kashmiri, Maithili, Malayalam, Marathi, Manipuri, Nepali, Odia, Punjabi, Sanskrit, Santali, Sindhi, Telugu, Tamil, Urdu

## 🏗️ Architecture

```
jobsathi/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI server with ASR & LLM integration
│       ├── job_search.py        # Multi-source job aggregation
│       ├── requirements.txt     # Python dependencies
│       └── database/            # Session data & PDF storage
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React application
│   │   ├── components/         # AudioRecorder, etc.
│   │   └── constants/          # Resume questions
│   └── package.json            # Node.js dependencies
├── setup.bat                    # Windows setup script
├── setup.sh                     # Linux/Mac setup script
├── start_all.bat                # Windows start script
└── start_all.sh                 # Linux/Mac start script
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (3.12 recommended)
- **PostgreSQL 15+** (18 used for measured verification)
- **Node.js 16+** with npm
- **Git**
- **Windows**: PowerShell or Command Prompt
- **Linux/Mac**: Bash shell
- **OR Docker** (for containerized deployment)

### Installation (Standard)

Use the current native setup in `docs/POSTGRESQL.md`. The historical convenience-script
examples below are retained for older installations; those scripts are not shipped in
this checkout. Run `python -m app.migrate` from `backend` before starting `app.main:app`.

#### Windows
```cmd
# Clone the repository
git clone https://github.com/yourusername/jobsathi.git
cd jobsathi

# Run setup (installs all dependencies and creates .env files)
setup.bat

# Edit backend/.env and add your GEMINI_API_KEY
notepad backend\.env

# Start both backend and frontend
start_all.bat
```

#### Linux/Mac
```bash
# Clone the repository
git clone https://github.com/yourusername/jobsathi.git
cd jobsathi

# Make scripts executable
chmod +x setup.sh start_all.sh

# Run setup (installs all dependencies and creates .env files)
./setup.sh

# Edit backend/.env and add your GEMINI_API_KEY
nano backend/.env

# Start both backend and frontend
./start_all.sh
```

### Installation (Docker)

```bash
# Clone the repository
git clone https://github.com/yourusername/jobsathi.git
cd jobsathi

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env and add your GEMINI_API_KEY
nano backend/.env  # Linux/Mac
notepad backend\.env  # Windows

# Build and start with Docker Compose
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

📖 **See [DOCKER.md](DOCKER.md) for complete Docker documentation**

### Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📚 API Endpoints

### Session Management
- `POST /start_session` - Create new user session
- Returns: `{ session_id: "uuid" }`

### ASR & Data Extraction
- `POST /transcribe` - Transcribe audio to text
- `POST /ask_llm` - Extract structured data from transcript
- Both endpoints auto-translate to English

### Resume Generation
- `POST /build_profile` - Generate ATS resume from session data
- Returns: `{ profile: {...}, pdf_filename: "..." }`
- `GET /download_resume/{filename}` - Download PDF resume

### Job Search
- `POST /search_jobs` - Find relevant jobs based on profile
- Returns: `{ status: "success", jobs: [...], count: N, next_cursor: null | "..." }`
- Optional `limit`, `cursor` and `country_code` fields; existing `{profile}` requests work

### Utility
- `GET /languages` - List all supported languages
- `GET /health` - Health check

## 🔧 Configuration

### Environment Variables

#### Backend (`backend/.env`)

**Required:**
```env
DATABASE_URL=postgresql://jobsathi:jobsathi@127.0.0.1:5432/jobsathi
```

**Required for LLM interview/resume generation:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional (scheduled job imports):**
```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
JOOBLE_KEY=your_key
SERPAPI_KEY=your_key
```

**Server Configuration:**
```env
HOST=0.0.0.0
PORT=8000
ASR_MODEL_ID=ai4bharat/indic-conformer-600m-multilingual
DEVICE=auto
```

#### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Getting API Keys

| Service | Purpose | Sign Up URL | Free Tier |
|---------|---------|-------------|-----------|
| **Google Gemini** | LLM for data extraction | [makersuite.google.com](https://makersuite.google.com/app/apikey) | ✅ Yes |
| **Adzuna** | Job search | [developer.adzuna.com](https://developer.adzuna.com/) | ✅ Yes |
| **Jooble** | Job search | [jooble.org/api/about](https://jooble.org/api/about) | ✅ Yes |
| **SerpAPI** | Google Jobs | [serpapi.com](https://serpapi.com/) | ⚠️ Limited |

**Note:** Catalog search requires PostgreSQL and imported jobs, but no external API keys.
Provider keys are used by `python -m app.import_jobs`, outside the search request path.

## 📝 Resume Questions

The system asks 15 comprehensive questions:
1. Full Name
2. Role/Job Title
3. Years of Experience
4. Work Experience Details
5. Key Skills
6. Languages Spoken
7. Location
8. Education Background
9. Certifications
10. Phone Number
11. Email Address
12. Professional Summary
13. Work Type Preference
14. Machines/Vehicles Operated
15. Referrals

## 🎯 Usage Flow

1. **Start Session** - Click "Get Started"
2. **Select Language** - Choose your preferred language for voice input
3. **Answer Questions** - Record voice or type text answers
4. **Generate Resume** - System creates ATS-optimized PDF
5. **Search Jobs** - Click "Find Relevant Jobs" to see matching positions
6. **Download & Apply** - Download PDF resume and apply to jobs

## 🛠️ Development

### Backend Development
```bash
cd backend
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Run with auto-reload
python -m app.migrate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Docker Development
```bash
# Build and run with hot-reload
docker-compose up

# Rebuild specific service
docker-compose up --build backend

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

### Testing
```bash
# Backend
cd backend
export TEST_DATABASE_URL=postgresql://jobsathi:jobsathi@127.0.0.1:5432/jobsathi_test
pytest

# Frontend
cd frontend
npm test
```

## 📦 Dependencies

### Backend
- FastAPI - Web framework
- Uvicorn - ASGI server
- Transformers - Hugging Face models
- PyTorch & Torchaudio - ML framework
- Google Generative AI - Gemini LLM
- ReportLab - PDF generation
- Requests - HTTP client
- Feedparser - RSS parsing
- Psycopg 3 - PostgreSQL access and bounded connection pooling

### Frontend
- React - UI framework
- Vite - Build tool
- Web Audio API - Waveform visualization

## 🔒 Privacy & Data Storage

- Sessions, answers and final profile metadata are stored in PostgreSQL
- JSON exports and PDFs remain in `backend/app/database/` or `RESUME_STORAGE_DIR`
- Filenames include the session UUID to avoid collisions
- Database folder excluded from git
- **Environment files (`.env`) are excluded from git for security**
- API keys stored in `.env` files, never in code
- Use `.env.example` files as templates

## 📁 Project Structure

```
jobsathi/
├── README.md                    # Main documentation
├── DOCKER.md                    # Docker setup guide
├── setup.bat / setup.sh         # Setup scripts
├── start_all.bat / start_all.sh # Start scripts
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Backend Docker image
├── .dockerignore               # Docker build exclusions
├── .gitignore                  # Git exclusions
├── backend/
│   ├── .env                    # Backend environment variables (not in git)
│   ├── .env.example            # Backend env template
│   └── app/
│       ├── main.py             # FastAPI server
│       ├── job_search.py       # Job aggregation
│       ├── requirements.txt    # Python dependencies
│       └── database/           # User data & PDFs
└── frontend/
    ├── .env                    # Frontend environment variables (not in git)
    ├── .env.example            # Frontend env template
    ├── Dockerfile              # Frontend Docker image
    ├── src/
    │   ├── App.jsx            # Main React app
    │   ├── components/        # AudioRecorder, etc.
    │   └── constants/         # Questions config
    └── package.json           # Node.js dependencies
```

## 🐛 Troubleshooting

### "Module not found" errors
```bash
# Backend
cd backend && pip install -r app/requirements.txt

# Frontend
cd frontend && npm install
```

### Port already in use
```bash
# Find and kill process on port 8000
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### ASR model download issues
- First run downloads ~600MB model
- Requires stable internet connection
- Model cached in `~/.cache/huggingface/`

### Job search returns no results
- Check database readiness with `/health` and apply migrations
- Import jobs with `python -m app.import_jobs --file /path/to/jobs.json`
- Verify canonical city/country, active status and keyword matches; see `docs/POSTGRESQL.md`

## 📄 License

MIT License - See LICENSE file for details

## 👥 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 🙏 Acknowledgments

- **AI4Bharat** - Indic Conformer ASR model
- **Google Gemini** - LLM for data extraction
- **Adzuna, Jooble, SerpAPI** - Job search APIs

## 📧 Support

For issues and questions:
- GitHub Issues: [Create Issue](https://github.com/yourusername/jobsathi/issues)
- Email: support@jobsathi.com

## 🚀 Roadmap

- [ ] Add more languages
- [ ] Resume templates selection
- [ ] Video resume support
- [ ] LinkedIn integration
- [ ] Email job alerts
- [ ] Mobile app (React Native)
- [ ] Multi-language resume generation
- [ ] Interview preparation module

---

**Built with ❤️ for job seekers across India**
