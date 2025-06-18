#!/bin/bash

echo "🤖 Starting AI Trading System (Simple Mode)..."
echo "=================================="

# Kill any existing processes
echo "🔄 Stopping existing services..."
pkill -f "uvicorn\|streamlit" 2>/dev/null || true
sleep 2

# Start backend
echo "🚀 Starting backend on port 8000..."
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend on port 8501..."
streamlit run streamlit_app.py --server.port 8501 &
FRONTEND_PID=$!

echo ""
echo "🎉 System started!"
echo "📱 URLs:"
echo "   • UI: http://localhost:8501"
echo "   • API: http://localhost:8000"
echo ""
echo "⏹️  Press Ctrl+C to stop"
echo ""

# Wait for user to stop
wait 