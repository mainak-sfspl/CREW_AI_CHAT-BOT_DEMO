import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
    exit()

genai.configure(api_key=api_key)

print("🔍 Checking available models for your API key...")
try:
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
            found = True

    if not found:
        print("⚠️ No models found. Check if the 'Generative Language API' is enabled in Google Cloud Console.")

except Exception as e:
    print(f"❌ Error listing models: {e}")
