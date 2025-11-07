#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🚀 STARTING VAPI VOICEBOT (Backend + Frontend) 🚀      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT SIGTERM

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}🐍 Activating Python virtual environment...${NC}"
source venv/bin/activate

# Install backend dependencies if needed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo -e "${YELLOW}📦 Installing backend dependencies...${NC}"
    pip install fastapi uvicorn python-dotenv python-multipart
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found. Creating template...${NC}"
    cat > .env << EOF
# SMTP Configuration (for email sending)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key_here
FROM_EMAIL=noreply@travel.ai

# Vapi Configuration
VAPI_PUBLIC_KEY=your_vapi_public_key_here
VAPI_ASSISTANT_ID=your_assistant_id_here

# Backend Configuration
BACKEND_PORT=4000
FRONTEND_PORT=5173
EOF
    echo -e "${YELLOW}📝 Please edit .env file with your actual credentials${NC}"
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Start Backend Server
echo ""
echo -e "${GREEN}🔧 Starting Backend Server (FastAPI)...${NC}"
echo -e "${BLUE}   Backend URL: http://localhost:4000${NC}"
echo -e "${BLUE}   API Docs: http://localhost:4000/docs${NC}"
echo ""

cd backend
uvicorn server:app --host 0.0.0.0 --port 4000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend started successfully (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Backend failed to start. Check logs/backend.log${NC}"
    exit 1
fi

# Start Frontend Server
echo ""
echo -e "${GREEN}🎨 Starting Frontend Server (React + Vite)...${NC}"
echo -e "${BLUE}   Frontend URL: http://localhost:5173${NC}"
echo ""

cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Frontend failed to start. Check logs/frontend.log${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ ALL SERVICES RUNNING ✅               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Services Status:${NC}"
echo -e "   ${GREEN}✓${NC} Backend API:  http://localhost:4000"
echo -e "   ${GREEN}✓${NC} Frontend App: http://localhost:5173"
echo -e "   ${GREEN}✓${NC} API Docs:     http://localhost:4000/docs"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Backend:  tail -f logs/backend.log"
echo -e "   Frontend: tail -f logs/frontend.log"
echo ""
echo -e "${YELLOW}🛑 Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

