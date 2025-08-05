"""
LangGraph agent for AI-powered producer onboarding
"""
from typing import Any, Dict, List, Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from groq import Groq
import json
import uuid
from datetime import datetime, timedelta

from config import GROQ_API_KEY, CALENDLY_API_TOKEN, CALENDLY_EVENT_TYPE_UUID
from producer_onboarding_models import (
    OnboardingStatus, ValidationIssue, 
    AnswerAssessmentResponse, DataValidationResponse
)
from validation_tools import ComplianceValidator, CalendlyScheduler

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize Calendly scheduler
calendly = CalendlyScheduler(
    api_token=CALENDLY_API_TOKEN,
    event_type_uuid=CALENDLY_EVENT_TYPE_UUID
)

# Agent State
class OnboardingState(TypedDict):
    """State for the onboarding conversation"""
    messages: Annotated[list, add_messages]
    session_id: str
    producer_id: str
    collected_data: Dict[str, Any]
    current_field: Optional[str]
    validation_results: Optional[Dict[str, Any]]
    risk_score: float
    status: str
    next_action: str
    conversation_context: Dict[str, Any]
    attempts: int
    field_validation_results: Dict[str, Any]  # Store validation results for each field

# Tool Functions
def validate_field_with_tool(field_name: str, value: str) -> Dict[str, Any]:
    """Use validation tools to validate specific fields"""
    
    validator = ComplianceValidator()
    
    # Map field names to validation functions
    validation_map = {
        'gst_number': validator.validate_gst,
        'gst': validator.validate_gst,
        'pan_number': validator.validate_pan,
        'pan': validator.validate_pan,
        'fssai_number': validator.validate_fssai,
        'fssai': validator.validate_fssai,
        'fssai_license': validator.validate_fssai,
        'phone': validator.validate_phone,
        'phone_number': validator.validate_phone,
        'mobile': validator.validate_phone,
        'email': validator.validate_email,
        'email_address': validator.validate_email,
        'pincode': validator.validate_pincode,
        'pin_code': validator.validate_pincode,
        'postal_code': validator.validate_pincode
    }
    
    # Get the appropriate validation function
    validate_func = validation_map.get(field_name.lower())
    
    if validate_func:
        return validate_func(value)
    
    # Default validation for other fields
    return {
        "valid": True,
        "error": None,
        "details": {"value": value}
    }

def analyze_required_fields(state: OnboardingState) -> OnboardingState:
    """Analyze what fields are required based on business type and context"""
    
    collected = state["collected_data"]
    
    # Use AI to determine required fields dynamically
    analysis_prompt = f"""
    As an expert in Indian business compliance and producer onboarding, analyze the following collected data 
    and determine what additional information is required:

    Collected Data: {json.dumps(collected, indent=2)}

    Based on the business type, domain, and Indian regulatory requirements, determine:
    1. What critical fields are still missing
    2. What documents are required
    3. The priority order for collecting missing information
    4. Any domain-specific requirements

    Consider regulations like:
    - GST requirements
    - FSSAI for food businesses
    - Drug license for pharmaceuticals
    - BIS standards for manufacturing
    - State-specific requirements

    Respond in JSON format:
    {{
        "required_fields": [
            {{"field": "field_name", "priority": 1-10, "reason": "why needed", "category": "basic/compliance/verification"}}
        ],
        "required_documents": [
            {{"document": "doc_type", "mandatory": true/false, "reason": "why needed"}}
        ],
        "next_priority_field": "field_name",
        "domain_specific_requirements": ["list of specific requirements"]
    }}
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        analysis = json.loads(completion.choices[0].message.content.strip())
        state["conversation_context"]["field_analysis"] = analysis
        state["current_field"] = analysis.get("next_priority_field")
        
    except Exception as e:
        print(f"Error analyzing fields: {e}")
        # Fallback to basic required fields
        basic_fields = ["name", "email", "phone", "business_type", "gst_number"]
        for field in basic_fields:
            if field not in collected:
                state["current_field"] = field
                break
    
    return state

def generate_contextual_prompt(state: OnboardingState) -> OnboardingState:
    """Generate a contextual, conversational prompt for the current field"""
    
    current_field = state["current_field"]
    collected = state["collected_data"]
    context = state["conversation_context"]
    
    if not current_field:
        state["next_action"] = "validate"
        return state
    
    # Generate conversational prompt using AI
    prompt_generation = f"""
    You are a friendly, professional onboarding assistant helping a producer/business owner register on our platform.
    
    Context:
    - Current field needed: {current_field}
    - Already collected: {json.dumps(collected, indent=2)}
    - Previous conversation: {state.get('messages', [])[-3:] if state.get('messages') else 'Just starting'}
    
    Generate a natural, conversational prompt to collect the '{current_field}' information.
    
    Guidelines:
    - Be warm and professional
    - Explain why this information is needed (compliance, verification, etc.)
    - If relevant, reference previously collected information
    - For documents, explain acceptable formats
    - Make it feel like a conversation, not a form
    - Include any helpful hints or examples
    - If this is a retry (attempts > 0), acknowledge the issue and provide clearer guidance
    
    Attempts so far: {state.get('attempts', 0)}
    
    Respond with just the conversational prompt, nothing else.
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt_generation}],
            temperature=0.7,
            max_tokens=300
        )
        
        prompt = completion.choices[0].message.content.strip()
        state["messages"].append({"role": "assistant", "content": prompt})
        state["next_action"] = "wait_response"
        
    except Exception as e:
        print(f"Error generating prompt: {e}")
        # Fallback prompt
        prompt = f"Could you please provide your {current_field}?"
        state["messages"].append({"role": "assistant", "content": prompt})
        state["next_action"] = "wait_response"
    
    return state

