"""
Producer onboarding models and data structures
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime


class OnboardingStatus(str, Enum):
    """Status of producer onboarding"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """Model for validation issues"""
    field: str
    issue_type: str  # Updated to match API documentation
    description: str  # Updated to match API documentation
    severity: float  # Updated to match API documentation
    suggestion: Optional[str] = None
    

class AnswerAssessmentResponse(BaseModel):
    """Response model for answer assessment"""
    valid: bool
    confidence: float
    extracted_value: Optional[str]
    feedback: str
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None


class DataValidationResponse(BaseModel):
    """Response model for data validation"""
    completeness_percentage: float
    is_complete: bool
    data_quality_issues: List[ValidationIssue]  # Updated field name
    risk_score: float
    explanation: str  # New field for better API docs
    missing_fields: List[str]  # New field
    next_required_field: Optional[str] = None  # New field


class ProducerData(BaseModel):
    """Model for producer data"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    business_type: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    fssai_number: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    annual_turnover: Optional[str] = None
    employee_count: Optional[str] = None
    established_year: Optional[int] = None
    
    # Metadata
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    session_id: Optional[str] = None
    producer_id: Optional[str] = None


class OnboardingSession(BaseModel):
    """Model for onboarding session"""
    session_id: str
    producer_id: Optional[str] = None
    status: OnboardingStatus = OnboardingStatus.STARTED
    collected_data: ProducerData = ProducerData()
    validation_results: Optional[DataValidationResponse] = None
    risk_score: float = 0.0
    current_field: Optional[str] = None
    attempts: int = 0
    field_validation_results: Dict[str, Any] = {}
    conversation_context: Dict[str, Any] = {}
    
    # Timestamps
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None


# Request/Response models for API endpoints
class DataValidationRequest(BaseModel):
    """Request model for data validation"""
    producer_data: Dict[str, Any]
    business_type: Optional[str] = None
    validation_level: str = "standard"  # standard, strict, comprehensive


class PromptGenerationRequest(BaseModel):
    """Request model for prompt generation"""
    focus_field: Optional[str] = None  # Updated field name to match API docs
    partial_data: Dict[str, Any]  # Updated field name
    context: Dict[str, Any] = {}  # Updated field name
    attempts: int = 0
    business_type: Optional[str] = None


class PromptGenerationResponse(BaseModel):
    """Response model for prompt generation"""
    prompt: str
    field_name: str  # New field to match API docs
    expected_format: str  # Updated field name
    validation_hint: str  # Updated field name  
    is_critical: bool  # New field
    follow_up_questions: List[str] = []  # New field


class AnswerAssessmentRequest(BaseModel):
    """Request model for answer assessment"""
    question: str  # New field to match API docs
    user_answer: str  # Updated field name
    expected_field: str  # Updated field name
    context: Dict[str, Any] = {}  # Updated field name
    validation_rules: Optional[Dict[str, Any]] = None  # New field


class VerificationScheduleRequest(BaseModel):
    """Request model for verification scheduling"""
    producer_id: str  # New field
    producer_data: Dict[str, Any]
    risk_score: float
    priority_override: Optional[str] = None  # Updated field name
    preferred_time: Optional[str] = None
    contact_method: str = "email"  # email, phone, both
    validation_issues: Optional[List[ValidationIssue]] = None  # New field


class VerificationScheduleResponse(BaseModel):
    """Response model for verification scheduling"""
    verification_id: str  # New field
    producer_id: str  # New field  
    scheduled_time: Optional[datetime] = None
    queue_position: int  # New field
    estimated_wait_hours: int  # New field
    status: str  # New field
    verification_type: str  # New field
