"""
Validation tools for producer onboarding
"""
import re
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid


class ComplianceValidator:
    """Validator for Indian business compliance documents and information"""
    
    def validate_gst(self, gst_number: str) -> Dict[str, Any]:
        """Validate GST number format and structure"""
        if not gst_number:
            return {"valid": False, "error": "GST number is required"}
        
        # Remove spaces and convert to uppercase
        gst_clean = gst_number.replace(" ", "").upper()
        
        # GST format: 2 digit state code + 10 char PAN + 1 digit + 1 check alphabet + 1 digit
        gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
        
        if not re.match(gst_pattern, gst_clean):
            return {
                "valid": False, 
                "error": "Invalid GST format. GST should be 15 characters (e.g., 27AAPFU0939F1ZV)"
            }
        
        # Extract state code
        state_code = gst_clean[:2]
        state_map = {
            "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
            "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
            "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
            "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
            "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
            "16": "Tripura", "17": "Meghalaya", "18": "Assam",
            "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
            "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
            "25": "Daman and Diu", "26": "Dadra and Nagar Haveli", "27": "Maharashtra",
            "28": "Karnataka", "29": "Goa", "30": "Lakshadweep",
            "31": "Kerala", "32": "Tamil Nadu", "33": "Puducherry",
            "34": "Andaman and Nicobar Islands", "35": "Andhra Pradesh", "36": "Telangana",
            "37": "Andhra Pradesh", "38": "Ladakh"
        }
        
        state_name = state_map.get(state_code, "Unknown")
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "state_code": state_code,
                "state": state_name,
                "formatted_gst": gst_clean
            }
        }
    
    def validate_pan(self, pan_number: str) -> Dict[str, Any]:
        """Validate PAN number format"""
        if not pan_number:
            return {"valid": False, "error": "PAN number is required"}
        
        # Remove spaces and convert to uppercase
        pan_clean = pan_number.replace(" ", "").upper()
        
        # PAN format: 5 letters + 4 digits + 1 letter
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        
        if not re.match(pan_pattern, pan_clean):
            return {
                "valid": False,
                "error": "Invalid PAN format. PAN should be 10 characters (e.g., ABCDE1234F)"
            }
        
        # Determine holder type from 4th character
        holder_type_map = {
            'P': 'Individual',
            'C': 'Company', 
            'H': 'HUF',
            'F': 'Firm',
            'A': 'Association of Persons',
            'T': 'Trust',
            'B': 'Body of Individuals',
            'L': 'Local Authority',
            'J': 'Artificial Juridical Person',
            'G': 'Government'
        }
        
        holder_type = holder_type_map.get(pan_clean[3], 'Unknown')
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "holder_type": holder_type,
                "formatted_pan": pan_clean
            }
        }
    
    def validate_fssai(self, fssai_number: str) -> Dict[str, Any]:
        """Validate FSSAI license number"""
        if not fssai_number:
            return {"valid": False, "error": "FSSAI license number is required"}
        
        # Remove spaces
        fssai_clean = fssai_number.replace(" ", "")
        
        # FSSAI is 14 digits
        if not fssai_clean.isdigit() or len(fssai_clean) != 14:
            return {
                "valid": False,
                "error": "FSSAI license should be exactly 14 digits"
            }
        
        # First digit indicates license type
        license_type_map = {
            '1': 'Central License',
            '2': 'State License', 
            '3': 'Registration'
        }
        
        license_type = license_type_map.get(fssai_clean[0], 'Unknown')
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "business_type": license_type,
                "formatted_fssai": fssai_clean
            }
        }
    
    def validate_phone(self, phone_number: str) -> Dict[str, Any]:
        """Validate Indian phone number"""
        if not phone_number:
            return {"valid": False, "error": "Phone number is required"}
        
        # Remove spaces, dashes, and parentheses
        phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone_number)
        
        # Remove country code if present
        if phone_clean.startswith('91') and len(phone_clean) == 12:
            phone_clean = phone_clean[2:]
        elif phone_clean.startswith('+91') and len(phone_clean) == 13:
            phone_clean = phone_clean[3:]
        
        # Mobile number (10 digits starting with 6-9)
        mobile_pattern = r'^[6-9][0-9]{9}$'
        
        # Landline with STD code (10-11 digits)
        landline_pattern = r'^[0-9]{2,4}[0-9]{6,8}$'
        
        if re.match(mobile_pattern, phone_clean):
            return {
                "valid": True,
                "error": None,
                "details": {
                    "type": "mobile",
                    "formatted_phone": phone_clean
                }
            }
        elif re.match(landline_pattern, phone_clean) and len(phone_clean) >= 10:
            return {
                "valid": True,
                "error": None,
                "details": {
                    "type": "landline",
                    "formatted_phone": phone_clean
                }
            }
        else:
            return {
                "valid": False,
                "error": "Invalid phone number. Please provide a valid Indian mobile number (10 digits) or landline with STD code"
            }
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email address with suggestions"""
        if not email:
            return {"valid": False, "error": "Email address is required"}
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email.strip()):
            # Try to suggest corrections for common typos
            suggestions = []
            email_lower = email.lower().strip()
            
            # Common domain typos
            typo_corrections = {
                'gmail.com': ['gmai.com', 'gmial.com', 'gamil.com', 'gmail.co'],
                'yahoo.com': ['yahoo.co', 'yaho.com', 'yahoo.in'],
                'outlook.com': ['outlok.com', 'outlook.co'],
                'hotmail.com': ['hotmai.com', 'hotmail.co']
            }
            
            for correct_domain, typos in typo_corrections.items():
                for typo in typos:
                    if typo in email_lower:
                        suggestion = email_lower.replace(typo, correct_domain)
                        suggestions.append(suggestion)
                        break
            
            return {
                "valid": False,
                "error": "Invalid email format",
                "details": {
                    "suggestion": suggestions[0] if suggestions else None
                }
            }
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "formatted_email": email.strip().lower()
            }
        }
    
    def validate_pincode(self, pincode: str) -> Dict[str, Any]:
        """Validate Indian PIN code"""
        if not pincode:
            return {"valid": False, "error": "PIN code is required"}
        
        # Remove spaces
        pin_clean = pincode.replace(" ", "")
        
        # Indian PIN codes are 6 digits
        if not pin_clean.isdigit() or len(pin_clean) != 6:
            return {
                "valid": False,
                "error": "Invalid PIN code. Indian PIN codes are 6 digits (e.g., 400001)"
            }
        
        # First digit indicates postal region
        region_map = {
            '1': 'Northern',
            '2': 'Northern', 
            '3': 'Western',
            '4': 'Western',
            '5': 'Southern',
            '6': 'Southern',
            '7': 'Eastern',
            '8': 'Eastern',
            '9': 'Army Postal Service'
        }
        
        region = region_map.get(pin_clean[0], 'Unknown')
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "region": region,
                "formatted_pincode": pin_clean
            }
        }


class CalendlyScheduler:
    """Calendly integration for scheduling verification meetings"""
    
    def __init__(self, api_token: str, event_type_uuid: str):
        self.api_token = api_token
        self.event_type_uuid = event_type_uuid
        self.base_url = "https://api.calendly.com"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_meeting_for_verification(self, producer_data: Dict[str, Any], risk_score: float, priority: str) -> Dict[str, Any]:
        """Create a verification meeting based on risk assessment"""
        
        # Determine urgency and meeting duration
        if risk_score >= 70:
            urgency_note = "High Risk - Urgent verification required"
            meeting_duration = 45  # minutes
        elif risk_score >= 50:
            urgency_note = "Medium Risk - Priority verification needed"
            meeting_duration = 30
        else:
            urgency_note = "Standard verification process"
            meeting_duration = 20
        
        # Generate meeting details
        meeting_details = {
            "event_type_uuid": self.event_type_uuid,
            "producer_data": producer_data,
            "risk_score": risk_score,
            "priority": priority,
            "meeting_duration": meeting_duration,
            "notes": f"Producer verification meeting. {urgency_note}",
            "created_at": datetime.now().isoformat()
        }
        
        # For now, return a mock booking URL since we don't have real Calendly credentials
        # In production, this would make actual API calls to Calendly
        booking_url = f"https://calendly.com/verification-team/producer-verification-{priority}"
        
        return {
            "scheduling_result": {
                "success": True,
                "booking_url": booking_url,
                "meeting_id": str(uuid.uuid4()),
                "duration_minutes": meeting_duration
            },
            "urgency_note": urgency_note,
            "priority": priority,
            "risk_score": risk_score
        }
    
    def get_available_slots(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get available time slots for scheduling"""
        # Mock implementation - in production would call Calendly API
        return {
            "available_slots": [
                {"start_time": "2025-08-06T10:00:00Z", "end_time": "2025-08-06T10:30:00Z"},
                {"start_time": "2025-08-06T14:00:00Z", "end_time": "2025-08-06T14:30:00Z"},
                {"start_time": "2025-08-07T09:00:00Z", "end_time": "2025-08-07T09:30:00Z"}
            ]
        }