def assess_user_response(state: OnboardingState) -> OnboardingState:
    """Assess the user's response using AI"""
    
    if not state["messages"] or len(state["messages"]) < 2:
        state["next_action"] = "prompt"
        return state
    
    # Get the last user message
    user_response = None
    for msg in reversed(state["messages"]):
        # Handle both dict and LangChain message object formats
        if hasattr(msg, 'type') and msg.type == "human":
            # LangChain HumanMessage object
            user_response = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            # Dictionary format
            user_response = msg.get("content", "")
            break
    
    if not user_response:
        state["next_action"] = "prompt"
        return state
    
    current_field = state["current_field"]
    
    # Use AI to assess the response
    assessment_prompt = f"""
    Assess if the user's response is valid and complete for the requested field.
    
    Field requested: {current_field}
    User response: {user_response}
    Context: {json.dumps(state["collected_data"], indent=2)}
    
    Perform these checks:
    1. Is the response relevant to the field requested?
    2. Is the format correct? (e.g., email format, phone number format, GST format)
    3. Is the information complete and usable?
    4. Are there any red flags or suspicious patterns?
    5. Can you extract the actual value from the response?
    
    For Indian compliance, check:
    - GST: 15 characters (2 digit state code + 10 char PAN + 1 digit + 1 check alphabet + 1 digit)
    - PAN: 10 characters (5 letters + 4 digits + 1 letter)
    - Phone: Valid Indian mobile (10 digits) or landline
    - Pincode: 6 digits
    
    Respond in JSON format:
    {{
        "valid": true/false,
        "confidence": 0.0-1.0,
        "extracted_value": "the actual value to store",
        "feedback": "Clear explanation of what's wrong or 'Looks good!'",
        "requires_clarification": true/false,
        "clarification_prompt": "optional prompt for clarification"
    }}
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": assessment_prompt}],
            temperature=0.2,
            max_tokens=500
        )
        
        assessment = json.loads(completion.choices[0].message.content.strip())
        
        if assessment["valid"] and assessment["confidence"] > 0.7:
            # Store the extracted value
            state["collected_data"][current_field] = assessment["extracted_value"]
            state["attempts"] = 0
            
            # Thank the user and move to next field
            thank_msg = f"Great! I've recorded your {current_field}."
            state["messages"].append({"role": "assistant", "content": thank_msg})
            
            # Determine next action
            state["next_action"] = "analyze_fields"
        else:
            # Response not valid, provide feedback
            state["attempts"] = state.get("attempts", 0) + 1
            
            if state["attempts"] > 2:
                # Too many attempts, mark for manual review
                state["messages"].append({
                    "role": "assistant", 
                    "content": f"I'm having trouble understanding your {current_field}. Let's move on for now and our team will help you with this later."
                })
                state["collected_data"][f"{current_field}_pending"] = user_response
                state["next_action"] = "analyze_fields"
            else:
                # Provide feedback and retry
                state["messages"].append({
                    "role": "assistant",
                    "content": assessment["feedback"]
                })
                if assessment.get("clarification_prompt"):
                    state["messages"].append({
                        "role": "assistant",
                        "content": assessment["clarification_prompt"]
                    })
                state["next_action"] = "wait_response"
        
    except Exception as e:
        print(f"Error assessing response: {e}")
        # Fallback - accept the response and move on
        state["collected_data"][current_field] = user_response
        state["next_action"] = "analyze_fields"
    
    return state

def validate_all_data(state: OnboardingState) -> OnboardingState:
    """Validate all collected data and calculate risk score"""
    
    data = state["collected_data"]
    field_validations = state.get("field_validation_results", {})
    
    # Count validation failures
    validation_failures = sum(1 for v in field_validations.values() if not v.get("valid", True))
    fields_needing_review = sum(1 for v in field_validations.values() if v.get("needs_manual_review", False))
    
    # Use AI to perform comprehensive validation
    validation_prompt = f"""
    As a compliance expert, validate the following producer data for completeness and authenticity:
    
    Data: {json.dumps(data, indent=2)}
    
    Field Validation Results: {json.dumps(field_validations, indent=2)}
    
    Consider:
    1. Number of validation failures: {validation_failures}
    2. Fields needing manual review: {fields_needing_review}
    3. Check completeness - are all critical fields present?
    4. Check consistency - does the data make sense together?
    5. Identify any red flags or suspicious patterns
    6. Calculate a risk score (0-100) based on:
       - Completeness (30%)
       - Data validity (30%) - weight validation failures heavily
       - Business credibility (20%)
       - Compliance with regulations (20%)
    
    Add 10 points to risk score for each validation failure.
    Add 5 points for each field needing manual review.
    
    Consider Indian business regulations and typical patterns.
    
    Respond in JSON format:
    {{
        "completeness_percentage": 0-100,
        "is_complete": true/false,
        "issues": [
            {{"field": "field_name", "issue": "description", "severity": 0.0-1.0}}
        ],
        "risk_score": 0-100,
        "risk_factors": ["list of risk factors"],
        "recommendations": ["list of recommendations"],
        "requires_manual_verification": true/false
    }}
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": validation_prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        validation = json.loads(completion.choices[0].message.content.strip())
        state["validation_results"] = validation
        state["risk_score"] = validation["risk_score"]
        
        # Force manual verification if there were validation failures
        if validation_failures > 0 or fields_needing_review > 0:
            validation["requires_manual_verification"] = True
            state["validation_results"]["requires_manual_verification"] = True
        
        if validation["is_complete"] and validation["risk_score"] < 50 and validation_failures == 0:
            state["status"] = "completed"
            state["next_action"] = "complete"
        elif validation["requires_manual_verification"]:
            state["status"] = "pending_verification"
            state["next_action"] = "schedule_verification"
        else:
            state["next_action"] = "analyze_fields"
        
    except Exception as e:
        print(f"Error validating data: {e}")
        state["risk_score"] = 50.0  # Default medium risk
        state["next_action"] = "schedule_verification"
    
    return state

