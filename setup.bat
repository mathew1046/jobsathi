@echo off
ECHO ====================================
ECHO JobSathi - Windows Setup Script
ECHO ====================================
ECHO.

REM Check Python installation
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Python is not installed or not in PATH
    ECHO Please install Python 3.8+ from https://www.python.org/downloads/
    PAUSE
    EXIT /B 1
)

REM Check Node.js installation
node --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Node.js is not installed or not in PATH
    ECHO Please install Node.js 16+ from https://nodejs.org/
    PAUSE
    EXIT /B 1
)

ECHO [1/6] Checking environment files...
IF NOT EXIST backend\.env (
    ECHO Creating backend/.env from .env.example...
    copy backend\.env.example backend\.env
    ECHO.
    ECHO *** IMPORTANT: Edit backend/.env and add your API keys ***
    ECHO - GEMINI_API_KEY is required for the app to work
    ECHO - Job search API keys are optional
    ECHO.
) ELSE (
    ECHO Backend .env file already exists.
)

IF NOT EXIST frontend\.env (
    ECHO Creating frontend/.env from .env.example...
    copy frontend\.env.example frontend\.env
    ECHO Frontend .env file created.
) ELSE (
    ECHO Frontend .env file already exists.
)

ECHO [2/6] Setting up Python virtual environment...
cd backend
IF NOT EXIST venv (
    python -m venv venv
    ECHO Virtual environment created.
) ELSE (
    ECHO Virtual environment already exists.
)

ECHO [3/6] Activating virtual environment and installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r app\requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Failed to install Python dependencies
    PAUSE
    EXIT /B 1
)
ECHO Python dependencies installed successfully.

ECHO [4/6] Creating database directory...
IF NOT EXIST app\database (
    mkdir app\database
    ECHO Database directory created.
) ELSE (
    ECHO Database directory already exists.
)

cd ..

ECHO [5/6] Installing Node.js dependencies for frontend...
cd frontend
call npm install
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Failed to install Node.js dependencies
    cd ..
    PAUSE
    EXIT /B 1
)
ECHO Node.js dependencies installed successfully.

cd ..

ECHO [6/6] Setup verification...
ECHO Checking for API keys in backend/.env...
findstr /C:"GEMINI_API_KEY=your_" backend\.env >nul
IF %ERRORLEVEL% EQU 0 (
    ECHO.
    ECHO *** WARNING: GEMINI_API_KEY not configured! ***
    ECHO Please edit backend/.env and add your API key
    ECHO Get your key from: https://makersuite.google.com/app/apikey
    ECHO.
)

ECHO.
ECHO ====================================
ECHO Setup Complete!
ECHO ====================================
ECHO.
ECHO Next steps:
ECHO 1. Edit backend/.env and add your GEMINI_API_KEY
ECHO 2. Run: start_all.bat
ECHO.
ECHO Backend will run on: http://localhost:8000
ECHO Frontend will run on: http://localhost:5173
ECHO API Docs available at: http://localhost:8000/docs
ECHO.

PAUSE
