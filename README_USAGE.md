# Producer Onboarding API - Usage Guide

## 🚀 Quick Start

### 1. Activate Virtual Environment
```bash
.venv\Scripts\activate
```

### 2. Start the Server
```bash
python run_server.py
```

### 3. Access the API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 How It Works

### Current Setup
You have a **FastAPI web API** that uses the **LangGraph agent** for AI-powered producer onboarding.

### Key Components
- **`main.py`** - FastAPI web server with REST endpoints
- **`agent.py`** - LangGraph workflow for conversational onboarding
- **`validation_tools.py`** - Indian compliance validation (GST, PAN, FSSAI, etc.)
- **`producer_onboarding_models.py`** - Data models and schemas

## 🔗 API Endpoints

### Start Onboarding
```bash
POST /api/onboarding/start
```
**Response**: Session ID and first question

### Continue Conversation
```bash
POST /api/onboarding/continue/{session_id}
Body: { "user_response": "My business name is ABC Foods" }
```
**Response**: Next question or completion status

### Validate Data
```bash
POST /api/onboarding/validate-data
```
**Response**: Validation results and risk score

## 🧪 Testing the API

### Using curl:
```bash
# Start onboarding
curl -X POST "http://localhost:8000/api/onboarding/start" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json"

# Continue with user response
curl -X POST "http://localhost:8000/api/onboarding/continue/session_id_here" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{"user_response": "ABC Foods Private Limited"}'
```

### Using the Swagger UI:
1. Go to http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in the parameters
4. Click "Execute"

## 🔧 Configuration

### Environment Variables (.env)
```
GROQ_API_KEY=your_groq_api_key_here
CALENDLY_API_TOKEN=your_calendly_token_here
CALENDLY_EVENT_TYPE_UUID=your_event_uuid_here
```

## ✨ Features

- **AI-powered conversation** using Groq LLM
- **Indian compliance validation** (GST, PAN, FSSAI, phone, email, pincode)
- **Risk assessment** and scoring
- **Automated verification scheduling** via Calendly
- **Conversational data collection** with error handling
- **Field-specific validation** with helpful examples

## 🛠️ Development

### Run Tests
```bash
python test_agent.py    # Test the agent components
python test_main.py     # Test FastAPI app import
```

### Project Structure
```
backend/
├── main.py                     # FastAPI server
├── agent.py                    # LangGraph agent
├── validation_tools.py         # Compliance validators
├── producer_onboarding_models.py  # Data models
├── config.py                   # Configuration
├── run_server.py              # Server startup script
├── .env                       # Environment variables
└── requirements files
```

The system is now ready to handle producer onboarding through a REST API! 🎉
