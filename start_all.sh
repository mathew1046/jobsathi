#!/bin/bash

# Run both frontend and backend together

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "🚀 Starting JobSathi Full Stack"
echo "=========================================="
echo ""

# Start backend in background
echo "🔧 Starting backend API server..."
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"
echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  URL: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo ""

# Wait for backend to be ready
sleep 2

# Start frontend
echo "⚛️ Starting frontend dev server..."
cd "$SCRIPT_DIR/frontend"
npm install --silent > /dev/null 2>&1
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo "  URL: http://localhost:3000"
echo ""

echo "=========================================="
echo "✅ JobSathi is running!"
echo "=========================================="
echo ""
echo "📍 Backend API:  http://localhost:8000"
echo "📍 Frontend:     http://localhost:3000"
echo "📍 API Docs:     http://localhost:8000/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Handle cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    wait 2>/dev/null || true
    echo "✓ Servers stopped"
}

trap cleanup EXIT INT TERM

# Wait for both processes
wait
