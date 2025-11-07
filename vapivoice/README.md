# Attar Travel - AI Voice Assistant with Vapi

An intelligent voice-powered travel assistant that helps users search for flights and hotels through natural conversation. Built with Vapi.ai, React, and FastAPI.

## 🚀 Features

- **Voice-Powered Flight Search**: Search flights using natural language conversation
- **Hotel Search**: Find hotels in Saudi Arabia cities (Riyadh, Jeddah, Al-Ula, Abha, Dammam)
- **Visual Flight Cards**: Beautiful flight cards displayed directly in the chat widget
- **Smart Booking Flow**: Collects all details (date, passengers, class, seat) before showing options
- **Email Summaries**: Automatic email summaries sent after each call
- **Real-time Transcripts**: Live conversation transcripts displayed in the UI

## 📋 Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn
- Vapi.ai account and API keys
- ngrok (for local development)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/RahiniSathish/AttarVoice.git
cd AttarVoice/vapivoice
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from config/ENV_TEMPLATE.txt)
cp config/ENV_TEMPLATE.txt .env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## 🚀 Quick Start

### Option 1: Use Scripts (Recommended)

```bash
# Start everything (backend + frontend)
./scripts/start_vapi.sh

# Or start only frontend
./scripts/START_REACT_FRONTEND.sh

# Stop everything
./scripts/stop_vapi.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python backend/server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🌐 Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:4000
- **API Documentation**: http://localhost:4000/docs

## 🔧 Configuration

### 1. Environment Variables

Create a `.env` file in the root directory:

```env
# Vapi Configuration
VAPI_PUBLIC_KEY=your_vapi_public_key
VAPI_ASSISTANT_ID=your_assistant_id

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Optional: Bright Data API (for real-time flights)
BRIGHTDATA_API_KEY=your_brightdata_key
```

### 2. Vapi Dashboard Setup

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Create an assistant named "Alex"
3. Add functions:
   - `search_flights` - Server URL: `https://your-ngrok-url/webhooks/vapi`
   - `search_hotels` - Server URL: `https://your-ngrok-url/webhooks/vapi`
4. Copy the system prompt from `VAPI_SYSTEM_PROMPT.txt`
5. Configure voice and model settings

### 3. ngrok Setup (for Local Development)

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start ngrok tunnel
ngrok http 4000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Use this URL in Vapi Dashboard webhook configuration
```

## 📁 Project Structure

```
vapivoice/
├── backend/
│   ├── server.py              # Main FastAPI server
│   ├── bookings.py            # Booking service
│   ├── email_service.py       # Email sending service
│   ├── mock_flights.py        # Mock flight database
│   ├── mock_hotels.py         # Mock hotel database
│   └── hotels_api.py         # Hotel API fallback
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React app
│   │   ├── components/
│   │   │   ├── VoiceButton.jsx    # Vapi voice widget
│   │   │   ├── FlightCard.jsx     # Flight card component
│   │   │   └── HotelCard.jsx      # Hotel card component
│   │   └── utils/
│   │       └── logger.js     # Logging utility
│   └── package.json
├── docs/                      # Documentation
├── scripts/                   # Startup scripts
├── VAPI_SYSTEM_PROMPT.txt     # AI system prompt
└── requirements.txt           # Python dependencies
```

## 🎯 Usage

### Search Flights

1. Click the microphone button
2. Say: "Show me flights from Bangalore to Jeddah"
3. AI will ask for departure date
4. Flight cards will appear in the widget
5. Select a flight and provide booking details

### Search Hotels

1. Click the microphone button
2. Say: "Find hotels in Riyadh"
3. Hotel cards will appear with details
4. Click "View on Google Maps" for location

## 🔄 Workflow

### Flight Search Flow

1. User asks for flights → AI asks for departure date
2. User provides date → AI immediately shows flight cards
3. User selects flight → AI collects passengers, class, seat preference
4. Booking completed → Email sent with summary

### Hotel Search Flow

1. User asks for hotels → AI calls search_hotels function
2. Backend returns hotel data → Cards displayed in widget
3. User can view location on Google Maps

## 📧 Email Features

- Automatic call summaries sent after each call
- Booking confirmations with ticket details
- Transcript included in email
- Professional HTML email templates

## 🧪 Testing

```bash
# Backend tests
pytest backend/

# Frontend tests (if configured)
cd frontend
npm test
```

## 📝 API Endpoints

- `POST /webhooks/vapi` - Vapi webhook handler
- `GET /api/flight-cards/{call_id}` - Get cached flight cards
- `GET /api/hotel-cards/{call_id}` - Get cached hotel cards
- `POST /api/clear-cache` - Clear all cached cards
- `POST /api/send-call-summary` - Send call summary email
- `GET /api/call-summary-latest` - Get latest call summary

See `docs/API_REFERENCE.md` for complete API documentation.

## 🐛 Troubleshooting

See `docs/TROUBLESHOOTING.md` for common issues and solutions.

## 📚 Documentation

- [API Reference](docs/API_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Commit: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Create a Pull Request

## 📄 License

This project is proprietary and confidential.

## 👥 Contact

- GitHub: [@RahiniSathish](https://github.com/RahiniSathish)
- Repository: https://github.com/RahiniSathish/AttarVoice

## 🙏 Acknowledgments

- Built with [Vapi.ai](https://vapi.ai) for voice AI
- Frontend powered by React + Vite
- Backend powered by FastAPI

