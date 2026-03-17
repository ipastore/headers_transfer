"""Quick test — verifies the Gemini API key and SDK are working."""

from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)
print(f"API key: {api_key[:6]}...{api_key[-4:]}")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello in one word.",
    config=GenerateContentConfig(
        thinking_config=ThinkingConfig(thinking_budget=0)
    ),
)
print("Gemini response:", response.text)

