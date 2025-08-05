"""
Validation tools for Indian compliance fields
"""
import re
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

class ComplianceValidator:
    """Validation tools for Indian compliance numbers"""
    
    @staticmethod
    def validate_gst(gst_number: str) -> Dict[str, Any]:
        """
        Validate GST number format and structure
        GST Format: 2 digits (state code) + 10 characters (PAN) + 1 digit + 1 letter + 1 digit
        """
        gst_number = gst_number.strip().upper()
        
        # GST regex pattern
        pattern = r'^([0-9]{2})([A-Z]{5}[0-9]{4}[A-Z]{1})([0-9]{1})([A-Z]{1})([0-9]{1})$'
        match = re.match(pattern, gst_number)
        
        if not match:
            return {
                "valid": False,
                "error": "Invalid GST format. Should be 15 characters like: 27AAPFU0939F1ZV",
                "details": None
            }
        
        state_code = match.group(1)
        pan = match.group(2)
        entity_number = match.group(3)
        default_letter = match.group(4)
        checksum = match.group(5)
        
        # State codes validation
        valid_state_codes = {
            "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
            "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
            "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
            "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
            "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
            "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
            "24": "Gujarat", "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra",
            "28": "Andhra Pradesh", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep",
            "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman and Nicobar",
            "36": "Telangana", "37": "Andhra Pradesh (New)", "38": "Ladakh"
        }
        
        if state_code not in valid_state_codes:
            return {
                "valid": False,
                "error": f"Invalid state code: {state_code}",
                "details": None
            }
        
        # Validate default letter (should be 'Z' for normal taxpayers)
        if default_letter != 'Z':
            return {
                "valid": False,
                "error": f"Invalid entity type letter: {default_letter}. Should be 'Z' for normal taxpayers.",
                "details": None
            }
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "state": valid_state_codes[state_code],
                "state_code": state_code,
                "pan": pan,
                "entity_number": entity_number,
                "checksum": checksum
            }
        }
    
    @staticmethod
    def validate_pan(pan_number: str) -> Dict[str, Any]:
        """
        Validate PAN number format
        PAN Format: 5 letters + 4 digits + 1 letter
        4th character indicates holder type
        """
        pan_number = pan_number.strip().upper()
        
        # PAN regex pattern
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        
        if not re.match(pattern, pan_number):
            return {
                "valid": False,
                "error": "Invalid PAN format. Should be 10 characters like: ABCDE1234F",
                "details": None
            }
        
        # 4th character validation
        fourth_char = pan_number[3]
        holder_types = {
            'C': 'Company',
            'P': 'Person',
            'H': 'HUF (Hindu Undivided Family)',
            'F': 'Firm',
            'A': 'Association of Persons',
            'T': 'Trust',
            'B': 'Body of Individuals',
            'L': 'Local Authority',
            'J': 'Artificial Juridical Person',
            'G': 'Government'
        }
        
        if fourth_char not in holder_types:
            return {
                "valid": False,
                "error": f"Invalid holder type character: {fourth_char}",
                "details": None
            }
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "holder_type": holder_types[fourth_char],
                "holder_code": fourth_char
            }
        }
    
    @staticmethod
    def validate_fssai(fssai_number: str) -> Dict[str, Any]:
        """
        Validate FSSAI license number
        FSSAI Format: 14 digits
        First digit indicates the type of business
        """
        fssai_number = fssai_number.strip()
        
        # FSSAI should be 14 digits
        if not re.match(r'^\d{14}$', fssai_number):
            return {
                "valid": False,
                "error": "Invalid FSSAI format. Should be 14 digits.",
                "details": None
            }
        
        # First digit indicates business type
        first_digit = fssai_number[0]
        business_types = {
            '1': 'Manufacturing',
            '2': 'Trading',
            '3': 'Restaurant/Hotel',
            '4': 'Transport',
            '5': 'Retail',
            '6': 'Wholesale',
            '7': 'Import',
            '8': 'Others',
            '9': 'Special Category'
        }
        
        business_type = business_types.get(first_digit, 'Unknown')
        
        # Extract year (digits 3-4)
        year = '20' + fssai_number[2:4]
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "business_type": business_type,
                "registration_year": year,
                "state_code": fssai_number[4:6]
            }
        }
    
    @staticmethod
    def validate_phone(phone_number: str) -> Dict[str, Any]:
        """
        Validate Indian phone number
        Accepts: 10 digit mobile, 11 digit mobile with 0, +91 prefix, landline with STD
        """
        # Remove spaces, dashes, parentheses
        phone_clean = re.sub(r'[\s\-\(\)]', '', phone_number.strip())
        
        # Remove +91 or 91 prefix
        if phone_clean.startswith('+91'):
            phone_clean = phone_clean[3:]
        elif phone_clean.startswith('91') and len(phone_clean) > 10:
            phone_clean = phone_clean[2:]
        
        # Check if it's a valid 10-digit mobile
        if re.match(r'^[6-9]\d{9}$', phone_clean):
            return {
                "valid": True,
                "error": None,
                "details": {
                    "type": "mobile",
                    "number": phone_clean,
                    "formatted": f"+91-{phone_clean[:5]}-{phone_clean[5:]}"
                }
            }
        
        # Check if it's a valid 11-digit mobile (with leading 0)
        if re.match(r'^0[6-9]\d{9}$', phone_clean):
            return {
                "valid": True,
                "error": None,
                "details": {
                    "type": "mobile",
                    "number": phone_clean[1:],
                    "formatted": f"+91-{phone_clean[1:6]}-{phone_clean[6:]}"
                }
            }
        
        # Check for landline (STD code + number)
        if re.match(r'^0\d{2,4}\d{6,8}$', phone_clean) and 10 <= len(phone_clean) <= 12:
            std_length = 3 if phone_clean[1:3] in ['11', '22', '33', '44', '79', '80'] else 4
            std_code = phone_clean[:std_length]
            number = phone_clean[std_length:]
            return {
                "valid": True,
                "error": None,
                "details": {
                    "type": "landline",
                    "std_code": std_code,
                    "number": number,
                    "formatted": f"{std_code}-{number}"
                }
            }
        
        return {
            "valid": False,
            "error": "Invalid phone number. Please provide a valid 10-digit mobile number or landline with STD code.",
            "details": None
        }
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Any]:
        """
        Validate email address format and domain
        """
        email = email.strip().lower()
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return {
                "valid": False,
                "error": "Invalid email format.",
                "details": None
            }
        
        # Extract domain
        domain = email.split('@')[1]
        
        # Check for common typos in popular domains
        common_domains = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'yahooo.com': 'yahoo.com',
            'yahho.com': 'yahoo.com',
            'hotmial.com': 'hotmail.com',
            'outlok.com': 'outlook.com'
        }
        
        suggestion = None
        if domain in common_domains:
            suggestion = email.replace(domain, common_domains[domain])
        
        # Check for disposable email domains (basic list)
        disposable_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        is_disposable = domain in disposable_domains
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "email": email,
                "domain": domain,
                "suggestion": suggestion,
                "is_disposable": is_disposable
            }
        }
    
    @staticmethod
    def validate_pincode(pincode: str) -> Dict[str, Any]:
        """
        Validate Indian PIN code
        Indian PIN codes are 6 digits, first digit indicates region
        """
        pincode = pincode.strip()
        
        if not re.match(r'^\d{6}$', pincode):
            return {
                "valid": False,
                "error": "Invalid PIN code format. Should be 6 digits.",
                "details": None
            }
        
        # First digit indicates region
        first_digit = pincode[0]
        regions = {
            '1': 'Delhi, Haryana, Punjab, Himachal Pradesh, Jammu & Kashmir',
            '2': 'Uttar Pradesh, Uttarakhand',
            '3': 'Rajasthan, Gujarat',
            '4': 'Maharashtra, Madhya Pradesh, Chhattisgarh',
            '5': 'Andhra Pradesh, Telangana, Karnataka',
            '6': 'Tamil Nadu, Kerala',
            '7': 'West Bengal, Odisha, Assam, Sikkim, Arunachal Pradesh',
            '8': 'Bihar, Jharkhand',
            '9': 'Army Post Office (APO), Field Post Office (FPO)'
        }
        
        region = regions.get(first_digit, 'Unknown')
        
        return {
            "valid": True,
            "error": None,
            "details": {
                "pincode": pincode,
                "region": region,
                "region_code": first_digit
            }
        }