def schedule_verification(state: OnboardingState) -> OnboardingState:
    """Schedule manual verification using Calendly if needed"""
    
    risk_score = state["risk_score"]
    validation_results = state.get("validation_results", {})
    producer_data = state["collected_data"]
    
    # Determine verification priority
    if risk_score >= 70:
        priority = "urgent"
        meeting_type = "High Risk Verification"
    elif risk_score >= 50:
        priority = "high"
        meeting_type = "Medium Risk Verification"
    else:
        priority = "normal"
        meeting_type = "Standard Verification"
    
    # Check if we have valid contact information
    has_valid_email = producer_data.get("email") and state.get("field_validation_results", {}).get("email", {}).get("valid", False)
    has_valid_phone = producer_data.get("phone") and state.get("field_validation_results", {}).get("phone", {}).get("valid", False)
    
    if not has_valid_email and not has_valid_phone:
        # Can't schedule without contact info
        verification_msg = f"""
        Your application requires manual verification due to the risk assessment (score: {risk_score:.1f}/100).
        
        However, we need valid contact information to schedule a verification meeting.
        Please ensure you provide a valid email address and phone number.
        
        Once you update your contact information, our team will reach out to schedule the verification.
        """
    else:
        # Try to schedule via Calendly
        try:
            scheduling_result = calendly.create_meeting_for_verification(
                producer_data=producer_data,
                risk_score=risk_score,
                priority=priority
            )
            
            if scheduling_result["scheduling_result"]["success"]:
                booking_url = scheduling_result["scheduling_result"]["booking_url"]
                urgency_note = scheduling_result["urgency_note"]
                
                verification_msg = f"""
                Thank you for providing your information! 
                
                Based on our initial review:
                - Risk Score: {risk_score:.1f}/100
                - Assessment: {urgency_note}
                - Verification Type: {meeting_type}
                
                To complete your verification, please schedule a meeting using this link:
                {booking_url}
                
                Available time slots have been prepared based on the urgency of your application.
                You'll receive a confirmation email at {producer_data.get('email')} once you book a slot.
                
                Is there anything specific you'd like us to know before the verification meeting?
                """
            else:
                # Fallback if Calendly scheduling fails
                raise Exception("Calendly scheduling failed")
                
        except Exception as e:
            print(f"Error scheduling via Calendly: {e}")
            # Fallback message
            if priority == "urgent":
                wait_time = "2-4 hours"
            elif priority == "high":
                wait_time = "4-8 hours"
            else:
                wait_time = "within 24 hours"
            
            verification_msg = f"""
            Thank you for providing your information! 
            
            Based on our initial review (risk score: {risk_score:.1f}/100), your application requires manual verification.
            
            Priority: {priority.upper()}
            Expected review time: {wait_time}
            
            Our verification team will contact you at:
            - Email: {producer_data.get('email', 'Not provided')}
            - Phone: {producer_data.get('phone', 'Not provided')}
            
            Please ensure you're available during business hours for the verification call.
            
            Is there anything else you'd like to add to help expedite the verification process?
            """
    
    state["messages"].append({"role": "assistant", "content": verification_msg})
    state["status"] = "pending_verification"
    state["next_action"] = "end"
    
    return state

