# Vapi Voicebot - Quick Start

## 🚀 Run Everything with One Command

Simply run:
```bash
./start.sh
```

This will:
- ✅ Activate Python virtual environment
- ✅ Install dependencies (if needed)
- ✅ Start Backend API server (port 4000)
- ✅ Start Frontend React app (port 5173)
- ✅ Show status and logs

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm

## 🔧 Manual Setup (if needed)

### Backend Setup
```bash
cd backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install fastapi uvicorn python-dotenv python-multipart
uvicorn server:app --host 0.0.0.0 --port 4000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📝 Configuration

Create a `.env` file in the root directory with:
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
FROM_EMAIL=noreply@travel.ai
```

## 🛑 Stop Services

Press `Ctrl+C` in the terminal running `start.sh` to stop all services.

## 📊 Access Points

- Frontend: http://localhost:5173
- Backend API: http://localhost:4000
- API Docs: http://localhost:4000/docs

## 📝 Logs

- Backend logs: `logs/backend.log`
- Frontend logs: `logs/frontend.log`

View logs in real-time:
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

