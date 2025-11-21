@echo off
ECHO ====================================
ECHO Starting JobSathi Application
ECHO ====================================
ECHO.

REM Check if setup has been run
IF NOT EXIST backend\venv (
    ECHO ERROR: Virtual environment not found!
    ECHO Please run setup.bat first.
    PAUSE
    EXIT /B 1
)

IF NOT EXIST frontend\node_modules (
    ECHO ERROR: Node modules not found!
    ECHO Please run setup.bat first.
    PAUSE
    EXIT /B 1
)

ECHO Starting Backend Server...
START "JobSathi Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && cd app && uvicorn main:app --host 0.0.0.0 --port 8000"

ECHO Waiting for backend to start...
timeout /t 5 /nobreak >nul

ECHO Starting Frontend Server...
START "JobSathi Frontend" cmd /k "cd frontend && npm run dev"

ECHO.
ECHO ====================================
ECHO JobSathi is starting!
ECHO ====================================
ECHO.
ECHO Backend: http://localhost:8000
ECHO Frontend: http://localhost:5173
ECHO API Docs: http://localhost:8000/docs
ECHO.
ECHO Press any key to open the application in your browser...
PAUSE >nul

REM Open browser
start http://localhost:5173

ECHO.
ECHO To stop the servers, close the terminal windows.
ECHO.
