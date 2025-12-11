"""
Test script to verify Gemini API integration works correctly.
Run this to check if all components are properly installed and configured.
"""

import sys
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported."""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)
    
    tests = {
        'PIL': 'pillow',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'streamlit': 'streamlit',
        'google.generativeai': 'google-generativeai'
    }
    
    all_ok = True
    for module, package in tests.items():
        try:
            __import__(module)
            print(f"✓ {module:30} OK")
        except ImportError as e:
            print(f"✗ {module:30} MISSING - Install with: pip install {package}")
            all_ok = False
    
    return all_ok

def test_gemini_module():
    """Test if gemini_card_detector module works."""
    print("\n" + "=" * 60)
    print("Testing gemini_card_detector module...")
    print("=" * 60)
    
    try:
        from gemini_card_detector import (
            configure_gemini,
            detect_card_type,
            extract_card_text,
            analyze_card_complete,
            pil_to_base64
        )
        print("✓ All functions imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import gemini_card_detector: {e}")
        return False

def test_verify_module():
    """Test if verify module works."""
    print("\n" + "=" * 60)
    print("Testing verify module...")
    print("=" * 60)
    
    try:
        from verify import (
            analyze_card_gemini,
            detect_card_type_gemini,
            extract_card_text_gemini,
            pil_from_upload,
            validate_fields
        )
        print("✓ All functions imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import verify: {e}")
        return False

def test_api_key_format(api_key):
    """Test if API key format is valid."""
    print("\n" + "=" * 60)
    print("Testing API Key...")
    print("=" * 60)
    
    if not api_key:
        print("✗ No API key provided")
        return False
    
    if len(api_key) < 10:
        print(f"✗ API key appears invalid (too short): {api_key[:5]}...")
        return False
    
    print(f"✓ API key format looks valid (length: {len(api_key)})")
    print(f"  First 10 chars: {api_key[:10]}...")
    return True

def test_gemini_config(api_key):
    """Test if Gemini API can be configured."""
    print("\n" + "=" * 60)
    print("Testing Gemini Configuration...")
    print("=" * 60)
    
    if not api_key:
        print("⚠ Skipping - no API key provided")
        return None
    
    try:
        from gemini_card_detector import configure_gemini
        result = configure_gemini(api_key)
        if result:
            print("✓ Gemini API configured successfully")
            print("  You can now use Gemini functions")
            return True
        else:
            print("✗ Failed to configure Gemini API")
            print("  Check your API key validity")
            return False
    except Exception as e:
        print(f"✗ Error testing Gemini configuration: {e}")
        return False

def check_files():
    """Check if all required files exist."""
    print("\n" + "=" * 60)
    print("Checking required files...")
    print("=" * 60)
    
    files = {
        'gemini_card_detector.py': 'Gemini API integration module',
        'verify.py': 'Validation functions',
        'app.py': 'Original Streamlit app',
        'app_gemini.py': 'Gemini-enhanced Streamlit app',
        'requirements.txt': 'Dependencies list',
        'GEMINI_USAGE.py': 'Usage examples',
        'GEMINI_README.md': 'Documentation'
    }
    
    all_exist = True
    for filename, description in files.items():
        path = Path(filename)
        if path.exists():
            print(f"✓ {filename:30} exists ({description})")
        else:
            print(f"✗ {filename:30} MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Gemini ID Verification System - Setup Verification".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Check files
    files_ok = check_files()
    
    # Test imports
    imports_ok = test_imports()
    
    # Test modules
    gemini_ok = test_gemini_module()
    verify_ok = test_verify_module()
    
    # Get API key from user or environment
    api_key = input("\nEnter your Gemini API key (or press Enter to skip): ").strip()
    
    # Test API key
    api_key_ok = test_api_key_format(api_key) if api_key else None
    
    # Test Gemini configuration
    gemini_config_ok = test_gemini_config(api_key) if api_key else None
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    summary = {
        "Files Check": "✓ PASS" if files_ok else "✗ FAIL",
        "Imports": "✓ PASS" if imports_ok else "✗ FAIL",
        "Gemini Module": "✓ PASS" if gemini_ok else "✗ FAIL",
        "Verify Module": "✓ PASS" if verify_ok else "✗ FAIL",
        "API Key Format": "✓ PASS" if api_key_ok else ("⚠ SKIP" if api_key_ok is None else "✗ FAIL"),
        "Gemini Config": "✓ PASS" if gemini_config_ok else ("⚠ SKIP" if gemini_config_ok is None else "✗ FAIL"),
    }
    
    for test_name, result in summary.items():
        print(f"{test_name:20} {result:10}")
    
    # Overall status
    critical_pass = files_ok and imports_ok and gemini_ok and verify_ok
    
    print("\n" + "=" * 60)
    if critical_pass:
        print("✓ READY TO USE")
        print("\nYou can now run:")
        print("  1. Streamlit app:  python -m streamlit run app_gemini.py")
        print("  2. Python scripts: from gemini_card_detector import *")
        print("  3. See examples:   python GEMINI_USAGE.py")
    else:
        print("✗ SETUP INCOMPLETE")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
        print("\nThen run this script again to verify.")
    print("=" * 60)
    
    return 0 if critical_pass else 1

if __name__ == "__main__":
    sys.exit(main())

