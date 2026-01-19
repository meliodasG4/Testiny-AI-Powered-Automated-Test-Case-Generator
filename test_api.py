import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key: {api_key[:20]}...")

if not api_key:
    print(" No API key found")
    exit()

genai.configure(api_key=api_key)

models_to_test = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-1.5-pro",
]

for model_name in models_to_test:
    print(f"\n Testing {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Hello' in French")
        print(f" Works! Response: {response.text}")
        print(f"Recommended to use: {model_name}")
        break
    except Exception as e:
        print(f"Failed: {str(e)[:120]}")
