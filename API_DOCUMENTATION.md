# Producer Onboarding API Documentation

## Overview

The Producer Onboarding API is an AI-powered system for conversational business registration and validation, specifically designed for Indian businesses. It features intelligent data collection, real-time compliance validation, and automated risk assessment.

## 🔐 Authentication

All API endpoints require Bearer token authentication except the health check endpoint.

**Header Format:**
```
Authorization: Bearer <your_token>
```

**Error Response (401):**
```json
{
  "detail": "Invalid authentication credentials"
}
```

## 📍 Base URL

- **Development**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🚀 Core Onboarding APIs

### 1. Start Onboarding Session

**POST** `/api/onboarding/start`

Initialize a new conversational onboarding session with optional pre-filled data.

#### Request
```json
{
  "initial_data": {
    "business_name": "ABC Foods Pvt Ltd",
    "email": "contact@abcfoods.com"
  }
}
```

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "producer_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "started",
  "message": "Welcome! I see you've provided your business name. Now, could you please tell me your business type?",
  "collected_fields": ["business_name", "email"],
  "current_field": "business_type"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/onboarding/start" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_data": {
      "business_name": "ABC Foods Pvt Ltd",
      "email": "contact@abcfoods.com"
    }
  }'
```

---

### 2. Continue Onboarding Conversation

**POST** `/api/onboarding/continue/{session_id}`

Continue the conversation by providing user responses to AI prompts.

#### Parameters
- `session_id` (path): UUID of the active session

#### Request
```json
{
  "user_response": "We are a food manufacturing company specializing in snacks"
}
```

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "message": "Perfect! Since you're in food manufacturing, I'll need your FSSAI license number. This is mandatory for food businesses in India. It's a 14-digit number starting with 1 or 2.",
  "collected_fields": ["business_name", "email", "business_type"],
  "current_field": "fssai_license",
  "is_complete": false,
  "risk_score": null,
  "validation_results": null
}
```

#### Completion Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Excellent! Your onboarding is complete. You'll receive a confirmation email shortly.",
  "collected_fields": ["business_name", "email", "business_type", "fssai_license", "gst_number"],
  "current_field": null,
  "is_complete": true,
  "risk_score": 15.2,
  "validation_results": {
    "completeness_percentage": 100,
    "risk_score": 15.2
  }
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/onboarding/continue/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "user_response": "We are a food manufacturing company specializing in snacks"
  }'
```

---

## 🛡️ Data Validation APIs

### 3. Validate Producer Data

**POST** `/api/onboarding/validate-data`

Comprehensive validation of producer data with Indian compliance checking.

#### Request
```json
{
  "producer_data": {
    "business_name": "ABC Foods Pvt Ltd",
    "email": "contact@abcfoods.com",
    "gst_number": "27ABCDE1234F1Z5",
    "phone": "9876543210",
    "business_type": "food_manufacturing"
  },
  "business_type": "food_manufacturing",
  "validation_level": "comprehensive"
}
```

#### Response (200)
```json
{
  "completeness_percentage": 85.0,
  "is_complete": false,
  "data_quality_issues": [
    {
      "field": "fssai_license",
      "issue_type": "missing_data",
      "description": "FSSAI license is mandatory for food businesses",
      "severity": 0.9
    }
  ],
  "risk_score": 35.2,
  "explanation": "Medium risk due to missing FSSAI license for food business",
  "missing_fields": ["fssai_license", "address", "pincode"],
  "next_required_field": "fssai_license"
}
```

#### Indian Compliance Validations

| Field | Format | Example | Validation Rules |
|-------|--------|---------|------------------|
| GST Number | 15 characters | `27ABCDE1234F1Z5` | 2-digit state + 10-digit PAN + 3 characters |
| PAN Number | 10 characters | `ABCDE1234F` | 5 letters + 4 digits + 1 letter |
| FSSAI License | 14 digits | `12345678901234` | Must start with 1 or 2 |
| Phone | 10 digits | `9876543210` | Valid Indian mobile/landline |
| Pincode | 6 digits | `560001` | Valid Indian postal code |

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/onboarding/validate-data" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "producer_data": {
      "business_name": "ABC Foods Pvt Ltd",
      "gst_number": "27ABCDE1234F1Z5"
    },
    "validation_level": "comprehensive"
  }'
```

---

## 🤖 AI Conversation APIs

### 4. Generate Conversational Prompts

