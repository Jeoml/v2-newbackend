"""
Configuration settings and environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./transparency_assessment.db")

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Calendly configuration
CALENDLY_API_TOKEN = os.getenv("CALENDLY_API_TOKEN")
CALENDLY_EVENT_TYPE_UUID = os.getenv("CALENDLY_EVENT_TYPE_UUID")

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")

# Indian Consumer Safety Guidelines Questions
TRANSPARENCY_QUESTIONS = [
    "Please provide detailed information about all ingredients/components used in your product. Are there any potentially harmful substances that consumers should be aware of?",
    
    "What quality control measures and testing procedures do you implement during manufacturing? Please share your quality certifications and compliance standards.",
    
    "Are there any known side effects, risks, or contraindications associated with your product? How do you communicate these to consumers?",
    
    "Please describe your product's environmental impact and disposal methods. What sustainable practices do you follow in production?",
    
    "What is your product's shelf life, storage requirements, and proper usage instructions? How do you ensure consumers receive accurate information?",
    
    "Do you have a system for tracking adverse events, consumer complaints, and product recalls? How transparent are you about product issues and their resolution?"
]