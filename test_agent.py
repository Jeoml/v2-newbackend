"""
Test script to verify the agent module works correctly
"""
import sys
import traceback

def test_imports():
    """Test that all modules can be imported successfully"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from producer_onboarding_models import OnboardingStatus, ValidationIssue
        print("✓ producer_onboarding_models imported successfully")
        
        from validation_tools import ComplianceValidator, CalendlyScheduler
        print("✓ validation_tools imported successfully")
        
        from agent import OnboardingState, create_onboarding_workflow
        print("✓ agent imported successfully")
        
        # Test creating a validator
        validator = ComplianceValidator()
        print("✓ ComplianceValidator created successfully")
        
        # Test a simple validation
        result = validator.validate_email("test@example.com")
        print(f"✓ Email validation test: {result['valid']}")
        
        # Test creating the workflow
        workflow = create_onboarding_workflow()
        print("✓ Onboarding workflow created successfully")
        
        print("\n🎉 All tests passed! The agent.py file is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
