# 🚀 Quick Start Guide

## For Users Who Want to Run Immediately

### Option 1: Standard Setup (Recommended for Development)

**Windows:**
```cmd
1. setup.bat
2. Edit backend\.env and add your GEMINI_API_KEY
3. start_all.bat
```

**Linux/Mac:**
```bash
1. chmod +x *.sh
2. ./setup.sh
3. Edit backend/.env and add your GEMINI_API_KEY
4. ./start_all.sh
```

### Option 2: Docker (Recommended for Production)

```bash
1. cp backend/.env.example backend/.env
2. Edit backend/.env and add your GEMINI_API_KEY
3. docker-compose up --build
```

## Get Your API Key

🔑 **GEMINI_API_KEY (Required)**
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Paste it in `backend/.env`

⚠️ Job search API keys are optional but recommended for better job results.

## Access the App

After starting:
- 🌐 **Frontend**: http://localhost:5173
- 🔧 **Backend**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

## Need Help?

- 📖 See **README.md** for complete documentation
- 🐳 See **DOCKER.md** for Docker-specific help
- 📝 See **SETUP_SUMMARY.md** for technical details

---

**Total setup time: ~5-10 minutes** ⚡
