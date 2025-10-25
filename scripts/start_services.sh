#!/bin/bash

# Start All Services Script for Vapi-Haptik Voice Bot
# This script starts the backend server and related services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║   🎙️  MyTrip.ai Voice Bot - Starting Services   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f "config/.env" ]; then
    echo -e "${RED}❌ Error: config/.env file not found${NC}"
    echo -e "${YELLOW}Run: cp config/env.example config/.env${NC}"
    exit 1
fi

# Load environment variables
export $(cat config/.env | xargs)

# Check Python
echo -e "${BLUE}🐍 Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.deps_installed" ]; then
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    pip install -r requirements.txt
    touch venv/.deps_installed
fi

# Create logs directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping services...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    echo -e "${GREEN}✅ Services stopped${NC}"
}

trap cleanup EXIT INT TERM

# Start the backend server
echo -e "\n${BLUE}🚀 Starting Backend Server...${NC}"
python backend/server.py > logs/server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend Server started (PID: $SERVER_PID)${NC}"
    echo -e "${GREEN}   URL: http://localhost:${PORT:-8080}${NC}"
    echo -e "${GREEN}   Docs: http://localhost:${PORT:-8080}/docs${NC}"
else
    echo -e "${RED}❌ Failed to start Backend Server${NC}"
    exit 1
fi

# Display status
echo -e "\n${GREEN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║   ✅ All Services Running                         ║"
echo "╠═══════════════════════════════════════════════════╣"
echo "║   Backend API: http://localhost:${PORT:-8080}            ║"
echo "║   API Docs: http://localhost:${PORT:-8080}/docs          ║"
echo "║                                                   ║"
echo "║   Logs: logs/server.log                           ║"
echo "║                                                   ║"
echo "║   Press Ctrl+C to stop all services               ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Tail the logs
tail -f logs/server.log
