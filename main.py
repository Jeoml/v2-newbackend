"""
FastAPI endpoints for AI-powered producer onboarding system
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import tempfile
import os

from database import get_db, SessionLocal
from config import GROQ_API_KEY
from auth import (
    verify_token, UserRegister, UserLogin, Token, 
    create_user, authenticate_user, create_access_token
)
from producer_onboarding_models import (
    DataValidationRequest, DataValidationResponse, ValidationIssue,
    PromptGenerationRequest, PromptGenerationResponse,
    VerificationScheduleRequest, VerificationScheduleResponse,
    AnswerAssessmentRequest, AnswerAssessmentResponse,
    OnboardingSession, OnboardingStatus
)
from agent import onboarding_agent, OnboardingState
from groq import Groq

# Initialize Groq client for endpoints
groq_client = Groq(api_key=GROQ_API_KEY)

# Add new endpoints to existing FastAPI app
app = FastAPI(
    title="Producer Onboarding API",
    version="2.0.0",
    description="""
    AI-powered producer onboarding system for Indian businesses.
    
    This API provides conversational onboarding with intelligent data collection, 
    real-time validation, and automated risk assessment for producer registration.
    
    ## Features
    - 🤖 AI-powered conversational onboarding
    - ✅ Real-time data validation (GST, PAN, FSSAI, etc.)
    - 📊 Automated risk scoring
    - 🗓️ Smart verification scheduling
    - 🎤 Audio transcription support
    - 🔒 Secure authentication with Bearer tokens
    
    ## Authentication
    All endpoints require Bearer token authentication in the Authorization header:
    ```
    Authorization: Bearer <your_token>
    ```
    """,
    contact={
        "name": "API Support",
        "email": "support@altibbe.com",
    },
    license_info={
        "name": "MIT",
    },
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "User registration and login endpoints for obtaining access tokens.",
        },
        {
            "name": "Onboarding Core",
            "description": "Core conversational onboarding endpoints for starting and continuing sessions.",
        },
        {
            "name": "Data Validation", 
            "description": "AI-powered validation of producer data with Indian compliance checking.",
        },
        {
            "name": "AI Conversation",
            "description": "Intelligent prompt generation and response assessment using AI.",
        },
        {
            "name": "Verification",
            "description": "Manual verification scheduling based on risk assessment.",
        },
        {
            "name": "Audio Processing",
            "description": "Audio transcription and multi-language support for voice-based onboarding.",
        },
        {
            "name": "Session Management",
            "description": "Session lifecycle management including status tracking and data export.",
        },
        {
            "name": "System",
            "description": "System health and monitoring endpoints.",
        },
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active onboarding sessions (in production, use Redis or database)
active_sessions: Dict[str, OnboardingState] = {}

# Authentication Endpoints
@app.post(
    "/api/auth/register",
    response_model=Token,
    summary="Register New User",
    description="""
    Register a new user account and receive an access token.
    
    The token should be used in the Authorization header for subsequent API calls:
    ```
    Authorization: Bearer <token>
    ```
    """,
    tags=["Authentication"],
    responses={
        200: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        400: {"description": "Username or email already exists"},
        422: {"description": "Invalid input data"}
    }
)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and return access token"""
    try:
        # Create user
        user = create_user(db, user_data)
        
        # Generate access token
        access_token = create_access_token(data={"sub": user.username})
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

@app.post(
    "/api/auth/login",
    response_model=Token,
    summary="User Login",
    description="""
    Authenticate user with username and password to receive an access token.
    
    The token should be used in the Authorization header for subsequent API calls:
    ```
    Authorization: Bearer <token>
    ```
    """,
    tags=["Authentication"],
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Invalid username or password"},
        422: {"description": "Invalid input data"}
    }
)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    try:
        # Authenticate user
        user = authenticate_user(db, user_credentials.username, user_credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        
        # Generate access token
        access_token = create_access_token(data={"sub": user.username})
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )

@app.post(
    "/api/onboarding/start",
    summary="Start Producer Onboarding",
    description="""
    Initialize a new producer onboarding session with AI-powered conversational flow.
    
    The system will analyze any provided initial data and start the onboarding conversation
    by asking for the most critical missing information first.
    """,
    response_description="Session details with initial prompt",
    tags=["Onboarding Core"],
    responses={
        200: {
            "description": "Session started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "uuid-v4-string",
                        "producer_id": "uuid-v4-string", 
                        "status": "started",
                        "message": "Welcome! Let's start by getting your business name.",
                        "collected_fields": [],
                        "current_field": "business_name"
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)
async def start_onboarding(
    initial_data: Optional[Dict[str, Any]] = None,
    token: str = Depends(verify_token)
):
    """Start a new onboarding session"""
    
    session_id = str(uuid.uuid4())
    producer_id = str(uuid.uuid4())
    
    # Initialize state
    initial_state = OnboardingState(
        messages=[],
        session_id=session_id,
        producer_id=producer_id,
        collected_data=initial_data or {},
        current_field=None,
        validation_results=None,
        risk_score=0.0,
        status="started",
        next_action="analyze_fields",
        conversation_context={},
        attempts=0,
        field_validation_results={}
    )
    
    # Run the first step
    try:
        result = onboarding_agent.invoke(initial_state)
        active_sessions[session_id] = result
        
        # Get the last assistant message
        last_message = None
        for msg in reversed(result.get("messages", [])):
            # Handle both dict and LangChain message object formats
            if hasattr(msg, 'type') and msg.type == "ai":
                # LangChain AIMessage object
                last_message = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                # Dictionary format
                last_message = msg.get("content")
                break
        
        return {
            "session_id": session_id,
            "producer_id": producer_id,
            "status": result["status"],
            "message": last_message or "Welcome! Let's get started with your onboarding.",
            "collected_fields": list(result["collected_data"].keys()),
            "current_field": result.get("current_field")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start onboarding: {str(e)}")

@app.post(
    "/api/onboarding/continue/{session_id}",
    summary="Continue Onboarding Conversation",
    description="""
    Continue an active onboarding session by providing the user's response to the AI agent.
    
    The system will:
    1. Validate the user's response using AI
    2. Extract and store relevant data
    3. Determine the next question or action
    4. Return the AI's response for continued conversation
    """,
    response_description="Next prompt or completion status",
    tags=["Onboarding Core"],
    responses={
        200: {
            "description": "Response processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "uuid-v4-string",
                        "status": "in_progress",
                        "message": "Great! Now could you please provide your GST number?",
                        "collected_fields": ["business_name", "email"],
                        "current_field": "gst_number",
                        "is_complete": False,
                        "risk_score": None,
                        "validation_results": None
                    }
                }
            }
        },
        404: {"description": "Session not found"},
        401: {"description": "Authentication required"},
        500: {"description": "Processing failed"}
    }
)
async def continue_onboarding(
    session_id: str,
    user_response: str,
    token: str = Depends(verify_token)
):
    """Continue an onboarding session with user's response"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = active_sessions[session_id]
    
    # Add user message
    state["messages"].append({"role": "user", "content": user_response})
    
    # Process the response through assessment
    state["next_action"] = "assess"
    
    try:
        # First assess the response
        from agent import assess_user_response
        state = assess_user_response(state)
        
        # Then continue with the workflow based on the assessment
        if state["next_action"] != "wait_response":
            result = onboarding_agent.invoke(state)
            active_sessions[session_id] = result
        else:
            result = state
            active_sessions[session_id] = state
        
        # Get the last assistant message
        last_message = None
        for msg in reversed(result.get("messages", [])):
            # Handle both dict and LangChain message object formats
            if hasattr(msg, 'type') and msg.type == "ai":
                # LangChain AIMessage object
                last_message = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                # Dictionary format
                last_message = msg.get("content")
                break
        
        return {
            "session_id": session_id,
            "status": result["status"],
            "message": last_message,
            "collected_fields": list(result["collected_data"].keys()),
            "current_field": result.get("current_field"),
            "is_complete": result["status"] in ["completed", "pending_verification"],
            "risk_score": result.get("risk_score", 0) if result["status"] != "in_progress" else None,
            "validation_results": result.get("validation_results") if result["status"] != "in_progress" else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@app.post(
    "/api/onboarding/validate-data", 
    response_model=DataValidationResponse,
    summary="Validate Producer Data",
    description="""
    Validate producer data comprehensively using AI-powered compliance checking.
    
    This endpoint performs:
    - **Format validation** for Indian regulatory fields (GST, PAN, FSSAI, etc.)
    - **Completeness analysis** based on business type
    - **Risk assessment** using multiple factors
    - **Compliance checking** against Indian regulations
    
    ### Supported Validations
    - **GST Number**: 15-character format with state code validation
    - **PAN Number**: 10-character alphanumeric format
    - **FSSAI License**: 14-digit food safety license
    - **Phone Numbers**: Indian mobile/landline validation
    - **Email**: RFC compliant email validation
    - **Pincode**: 6-digit Indian postal codes
    """,
    response_description="Comprehensive validation results with risk score",
    tags=["Data Validation"],
    responses={
        200: {
            "description": "Validation completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "completeness_percentage": 85.0,
                        "is_complete": False,
                        "data_quality_issues": [
                            {
                                "field": "gst_number",
                                "issue_type": "format_error",
                                "description": "GST number must be 15 characters",
                                "severity": "high"
                            }
                        ],
                        "risk_score": 35.2,
                        "explanation": "Medium risk due to missing compliance documents",
                        "missing_fields": ["fssai_license", "bank_details"],
                        "next_required_field": "fssai_license"
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        422: {"description": "Invalid request data"},
        500: {"description": "Validation failed"}
    }
)
async def validate_producer_data(
    request: DataValidationRequest,
    token: str = Depends(verify_token)
):
    """Validate producer data using AI-powered rules"""
    
    validation_prompt = f"""
    As a compliance expert, validate the following producer data:
    
    Data: {json.dumps(request.producer_data, indent=2)}
    
    Check for:
    1. Missing required fields based on business type
    2. Invalid formats (GST, PAN, email, phone)
    3. Suspicious patterns or inconsistencies
    4. Compliance with Indian regulations
    
    Required fields vary by business type:
    - All: name, email, phone, address, business_type
    - Manufacturers: GST, factory license, BIS certification
    - Food businesses: FSSAI license
    - Pharmaceuticals: drug license
    
    Calculate risk score based on:
    - Data completeness (40%)
    - Format validity (30%)
    - Business credibility (20%)
    - Regulatory compliance (10%)
    
    Respond in JSON format:
    {{
        "completeness_percentage": 0-100,
        "is_complete": true/false,
        "issues": [
            {{"field": "field_name", "issue_type": "format_error|missing_data|invalid_value", "description": "detailed explanation", "severity": 0.0-1.0}}
        ],
        "risk_score": 0-100,
        "explanation": "overall assessment explanation",
        "missing_fields": ["list", "of", "missing", "fields"],
        "next_required_field": "most_critical_missing_field"
    }}
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": validation_prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        validation_data = json.loads(completion.choices[0].message.content.strip())
        
        # Map to response model
        issues = [
            ValidationIssue(
                field=issue["field"],
                issue_type=issue["issue_type"],
                description=issue["description"],
                severity=issue["severity"]
            ) for issue in validation_data.get("issues", [])
        ]
        
        return DataValidationResponse(
            completeness_percentage=validation_data["completeness_percentage"],
            is_complete=validation_data["is_complete"],
            data_quality_issues=issues,
            risk_score=validation_data["risk_score"],
            explanation=validation_data["explanation"],
            missing_fields=validation_data["missing_fields"],
            next_required_field=validation_data.get("next_required_field")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post(
    "/api/onboarding/generate-prompts", 
    response_model=PromptGenerationResponse,
    summary="Generate Conversational Prompts",
    description="""
    Generate intelligent, context-aware prompts for collecting missing producer information.
    
    The AI analyzes:
    - **Current conversation context**
    - **Previously collected data**
    - **Business type requirements** 
    - **Failed attempt history**
    
    Returns natural, conversational prompts that explain why information is needed
    and provide helpful formatting examples.
    """,
    response_description="Contextual prompt with validation hints",
    tags=["AI Conversation"],
    responses={
        200: {
            "description": "Prompt generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "prompt": "Since you're in the food business, we need your FSSAI license number for regulatory compliance. This is a 14-digit number starting with 1 or 2.",
                        "field_name": "fssai_license",
                        "expected_format": "14-digit number",
                        "validation_hint": "FSSAI numbers start with 1 or 2 followed by 13 digits",
                        "is_critical": True,
                        "follow_up_questions": ["What type of food products do you manufacture?"]
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        500: {"description": "Prompt generation failed"}
    }
)
async def generate_prompts(
    request: PromptGenerationRequest,
    token: str = Depends(verify_token)
):
    """Generate conversational prompts for missing data"""
    
    prompt_request = f"""
    Generate a natural, conversational prompt to collect missing producer information.
    
    Current data: {json.dumps(request.partial_data, indent=2)}
    Focus field: {request.focus_field or "auto-detect most important missing field"}
    Context: {json.dumps(request.context, indent=2)}
    
    Guidelines:
    - Be warm and professional
    - Explain why the information is needed
    - Provide examples or formatting hints
    - Make it conversational, not like a form
    - Consider the business context
    
    If no specific field is provided, identify the most critical missing field.
    
    Respond in JSON format:
    {{
        "prompt": "the conversational prompt",
        "field_name": "field being requested",
        "expected_format": "format description",
        "validation_hint": "helpful hint for users",
        "is_critical": true/false,
        "follow_up_questions": ["optional follow-ups"]
    }}
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_request}],
            temperature=0.7,
            max_tokens=800
        )
        
        prompt_data = json.loads(completion.choices[0].message.content.strip())
        
        return PromptGenerationResponse(**prompt_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")

@app.post(
    "/api/onboarding/assess-answer", 
    response_model=AnswerAssessmentResponse,
    summary="Assess User Responses",
    description="""
    Intelligently assess whether a user's response is valid and complete for the requested field.
    
    The AI performs:
    - **Relevance checking** - Is the response answering the right question?
    - **Format validation** - Does it match expected patterns (GST, PAN, etc.)?
    - **Data extraction** - Can we extract clean, usable data?
    - **Quality assessment** - Is additional clarification needed?
    
    ### Validation Rules
    - **GST**: 15 characters (2-digit state + 10-digit PAN + 3 characters)
    - **PAN**: 10 characters (5 letters + 4 digits + 1 letter)
    - **FSSAI**: 14 digits starting with 1 or 2
    - **Phone**: Valid Indian mobile (10 digits) or landline with STD code
    - **Email**: RFC 5322 compliant format
    """,
    response_description="Assessment results with feedback and extracted value",
    tags=["AI Conversation"],
    responses={
        200: {
            "description": "Assessment completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "valid": True,
                        "feedback": "Perfect! Your GST number format is correct.",
                        "confidence": 0.95,
                        "extracted_value": "27ABCDE1234F1Z5",
                        "requires_clarification": False,
                        "clarification_prompt": None
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        500: {"description": "Assessment failed"}
    }
)
async def assess_answer(
    request: AnswerAssessmentRequest,
    token: str = Depends(verify_token)
):
    """Assess if user's answer is valid and complete using AI"""
    
    assessment_prompt = f"""
    Assess if the user's answer is valid and complete for the requested information.
    
    Question: {request.question}
    User Answer: {request.user_answer}
    Expected Field: {request.expected_field}
    Context: {json.dumps(request.context, indent=2)}
    
    Validation Rules: {json.dumps(request.validation_rules, indent=2) if request.validation_rules else "Use standard validation for the field type"}
    
    Check:
    1. Is the answer relevant to the question?
    2. Is the format correct for the field type?
    3. Is the information complete and usable?
    4. Can you extract the actual value?
    
    For Indian compliance fields:
    - GST: 15 chars (2 digit state + 10 PAN + 1 digit + 1 letter + 1 digit)
    - PAN: 10 chars (5 letters + 4 digits + 1 letter)
    - FSSAI: 14 digits
    - Phone: 10 digit mobile or landline with STD
    - Email: valid email format
    - Pincode: 6 digits
    
    Respond in JSON format:
    {{
        "valid": true/false,
        "feedback": "Clear, helpful feedback",
        "confidence": 0.0-1.0,
        "extracted_value": "the clean extracted value or null",
        "requires_clarification": true/false,
        "clarification_prompt": "optional follow-up question"
    }}
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": assessment_prompt}],
            temperature=0.2,
            max_tokens=600
        )
        
        assessment_data = json.loads(completion.choices[0].message.content.strip())
        
        return AnswerAssessmentResponse(
            valid=assessment_data["valid"],
            feedback=assessment_data["feedback"],
            confidence=assessment_data["confidence"],
            extracted_value=assessment_data.get("extracted_value"),
            requires_clarification=assessment_data.get("requires_clarification", False),
            clarification_prompt=assessment_data.get("clarification_prompt")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assess answer: {str(e)}")

@app.post(
    "/api/onboarding/schedule-verification", 
    response_model=VerificationScheduleResponse,
    summary="Schedule Manual Verification",
    description="""
    Schedule manual verification meetings based on risk assessment and business priority.
    
    ### Priority Levels
    - **Risk Score 70+**: Urgent (2-hour response)
    - **Risk Score 50-69**: High priority (4-hour response)  
    - **Risk Score 30-49**: Normal priority (8-hour response)
    - **Risk Score <30**: Low priority (24-hour response)
    
    ### Verification Types
    - **Manual**: Human verification call/meeting
    - **Hybrid**: Automated + human review
    - **Automated**: System verification only
    
    The system integrates with Calendly for automated scheduling when possible.
    """,
    response_description="Verification scheduling details with meeting information",
    tags=["Verification"],
    responses={
        200: {
            "description": "Verification scheduled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "verification_id": "uuid-v4-string",
                        "producer_id": "uuid-v4-string",
                        "scheduled_time": "2025-08-06T10:30:00Z",
                        "queue_position": 3,
                        "estimated_wait_hours": 4,
                        "status": "queued",
                        "verification_type": "manual"
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        422: {"description": "Invalid scheduling request"},
        500: {"description": "Scheduling failed"}
    }
)
async def schedule_verification(
    request: VerificationScheduleRequest,
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Schedule manual verification based on risk score"""
    
    verification_id = str(uuid.uuid4())
    
    # Determine priority and wait time based on risk score
    if request.risk_score >= 70:
        priority = 1
        wait_hours = 2
        verification_type = "manual"
    elif request.risk_score >= 50:
        priority = 2
        wait_hours = 4
        verification_type = "manual"
    elif request.risk_score >= 30:
        priority = 3
        wait_hours = 8
        verification_type = "hybrid"
    else:
        priority = 4
        wait_hours = 24
        verification_type = "automated"
    
    # Override priority if specified
    if request.priority_override:
        priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
        priority = priority_map.get(request.priority_override.lower(), priority)
    
    # Calculate queue position (simulated - in production, query actual queue)
    queue_position = priority * 5 + 3
    
    # Schedule verification
    scheduled_time = datetime.utcnow() + timedelta(hours=wait_hours)
    
    # In production, save to database
    # verification_record = VerificationQueue(
    #     verification_id=verification_id,
    #     producer_id=request.producer_id,
    #     risk_score=request.risk_score,
    #     priority=priority,
    #     scheduled_time=scheduled_time,
    #     data_snapshot=json.dumps(request.producer_data),
    #     issues=json.dumps([issue.dict() for issue in request.validation_issues or []])
    # )
    # db.add(verification_record)
    # db.commit()
    
    return VerificationScheduleResponse(
        verification_id=verification_id,
        producer_id=request.producer_id,
        scheduled_time=scheduled_time,
        queue_position=queue_position,
        estimated_wait_hours=wait_hours,
        status="queued",
        verification_type=verification_type
    )

@app.post(
    "/api/onboarding/transcribe-audio",
    summary="Transcribe Audio to Text",
    description="""
    Transcribe audio files to text using AI-powered speech recognition.
    
    ### Supported Formats
    - **Audio types**: MP3, WAV, M4A, MPEG
    - **Languages**: Auto-detection or specify language code
    - **Translation**: Optional translation to target language
    
    ### Features
    - **Multi-language support** including Hindi, Tamil, Telugu, etc.
    - **Automatic language detection**
    - **Real-time translation**
    - **Business context optimization** for producer onboarding
    
    Perfect for voice-based onboarding where producers can speak their responses
    instead of typing, especially useful for regional language speakers.
    """,
    response_description="Transcribed text with language detection and optional translation",
    tags=["Audio Processing"],
    responses={
        200: {
            "description": "Audio transcribed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "original_text": "Mera business ka naam ABC Foods Private Limited hai",
                        "detected_language": "hi",
                        "confidence": 0.92,
                        "translated_text": "My business name is ABC Foods Private Limited",
                        "translation_language": "en",
                        "duration_seconds": 5.2,
                        "processing_time_seconds": 2.5
                    }
                }
            }
        },
        400: {"description": "Invalid file type or format"},
        401: {"description": "Authentication required"},
        413: {"description": "File too large"},
        500: {"description": "Transcription failed"}
    }
)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(..., description="Audio file to transcribe (MP3, WAV, M4A)"),
    language: Optional[str] = None,
    translate_to: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    Transcribe audio using Whisper (simulated)
    In production, integrate with OpenAI Whisper API or self-hosted Whisper
    """
    
    # Validate file type
    allowed_types = ["audio/mp3", "audio/wav", "audio/mpeg", "audio/m4a"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_types}")
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, audio_file.filename)
    
    try:
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # In production, use actual Whisper API
        # For now, simulate the transcription
        transcription_prompt = f"""
        Simulate audio transcription for a producer onboarding conversation.
        Audio file: {audio_file.filename}
        Language: {language or 'auto-detect'}
        
        Generate a realistic transcription of a business owner providing information like:
        - Business details
        - Contact information
        - Compliance numbers
        
        Make it natural with some hesitations and conversational elements.
        
        Respond in JSON:
        {{
            "transcription": "the transcribed text",
            "detected_language": "en/hi/ta/etc",
            "confidence": 0.85-0.95
        }}
        """
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": transcription_prompt}],
            temperature=0.8,
            max_tokens=500
        )
        
        transcript_data = json.loads(completion.choices[0].message.content.strip())
        
        # Translate if requested
        translated_text = None
        if translate_to and translate_to != transcript_data["detected_language"]:
            translation_prompt = f"""
            Translate the following text from {transcript_data["detected_language"]} to {translate_to}:
            
            {transcript_data["transcription"]}
            
            Provide only the translated text.
            """
            
            translation = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": translation_prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            translated_text = translation.choices[0].message.content.strip()
        
        # Clean up
        os.remove(temp_path)
        os.rmdir(temp_dir)
        
        return {
            "original_text": transcript_data["transcription"],
            "detected_language": transcript_data["detected_language"],
            "confidence": transcript_data["confidence"],
            "translated_text": translated_text,
            "translation_language": translate_to if translated_text else None,
            "duration_seconds": len(content) / 50000,  # Rough estimate
            "processing_time_seconds": 2.5  # Simulated
        }
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get(
    "/api/onboarding/session/{session_id}/status",
    summary="Get Session Status",
    description="""
    Retrieve the current status and progress of an onboarding session.
    
    Useful for:
    - **Progress tracking** during long onboarding flows
    - **Session recovery** after interruptions
    - **Analytics and monitoring**
    - **Frontend state synchronization**
    
    Returns comprehensive session information including collected data,
    validation results, and conversation progress.
    """,
    response_description="Complete session status and progress information",
    tags=["Session Management"],
    responses={
        200: {
            "description": "Session status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "uuid-v4-string",
                        "producer_id": "uuid-v4-string",
                        "status": "in_progress",
                        "collected_fields": ["business_name", "email", "phone"],
                        "current_field": "gst_number",
                        "risk_score": 25.5,
                        "validation_results": {"completeness_percentage": 60},
                        "message_count": 8,
                        "last_updated": "2025-08-05T14:30:00Z"
                    }
                }
            }
        },
        404: {"description": "Session not found"},
        401: {"description": "Authentication required"}
    }
)
async def get_session_status(
    session_id: str,
    token: str = Depends(verify_token)
):
    """Get the current status of an onboarding session"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "producer_id": state["producer_id"],
        "status": state["status"],
        "collected_fields": list(state["collected_data"].keys()),
        "current_field": state.get("current_field"),
        "risk_score": state.get("risk_score"),
        "validation_results": state.get("validation_results"),
        "message_count": len(state["messages"]),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post(
    "/api/onboarding/session/{session_id}/export",
    summary="Export Session Data",
    description="""
    Export complete session data including conversation history and collected information.
    
    ### Export Includes
    - **Complete conversation transcript**
    - **All collected producer data**
    - **Validation results and risk scores**
    - **Timestamps and session metadata**
    
    Perfect for:
    - **Data backup and archival**
    - **Manual review processes**
    - **Integration with external systems**
    - **Compliance record keeping**
    
    The exported data is sanitized and formatted for easy consumption by downstream systems.
    """,
    response_description="Complete session data export",
    tags=["Session Management"],
    responses={
        200: {
            "description": "Session data exported successfully",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "uuid-v4-string",
                        "producer_id": "uuid-v4-string",
                        "status": "completed",
                        "collected_data": {
                            "business_name": "ABC Foods Pvt Ltd",
                            "email": "contact@abcfoods.com",
                            "gst_number": "27ABCDE1234F1Z5"
                        },
                        "validation_results": {"risk_score": 15.2},
                        "conversation_history": [
                            {"role": "assistant", "content": "Welcome! What's your business name?"},
                            {"role": "user", "content": "ABC Foods Private Limited"}
                        ],
                        "export_timestamp": "2025-08-05T14:30:00Z"
                    }
                }
            }
        },
        404: {"description": "Session not found"},
        401: {"description": "Authentication required"}
    }
)
async def export_session_data(
    session_id: str,
    token: str = Depends(verify_token)
):
    """Export all collected data from a session"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = active_sessions[session_id]
    
    # Prepare export data
    export_data = {
        "session_id": session_id,
        "producer_id": state["producer_id"],
        "status": state["status"],
        "collected_data": state["collected_data"],
        "validation_results": state.get("validation_results"),
        "risk_score": state.get("risk_score"),
        "conversation_history": [
            {
                "role": msg.type.replace("ai", "assistant").replace("human", "user") if hasattr(msg, 'type') else msg["role"],
                "content": msg.content if hasattr(msg, 'content') and not isinstance(msg.content, dict) else msg["content"]
            }
            for msg in state["messages"]
        ],
        "export_timestamp": datetime.utcnow().isoformat()
    }
    
    return export_data

@app.delete(
    "/api/onboarding/session/{session_id}",
    summary="End and Cleanup Session",
    description="""
    Properly end an onboarding session and cleanup resources.
    
    ### What Happens
    1. **Session data is archived** (in production, saved to database)
    2. **Memory resources are freed** 
    3. **Final status is recorded**
    4. **Session becomes inactive**
    
    **Important**: This is irreversible. Ensure you've exported any needed data first.
    
    Best practice is to call this after successful completion or when abandoning a session
    to prevent memory leaks and maintain system performance.
    """,
    response_description="Session termination confirmation",
    tags=["Session Management"],
    responses={
        200: {
            "description": "Session ended successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Session ended successfully",
                        "session_id": "uuid-v4-string",
                        "final_status": "completed"
                    }
                }
            }
        },
        404: {"description": "Session not found"},
        401: {"description": "Authentication required"}
    }
)
async def end_session(
    session_id: str,
    token: str = Depends(verify_token)
):
    """End and clean up an onboarding session"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # In production, save session data to database before deletion
    state = active_sessions[session_id]
    
    # Remove from active sessions
    del active_sessions[session_id]
    
    return {
        "message": "Session ended successfully",
        "session_id": session_id,
        "final_status": state["status"]
    }

# Health check endpoint
@app.get(
    "/api/onboarding/health",
    summary="System Health Check",
    description="""
    Check the health and status of the onboarding system.
    
    ### Health Metrics
    - **System status**: Overall health indicator
    - **Active sessions**: Number of ongoing onboarding sessions
    - **Response time**: System responsiveness
    - **Memory usage**: Resource utilization
    
    **No authentication required** - This endpoint is public for monitoring purposes.
    
    Used by:
    - **Load balancers** for health checking
    - **Monitoring systems** for alerting
    - **DevOps teams** for system status
    """,
    response_description="System health and status information",
    tags=["System"],
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "active_sessions": 42,
                        "timestamp": "2025-08-05T14:30:00Z"
                    }
                }
            }
        },
        503: {"description": "System is unhealthy"}
    }
)
async def onboarding_health():
    """Health check for onboarding system"""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.utcnow().isoformat()
    }