class CalendlyScheduler:
    """Integration with Calendly API for scheduling meetings"""
    
    def __init__(self, api_token: str, event_type_uuid: str):
        self.api_token = api_token
        self.event_type_uuid = event_type_uuid
        self.base_url = "https://api.calendly.com"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_available_slots(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """Get available time slots from Calendly"""
        
        # Get event type availability
        url = f"{self.base_url}/event_type_available_times"
        
        params = {
            "event_type": f"https://api.calendly.com/event_types/{self.event_type_uuid}",
            "start_time": date_from.isoformat(),
            "end_time": date_to.isoformat()
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "available_times": []}
    
    def create_scheduled_event(self, 
                              invitee_email: str,
                              invitee_name: str,
                              scheduled_time: datetime,
                              questions: Optional[list] = None,
                              custom_data: Optional[dict] = None) -> Dict[str, Any]:
        """Create a scheduled event through Calendly API"""
        
        # Note: Calendly API v2 doesn't directly support creating scheduled events
        # You typically need to use scheduling links or webhooks
        # This is a simulated implementation
        
        # Generate a one-time scheduling link with pre-filled data
        scheduling_data = {
            "max_event_count": 1,
            "owner": f"https://api.calendly.com/event_types/{self.event_type_uuid}",
            "owner_type": "EventType"
        }
        
        try:
            # Create scheduling link
            url = f"{self.base_url}/scheduling_links"
            response = requests.post(url, headers=self.headers, json=scheduling_data)
            response.raise_for_status()
            
            link_data = response.json()
            booking_url = link_data.get("resource", {}).get("booking_url")
            
            # Add query parameters for pre-filling
            if booking_url:
                params = []
                params.append(f"name={invitee_name}")
                params.append(f"email={invitee_email}")
                
                if questions:
                    for i, q in enumerate(questions[:3]):  # Calendly typically supports up to 3 custom questions
                        params.append(f"a{i+1}={q}")
                
                booking_url += "?" + "&".join(params)
            
            return {
                "success": True,
                "booking_url": booking_url,
                "scheduling_link": link_data.get("resource", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_meeting_for_verification(self,
                                       producer_data: dict,
                                       risk_score: float,
                                       priority: str) -> Dict[str, Any]:
        """Create a verification meeting based on risk assessment"""
        
        # Determine meeting duration based on risk
        if risk_score >= 70:
            meeting_type = "detailed-verification-60min"
            urgency_note = "HIGH RISK - Requires detailed verification"
        elif risk_score >= 50:
            meeting_type = "standard-verification-30min"
            urgency_note = "MEDIUM RISK - Standard verification needed"
        else:
            meeting_type = "quick-verification-15min"
            urgency_note = "LOW RISK - Quick verification"
        
        # Prepare verification questions
        questions = [
            f"Business Type: {producer_data.get('business_type', 'Not provided')}",
            f"Risk Score: {risk_score:.1f}/100 - {urgency_note}",
            f"GST: {producer_data.get('gst_number', 'Not provided')}"
        ]
        
        # Custom data for the meeting
        custom_data = {
            "producer_id": producer_data.get('id'),
            "risk_score": risk_score,
            "priority": priority,
            "verification_type": meeting_type
        }
        
        # Schedule based on priority
        if priority == "urgent":
            date_from = datetime.utcnow()
            date_to = datetime.utcnow() + timedelta(hours=4)
        elif priority == "high":
            date_from = datetime.utcnow()
            date_to = datetime.utcnow() + timedelta(days=1)
        else:
            date_from = datetime.utcnow() + timedelta(days=1)
            date_to = datetime.utcnow() + timedelta(days=3)
        
        # Get available slots
        available_slots = self.get_available_slots(date_from, date_to)
        
        # Create the scheduled event
        result = self.create_scheduled_event(
            invitee_email=producer_data.get('email', ''),
            invitee_name=producer_data.get('name', 'Producer'),
            scheduled_time=date_from,  # This would be an actual slot in production
            questions=questions,
            custom_data=custom_data
        )
        
        return {
            "scheduling_result": result,
            "available_slots": available_slots.get("collection", [])[:5],  # First 5 slots
            "meeting_type": meeting_type,
            "urgency_note": urgency_note
        }