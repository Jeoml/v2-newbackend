"""
Test script to run the FastAPI application
"""
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import uvicorn
    from main import app
    
    if __name__ == "__main__":
        print("🚀 Starting FastAPI Producer Onboarding API...")
        print("📱 The API will be available at:")
        print("   • http://localhost:8000/docs (Swagger UI)")
        print("   • http://localhost:8000/redoc (ReDoc)")
        print("\n🔗 Key endpoints:")
        print("   • POST /api/onboarding/start - Start new onboarding session")
        print("   • POST /api/onboarding/continue/{session_id} - Continue session")
        print("   • POST /api/onboarding/validate-data - Validate producer data")
        print("\n⏹️  Press Ctrl+C to stop the server\n")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure to activate your virtual environment:")
    print("   .venv\\Scripts\\activate")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting server: {e}")
    sys.exit(1)
