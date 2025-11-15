#!/bin/bash

# JobSathi - AI4Bharat Setup Script

echo "=========================================="
echo "🚀 JobSathi - AI4Bharat Models Setup"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# Backend setup
echo "📦 Setting up backend..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

source venv/bin/activate
echo "✓ Virtual environment activated"

echo "📥 Installing AI4Bharat dependencies..."
echo "   (This may take 5-10 minutes on first run)"

pip install --upgrade pip setuptools wheel -q
pip install -r backend/app/requirements.txt

echo "✓ Backend dependencies installed"
echo ""

# Frontend setup
echo "⚛️ Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
    echo "✓ Frontend dependencies installed"
else
    echo "✓ Frontend dependencies already installed"
fi

cd ..

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📝 To run the application:"
echo "   ./start_all.sh"
echo ""
echo "📚 Models used:"
echo "   ASR: vasista22/whisper-hindi-large-v2"
echo "   Translation: ai4bharat/indictrans2-indic-en-1B"
echo ""
echo "⚠️  Note: Models will download on first use (~3GB)"
echo "=========================================="
