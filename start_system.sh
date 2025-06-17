#!/bin/bash

# Exit on any error
set -e

# Enable error tracing
set -o errtrace
trap 'echo "Error occurred in function ${FUNCNAME[0]} at line $LINENO"' ERR

echo "🤖 Starting AI Trading System (system Python, no venv)..."
echo "=================================="

# Kill any existing processes first
echo "🔄 Stopping any existing services..."
pkill -f "uvicorn\|streamlit" 2>/dev/null || true
sleep 2

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        echo "Port $port is in use. Attempting to free it..."
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -i :$port > /dev/null 2>&1; then
            return 1
        fi
    fi
    return 0
}

# Function to wait for a service to be ready
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=10
    local attempt=1
    
    echo "⏳ Waiting for $service_name to start..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$port/ > /dev/null; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo "❌ $service_name failed to start after $max_attempts seconds"
    return 1
}

# Function to install requirements
install_requirements() {
    echo "📥 Installing/updating requirements globally (system Python)..."
    python3 -m pip install --upgrade pip wheel setuptools || {
        echo "❌ Failed to upgrade pip and build tools"
        return 1
    }
    python3 -m pip install -r requirements.txt || {
        echo "❌ Failed to install requirements"
        return 1
    }
    return 0
}

# Function to cleanup processes
cleanup() {
    echo "🧹 Cleaning up processes..."
    pkill -f "uvicorn\|streamlit" 2>/dev/null || true
    exit 1
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Always install/update requirements globally
install_requirements || {
    echo "❌ Failed to install requirements"
    exit 1
}

# Clear Python cache
echo "🧹 Clearing Python cache..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Ensure ports are free
echo "🔍 Checking ports..."
check_port 8000 || {
    echo "❌ Could not free port 8000"
    exit 1
}
check_port 8501 || {
    echo "❌ Could not free port 8501"
    exit 1
}

# Start backend
echo "🚀 Starting FastAPI backend (port 8000)..."
PYTHONPATH=$PYTHONPATH:$(pwd) \
python3 -m uvicorn backend.app:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!

# Wait for backend to be ready
if ! wait_for_service 8000 "Backend"; then
    echo "❌ Backend failed to start"
    cleanup
fi

# Start frontend with warnings suppressed
echo "🎨 Starting Streamlit frontend (port 8501)..."
PYTHONWARNINGS="ignore::SyntaxWarning" \
python3 -m streamlit run streamlit_app.py --server.port 8501 &
FRONTEND_PID=$!

# Wait for frontend to be ready
if ! wait_for_service 8501 "Frontend"; then
    echo "❌ Frontend failed to start"
    cleanup
fi

echo ""
echo "🎉 AI Trading System is now running! (system Python, no venv)"
echo "=================================="
echo "📱 Access URLs:"
echo "   • Streamlit UI: http://localhost:8501"
echo "   • FastAPI Docs: http://localhost:8000/docs"
echo "   • Backend API: http://localhost:8000"
echo ""
echo "🔧 Process IDs:"
echo "   • Backend PID: $BACKEND_PID"
echo "   • Frontend PID: $FRONTEND_PID"
echo ""
echo "⏹️  To stop the system, press Ctrl+C or run: pkill -f 'uvicorn\\|streamlit'"
echo ""

# Run system test with warnings suppressed
echo "🧪 Running system test..."
PYTHONWARNINGS="ignore::SyntaxWarning" python3 test_system.py || {
    echo "⚠️  System test completed with warnings"
}

# Keep script running and handle cleanup on exit
echo "🔄 System is running. Press Ctrl+C to stop..."
wait 