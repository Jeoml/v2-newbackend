# AI-Powered Producer Onboarding System

A FastAPI-based backend system for intelligent producer onboarding with conversational AI, compliance validation, and automated risk assessment.

## Features

- 🤖 **AI-Powered Conversations** - Natural language onboarding flow
- 🔐 **Secure Authentication** - JWT-based authentication system
- ✅ **Smart Validation** - AI-driven data validation and compliance checking
- 📊 **Risk Assessment** - Automated risk scoring and verification scheduling
- 🎙️ **Audio Support** - Voice transcription and multi-language support
- 📈 **Session Management** - Complete session lifecycle management

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database (optional for development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000/api

## Core API Endpoints

### Authentication

Before using any endpoints, you need to authenticate:

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Login to get access token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

Use the returned `access_token` in the Authorization header for all subsequent requests:
```bash
Authorization: Bearer <your_access_token>
```

### Onboarding Core

#### Start Producer Onboarding
**POST** `/api/onboarding/start`

Initialize a new producer onboarding session with AI-powered conversational flow.

```bash
curl -X POST "http://localhost:8000/api/onboarding/start" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "ABC Foods Pvt Ltd",
    "email": "contact@abcfoods.com"
  }'
```

**Response:**
```json
{
  "session_id": "uuid-v4-string",
  "producer_id": "uuid-v4-string",
  "status": "started",
  "message": "Welcome! Let's start by getting your business details.",
  "collected_fields": ["business_name", "email"],
  "current_field": "phone_number"
}
```

#### Continue Onboarding Conversation
**POST** `/api/onboarding/continue/{session_id}`

Continue an active onboarding session by providing the user's response to the AI agent.

```bash
curl -X POST "http://localhost:8000/api/onboarding/continue/{session_id}" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_response": "+91 9876543210"}'
```

**Response:**
```json
{
  "session_id": "uuid-v4-string",
  "status": "in_progress",
  "message": "Great! Now could you please provide your GST number?",
  "collected_fields": ["business_name", "email", "phone_number"],
  "current_field": "gst_number",
  "is_complete": false
}
```

### AI Conversation

#### Generate Conversational Prompts
**POST** `/api/onboarding/generate-prompts`

Generate intelligent, context-aware prompts for collecting missing producer information.

```bash
curl -X POST "http://localhost:8000/api/onboarding/generate-prompts" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "partial_data": {
      "business_name": "ABC Foods",
      "business_type": "food_processing"
    },
    "focus_field": "fssai_license",
    "context": {
      "conversation_stage": "compliance_documents",
      "previous_attempts": 0
    }
  }'
```

**Response:**
```json
{
  "prompt": "Since you're in the food business, we need your FSSAI license number for regulatory compliance. This is a 14-digit number starting with 1 or 2.",
  "field_name": "fssai_license",
  "expected_format": "14-digit number",
  "validation_hint": "FSSAI numbers start with 1 or 2 followed by 13 digits",
  "is_critical": true,
  "follow_up_questions": ["What type of food products do you manufacture?"]
}
```

#### Assess User Responses
**POST** `/api/onboarding/assess-answer`

Intelligently assess whether a user's response is valid and complete for the requested field.

```bash
curl -X POST "http://localhost:8000/api/onboarding/assess-answer" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Please provide your GST number",
    "user_answer": "27ABCDE1234F1Z5",
    "expected_field": "gst_number",
    "context": {
      "business_type": "manufacturing",
      "state": "Maharashtra"
    }
  }'
```

**Response:**
```json
{
  "valid": true,
  "feedback": "Perfect! Your GST number format is correct.",
  "confidence": 0.95,
  "extracted_value": "27ABCDE1234F1Z5",
  "requires_clarification": false,
  "clarification_prompt": null
}
```

## Development

### Running with Auto-reload
For development, use the `--reload` flag to automatically restart the server when code changes:

```bash
uvicorn main:app --reload
```

Additional options:
```bash
# Custom host and port
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# With debug logging
uvicorn main:app --reload --log-level debug

# Using the run_server.py script
python run_server.py
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key
CALENDLY_API_TOKEN=your_calendly_token
CALENDLY_EVENT_TYPE_UUID=your_event_uuid

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/database

# Security
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret

# Environment
DEBUG=True
ENVIRONMENT=development
```

### Testing

```bash
# Run tests
python -m pytest

# Run specific test file
python -m pytest test_main.py

# Test with coverage
python -m pytest --cov=.
```

## Deployment

### Railway

1. **Prepare for deployment** - Ensure all files are committed:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push
   ```

2. **Deploy to Railway** - The application will use the `Procfile` and `requirements.txt` for deployment

3. **Set environment variables** in Railway dashboard

### Docker

```bash
# Build image
docker build -t producer-onboarding .

# Run container
docker run -p 8000:8000 --env-file .env producer-onboarding
```

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## Architecture

The system uses:
- **FastAPI** for the web framework
- **SQLAlchemy** for database ORM
- **Groq/LangGraph** for AI conversations
- **JWT** for authentication
- **Pydantic** for data validation

## Support

For issues and questions, please check the API documentation at `/docs` or contact the development team.