**POST** `/api/onboarding/generate-prompts`

Generate context-aware prompts for collecting missing information.

#### Request
```json
{
  "focus_field": "gst_number",
  "partial_data": {
    "business_name": "ABC Foods Pvt Ltd",
    "business_type": "food_manufacturing"
  },
  "context": {
    "previous_attempts": 1,
    "last_error": "invalid format"
  },
  "attempts": 1
}
```

#### Response (200)
```json
{
  "prompt": "I notice the GST number format wasn't quite right. GST numbers in India are 15 characters long. For example, if you're in Karnataka (state code 29), it would look like: 29ABCDE1234F1Z5. Could you please provide your complete 15-digit GST number?",
  "field_name": "gst_number",
  "expected_format": "15-character alphanumeric (2-digit state + 10-digit PAN + 3 characters)",
  "validation_hint": "GST format: XXAAAAANNNNXAX where XX=state code, AAAAA=letters, NNNN=numbers",
  "is_critical": true,
  "follow_up_questions": [
    "What state is your business registered in?",
    "Do you have your GST certificate handy?"
  ]
}
```

---

### 5. Assess User Responses

**POST** `/api/onboarding/assess-answer`

AI-powered assessment of user responses for validation and data extraction.

#### Request
```json
{
  "question": "Could you please provide your GST number?",
  "user_answer": "My GST number is 27ABCDE1234F1Z5",
  "expected_field": "gst_number",
  "context": {
    "business_state": "Maharashtra",
    "business_type": "manufacturing"
  },
  "validation_rules": {
    "format": "15_char_alphanumeric",
    "mandatory": true
  }
}
```

#### Response (200)
```json
{
  "valid": true,
  "feedback": "Perfect! Your GST number format is correct and matches Maharashtra state code.",
  "confidence": 0.95,
  "extracted_value": "27ABCDE1234F1Z5",
  "requires_clarification": false,
  "clarification_prompt": null
}
```

#### Invalid Response Example
```json
{
  "valid": false,
  "feedback": "The GST number should be 15 characters long. You provided only 12 characters.",
  "confidence": 0.88,
  "extracted_value": null,
  "requires_clarification": true,
  "clarification_prompt": "Could you please double-check your GST number? It should be exactly 15 characters including letters and numbers."
}
```

---

## 📅 Verification & Scheduling APIs

### 6. Schedule Manual Verification

**POST** `/api/onboarding/schedule-verification`

Schedule verification meetings based on risk assessment and business priority.

#### Request
```json
{
  "producer_id": "550e8400-e29b-41d4-a716-446655440001",
  "producer_data": {
    "business_name": "ABC Foods Pvt Ltd",
    "email": "contact@abcfoods.com",
    "phone": "9876543210"
  },
  "risk_score": 75.5,
  "priority_override": "urgent",
  "preferred_time": "2025-08-06T10:00:00Z",
  "contact_method": "both",
  "validation_issues": [
    {
      "field": "bank_details",
      "issue_type": "suspicious_pattern",
      "description": "Bank account details need manual verification",
      "severity": 0.8
    }
  ]
}
```

#### Response (200)
```json
{
  "verification_id": "660e8400-e29b-41d4-a716-446655440003",
  "producer_id": "550e8400-e29b-41d4-a716-446655440001",
  "scheduled_time": "2025-08-06T10:30:00Z",
  "queue_position": 2,
  "estimated_wait_hours": 2,
  "status": "queued",
  "verification_type": "manual"
}
```

#### Risk Score Priority Matrix

| Risk Score | Priority | Response Time | Verification Type |
|------------|----------|---------------|-------------------|
| 70-100 | Urgent | 2 hours | Manual |
| 50-69 | High | 4 hours | Manual |
| 30-49 | Normal | 8 hours | Hybrid |
| 0-29 | Low | 24 hours | Automated |

---

## 🎤 Audio Processing APIs

### 7. Transcribe Audio

**POST** `/api/onboarding/transcribe-audio`

Convert audio responses to text with multi-language support and translation.

#### Request (Multipart Form)
```
POST /api/onboarding/transcribe-audio
Content-Type: multipart/form-data

audio_file: [audio_file.mp3]
language: "hi" (optional)
translate_to: "en" (optional)
```