def complete_onboarding(state: OnboardingState) -> OnboardingState:
    """Complete the onboarding successfully"""
    
    completion_msg = f"""
    Excellent! Your onboarding is complete. 🎉
    
    Here's what happens next:
    1. You'll receive a confirmation email at {state['collected_data'].get('email')}
    2. Your account will be activated within the next hour
    3. You can start listing your products once activated
    
    Your risk assessment score: {state['risk_score']:.1f}/100 (Low risk)
    
    Thank you for choosing our platform! If you have any questions, please don't hesitate to ask.
    """
    
    state["messages"].append({"role": "assistant", "content": completion_msg})
    state["status"] = "completed"
    state["next_action"] = "end"
    
    return state

# Decision functions
def should_continue(state: OnboardingState) -> str:
    """Decide the next step in the workflow"""
    next_action = state.get("next_action", "analyze_fields")
    
    if next_action == "end" or state["status"] in ["completed", "failed"]:
        return "end"
    
    return next_action

# Create the workflow
def create_onboarding_workflow():
    """Create and compile the onboarding workflow"""
    
    workflow = StateGraph(OnboardingState)
    
    # Add nodes
    workflow.add_node("analyze_fields", analyze_required_fields)
    workflow.add_node("prompt", generate_contextual_prompt)
    workflow.add_node("assess", assess_user_response)
    workflow.add_node("validate", validate_all_data)
    workflow.add_node("schedule_verification", schedule_verification)
    workflow.add_node("complete", complete_onboarding)
    
    # Add edges
    workflow.add_edge(START, "analyze_fields")
    
    # Add conditional edges based on next_action
    workflow.add_conditional_edges(
        "analyze_fields",
        lambda x: "prompt" if x["current_field"] else "validate",
        {
            "prompt": "prompt",
            "validate": "validate"
        }
    )
    
    workflow.add_edge("prompt", END)  # Wait for user response
    workflow.add_edge("assess", "analyze_fields")
    
    workflow.add_conditional_edges(
        "validate",
        lambda x: x["next_action"],
        {
            "complete": "complete",
            "schedule_verification": "schedule_verification",
            "analyze_fields": "analyze_fields"
        }
    )
    
    workflow.add_edge("schedule_verification", END)
    workflow.add_edge("complete", END)
    
    return workflow.compile()

# Create the compiled workflow
onboarding_agent = create_onboarding_workflow()