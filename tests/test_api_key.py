"""
Test if Gemini API key is valid and what models are available
"""

import os
import google.generativeai as genai
import sys

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ GEMINI_API_KEY environment variable not set")
    sys.exit(1)

print(f"API Key (first 20 chars): {api_key[:20]}...")

try:
    genai.configure(api_key=api_key)
    print("✓ API configured successfully")
except Exception as e:
    print(f"❌ Failed to configure API: {e}")
    sys.exit(1)

# Try to list available models
print("\nAttempting to list available models...")
try:
    models = genai.list_models()
    print(f"✓ Retrieved {len(list(models))} models")
    
    # Re-fetch to display
    models = genai.list_models()
    print("\nAvailable Models:")
    for model in models:
        print(f"  - {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"    Methods: {model.supported_generation_methods}")
        
except Exception as e:
    print(f"❌ Failed to list models: {e}")
    import traceback
    traceback.print_exc()

# Try a simple text generation
print("\nTesting simple text generation...")
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say 'Hello from Gemini!'")
    print(f"✓ Response: {response.text}")
except Exception as e:
    print(f"❌ Text generation failed: {e}")
    
# Check model availability with explicit listing
print("\nChecking for latest models...")
try:
    import subprocess
    result = subprocess.run(
        [sys.executable, '-c', 
         "import google.generativeai as genai; "
         "genai.configure(api_key='%s'); "
         "print([m.name for m in genai.list_models()])" % api_key],
        capture_output=True,
        text=True
    )
    print("Models from subprocess:")
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
except Exception as e:
    print(f"Error running subprocess: {e}")