#### Response (200)
```json
{
  "original_text": "Mera business ka naam ABC Foods Private Limited hai aur yeh Maharashtra mein registered hai",
  "detected_language": "hi",
  "confidence": 0.92,
  "translated_text": "My business name is ABC Foods Private Limited and it is registered in Maharashtra",
  "translation_language": "en",
  "duration_seconds": 8.5,
  "processing_time_seconds": 3.2
}
```

#### Supported Audio Formats
- **MP3** (recommended)
- **WAV** (high quality)
- **M4A** (Apple format)
- **MPEG** (compressed)

#### Language Support
- **Hindi** (hi)
- **English** (en)
- **Tamil** (ta)
- **Telugu** (te)
- **Bengali** (bn)
- **Gujarati** (gu)
- **Marathi** (mr)
- **Auto-detect** (leave language blank)

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/onboarding/transcribe-audio" \
  -H "Authorization: Bearer your_token_here" \
  -F "audio_file=@business_intro.mp3" \
  -F "language=hi" \
  -F "translate_to=en"
```

---

## 📊 Session Management APIs

### 8. Get Session Status

**GET** `/api/onboarding/session/{session_id}/status`

Retrieve current status and progress of an onboarding session.

#### Parameters
- `session_id` (path): UUID of the session

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "producer_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "in_progress",
  "collected_fields": ["business_name", "email", "phone", "business_type"],
  "current_field": "gst_number",
  "risk_score": 25.5,
  "validation_results": {
    "completeness_percentage": 60
  },
  "message_count": 8,
  "last_updated": "2025-08-05T14:30:00Z"
}
```

#### Session Status Values
- `started` - Session initiated
- `in_progress` - Actively collecting data
- `pending_verification` - Awaiting manual verification
- `completed` - Successfully finished
- `failed` - Error occurred
- `rejected` - Verification failed

---

### 9. Export Session Data

**POST** `/api/onboarding/session/{session_id}/export`

Export complete session data for archival or integration purposes.

#### Response (200)
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "producer_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "collected_data": {
    "business_name": "ABC Foods Pvt Ltd",
    "email": "contact@abcfoods.com",
    "phone": "9876543210",
    "business_type": "food_manufacturing",
    "gst_number": "27ABCDE1234F1Z5",
    "fssai_license": "12345678901234"
  },
  "validation_results": {
    "risk_score": 15.2,
    "completeness_percentage": 100
  },
  "conversation_history": [
    {
      "role": "assistant",
      "content": "Welcome! Let's start with your business name."
    },
    {
      "role": "user", 
      "content": "ABC Foods Private Limited"
    },
    {
      "role": "assistant",
      "content": "Great! What type of business do you operate?"
    }
  ],
  "export_timestamp": "2025-08-05T14:30:00Z"
}
```

---

### 10. End Session

**DELETE** `/api/onboarding/session/{session_id}`

Properly terminate and cleanup an onboarding session.

#### Response (200)
```json
{
  "message": "Session ended successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "final_status": "completed"
}
```

**⚠️ Warning**: This operation is irreversible. Export session data first if needed.

---

## 🔍 System APIs

### 11. Health Check

**GET** `/api/onboarding/health`

Check system health and status. **No authentication required**.

#### Response (200)
```json
{
  "status": "healthy",
  "active_sessions": 42,
  "timestamp": "2025-08-05T14:30:00Z"
}
```

---

## 📋 Data Models

### Producer Data Fields

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `business_name` | string | ✅ | 2-100 chars | Legal business name |
| `email` | string | ✅ | RFC 5322 | Primary contact email |
| `phone` | string | ✅ | Indian format | Contact number |
| `business_type` | string | ✅ | Predefined list | Type of business |
| `gst_number` | string | ⚠️* | 15 chars | GST registration |
| `pan_number` | string | ⚠️* | 10 chars | PAN card number |
| `fssai_license` | string | ⚠️** | 14 digits | Food safety license |
| `address` | string | ✅ | - | Business address |
| `pincode` | string | ✅ | 6 digits | Postal code |
| `city` | string | ✅ | - | City name |
| `state` | string | ✅ | Indian states | State/UT |

*Required for businesses with turnover > ₹20 lakhs  
**Required for food businesses

### Business Types

- `manufacturing` - Manufacturing/Production
- `food_manufacturing` - Food Production
- `textiles` - Textile Manufacturing  
- `pharmaceuticals` - Pharmaceutical Manufacturing
- `electronics` - Electronics Manufacturing
- `chemicals` - Chemical Manufacturing
- `agriculture` - Agricultural Products
- `trading` - Trading/Retail
- `services` - Service Provider
- `other` - Other Business Type

---

## 🚨 Error Handling

### Standard Error Response
```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_FAILED",
  "field": "gst_number",
  "suggestion": "Please provide a valid 15-character GST number"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Missing or invalid authentication token |
