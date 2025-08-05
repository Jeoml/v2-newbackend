"""
Pydantic models for AI-powered producer onboarding system
"""
from typing import Dict, List, Optional, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class OnboardingStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    COMPLETED = "completed"
    FAILED = "failed"

class DataValidationRequest(BaseModel):
    """Request model for validating producer data"""
    producer_data: Dict[str, Any] = Field(..., description="Producer data to validate")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")

class ValidationIssue(BaseModel):
    """Model for validation issues"""
    field: str
    issue_type: str  # missing, invalid, incomplete, suspicious
    description: str
    severity: float = Field(..., ge=0, le=1)  # 0-1 scale

class DataValidationResponse(BaseModel):
    """Response model for data validation"""
    completeness_percentage: float = Field(..., ge=0, le=100)
    is_complete: bool
    data_quality_issues: List[ValidationIssue]
    risk_score: float = Field(..., ge=0, le=100)
    explanation: str
    missing_fields: List[str]
    next_required_field: Optional[str] = None

class PromptGenerationRequest(BaseModel):
    """Request for generating conversational prompts"""
    partial_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    focus_field: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class PromptGenerationResponse(BaseModel):
    """Response with generated prompts"""
    prompt: str
    field_name: str
    expected_format: str
    validation_hint: str
    is_critical: bool = False
    follow_up_questions: Optional[List[str]] = None

class VerificationScheduleRequest(BaseModel):
    """Request for scheduling verification"""
    producer_id: str
    risk_score: float = Field(..., ge=0, le=100)
    producer_data: Dict[str, Any]
    validation_issues: Optional[List[ValidationIssue]] = None
    priority_override: Optional[str] = None

class VerificationScheduleResponse(BaseModel):
    """Response for verification scheduling"""
    verification_id: str
    producer_id: str
    scheduled_time: Optional[datetime] = None
    queue_position: int
    estimated_wait_hours: float
    status: str
    verification_type: str  # automated, manual, hybrid

class AnswerAssessmentRequest(BaseModel):
    """Request for assessing user answers"""
    question: str
    user_answer: str
    expected_field: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    validation_rules: Optional[Dict[str, Any]] = None

class AnswerAssessmentResponse(BaseModel):
    """Response for answer assessment"""
    valid: bool
    feedback: str
    confidence: float = Field(..., ge=0, le=1)
    extracted_value: Optional[Any] = None
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None

class OnboardingSession(BaseModel):
    """Model for tracking onboarding session"""
    session_id: str
    producer_id: str
    status: OnboardingStatus
    current_field: Optional[str] = None
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Optional[Dict[str, Any]] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None