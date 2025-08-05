try:
    from main import app
    print("✓ SUCCESS: FastAPI app loaded successfully")
    print("✓ Onboarding agent is ready")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