| 404 | Not Found | Session or resource not found |
| 413 | Payload Too Large | File upload size exceeded |
| 422 | Unprocessable Entity | Validation errors in request data |
| 500 | Internal Server Error | Server processing error |
| 503 | Service Unavailable | System temporarily unavailable |

### Common Error Scenarios

#### Session Not Found (404)
```json
{
  "detail": "Session not found",
  "session_id": "invalid-uuid",
  "suggestion": "Please start a new onboarding session"
}
```

#### Invalid File Format (400)
```json
{
  "detail": "Invalid file type. Allowed: ['audio/mp3', 'audio/wav', 'audio/mpeg', 'audio/m4a']",
  "uploaded_type": "image/jpeg"
}
```

#### Validation Error (422)
```json
{
  "detail": "Validation failed: GST number format invalid",
  "field": "gst_number",
  "provided_value": "123456789",
  "expected_format": "15-character alphanumeric"
}
```

---

## 🔧 SDKs and Integration

### Python SDK Example

```python
import requests

class OnboardingAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def start_session(self, initial_data=None):
        response = requests.post(
            f"{self.base_url}/api/onboarding/start",
            headers=self.headers,
            json={"initial_data": initial_data}
        )
        return response.json()
    
    def continue_session(self, session_id, user_response):
        response = requests.post(
            f"{self.base_url}/api/onboarding/continue/{session_id}",
            headers=self.headers,
            json={"user_response": user_response}
        )
        return response.json()

# Usage
api = OnboardingAPI("http://localhost:8000", "your_token")
session = api.start_session({"business_name": "ABC Foods"})
result = api.continue_session(session["session_id"], "Food manufacturing")
```

### JavaScript/Node.js Example

```javascript
class OnboardingAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async startSession(initialData = null) {
    const response = await fetch(`${this.baseUrl}/api/onboarding/start`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ initial_data: initialData })
    });
    return await response.json();
  }

  async continueSession(sessionId, userResponse) {
    const response = await fetch(`${this.baseUrl}/api/onboarding/continue/${sessionId}`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ user_response: userResponse })
    });
    return await response.json();
  }
}

// Usage
const api = new OnboardingAPI('http://localhost:8000', 'your_token');
const session = await api.startSession({ business_name: 'ABC Foods' });
const result = await api.continueSession(session.session_id, 'Food manufacturing');
```

---

## 🎯 Usage Patterns

### 1. Simple Onboarding Flow

```python
# Start session
session = api.start_session()
session_id = session["session_id"]

# Conversation loop
while not session.get("is_complete"):
    print(session["message"])
    user_input = input("Your response: ")
    session = api.continue_session(session_id, user_input)

print("Onboarding completed!")
```

### 2. Batch Validation

```python
# Validate multiple producers
producers = [
    {"business_name": "ABC Foods", "gst_number": "27ABCDE1234F1Z5"},
    {"business_name": "XYZ Textiles", "gst_number": "29ABCDE1234F1Z5"}
]

for producer in producers:
    validation = api.validate_data(producer)
    if validation["risk_score"] > 50:
        # Schedule verification
        api.schedule_verification(producer, validation["risk_score"])
```

### 3. Audio-Based Onboarding

```python
# Upload and transcribe audio
audio_result = api.transcribe_audio("audio_file.mp3", translate_to="en")
text_response = audio_result["translated_text"]

# Continue with transcribed text
session = api.continue_session(session_id, text_response)
```

---

## 📚 Additional Resources

- **Swagger UI**: Interactive API documentation at `/docs`
- **ReDoc**: Alternative documentation at `/redoc`
- **Postman Collection**: [Download here](./postman_collection.json)
- **OpenAPI Spec**: Available at `/openapi.json`

## 🆘 Support

For API support and questions:
- **Email**: support@altibbe.com
- **Documentation**: This document
- **Status Page**: [status.altibbe.com](http://status.altibbe.com)

---

**Last Updated**: August 5, 2025  
**API Version**: 2.0.0  
**Maintainer**: Altibbe Backend Team
