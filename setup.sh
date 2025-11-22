#!/bin/bash

# JobSathi - Setup Script

echo "=========================================="
echo "🚀 JobSathi - Setup"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Check for environment files
echo "📋 [1/6] Checking environment files..."
if [ ! -f "backend/.env" ]; then
    echo "Creating backend/.env from .env.example..."
    cp backend/.env.example backend/.env
    echo ""
    echo "*** IMPORTANT: Edit backend/.env and add your API keys ***"
    echo "- GEMINI_API_KEY is required for the app to work"
    echo "- Job search API keys are optional"
    echo ""
else
    echo "✓ Backend .env file already exists"
fi

if [ ! -f "frontend/.env" ]; then
    echo "Creating frontend/.env from .env.example..."
    cp frontend/.env.example frontend/.env
    echo "✓ Frontend .env file created"
else
    echo "✓ Frontend .env file already exists"
fi
echo ""

# Backend setup
echo "📦 [2/6] Setting up backend..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
echo "✓ Virtual environment activated"

echo "📥 [3/6] Installing Python dependencies..."
echo "   (This may take 5-10 minutes on first run)"

pip install --upgrade pip setuptools wheel -q
pip install -r backend/app/requirements.txt

echo "✓ Backend dependencies installed"
echo ""

# Create database directory
echo "💾 [4/6] Creating database directory..."
mkdir -p backend/app/database
echo "✓ Database directory ready"
echo ""

# Frontend setup
echo "⚛️ [5/6] Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
    echo "✓ Frontend dependencies installed"
else
    echo "✓ Frontend dependencies already installed"
fi

cd ..

# Verify API keys
echo "🔑 [6/6] Verifying configuration..."
if grep -q "GEMINI_API_KEY=your_" backend/.env 2>/dev/null; then
    echo ""
    echo "*** WARNING: GEMINI_API_KEY not configured! ***"
    echo "Please edit backend/.env and add your API key"
    echo "Get your key from: https://makersuite.google.com/app/apikey"
    echo ""
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo "   1. Edit backend/.env and add your GEMINI_API_KEY"
echo "   2. Run: ./start_all.sh"
echo ""
echo "🌐 URLs:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🐳 Docker alternative:"
echo "   docker-compose up --build"
echo "   See DOCKER.md for details"
echo ""
echo "=========================================="
