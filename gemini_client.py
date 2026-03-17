import json
import os
import re
import time

from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
from google.genai.types import GenerateContentConfig, ThinkingConfig
from dotenv import load_dotenv
from PIL import Image

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-3.1-flash-lite-preview"
RETRY_DELAYS = [5, 15, 30, 60]  # seconds between attempts

load_dotenv()

FIELDS = [
    "Name",
    "Shirt Name",
    "Birth Date (dd/mm/yyyy)",
    "Height (cm)",
    "Weight (kg)",
    "Preferred Foot",
    "Nationality (ISO2)",
    "Second Nationality (ISO2)",
    "Market Value",
    "Position",
    "Second Position",
    "Club",
    "Contract Expiry Date (dd/mm/yyyy)",
    "Notes",
    "Profile Link",
    "Transfermarkt Link",
    "Address",
    "Phone Number",
    "Studies",
    "League",
    "On loan",
    "Club of origin of the Loan",
    "Representative",
    "Representative's Contact",
    "Contract Expiry Date of Representative (dd/mm/yyyy)",
    "Representative Link",
    "Annual Net Salary",
    "Position Profile",
    "Document ID",
    "Document Expiry Date (dd/mm/yyyy)",
]

PROMPT = """You are a football scouting data extractor.
Extract the following fields from this player profile screenshot.
Return ONLY a valid JSON object with these exact keys (use null for any field not visible):

{fields}

Rules:
- Dates must be formatted as dd/mm/yyyy.
- Nationalities must be ISO 3166-1 alpha-2 codes (e.g. AR, ES, BR).
- Height in cm (integer), Weight in kg (integer).
- Market Value as a plain number in EUR (e.g. 1500000).
- Annual Net Salary as a plain number in EUR per year.
- On loan: true or false (boolean).
- Do not include any explanation or markdown — only the JSON object.
""".format(fields="\n".join(f'- "{f}"' for f in FIELDS))


def _call_with_retry(client, model: str, image, final: bool = False):
    """Try calling model with retries. Returns response or None (unless final=True, then raises)."""
    for attempt, delay in enumerate(RETRY_DELAYS, 1):
        try:
            print(f"  Using model: {model}" if model != PRIMARY_MODEL else "", end="", flush=True)
            return client.models.generate_content(
                model=model,
                contents=[PROMPT, image],
                config=GenerateContentConfig(
                    thinking_config=ThinkingConfig(thinking_budget=0)
                ),
            )
        except (ServerError, ClientError) as e:
            is_quota = isinstance(e, ClientError) and "RESOURCE_EXHAUSTED" in str(e)
            if is_quota:
                # Quota exhausted — no point retrying this model, switch immediately
                print(f"  Quota exhausted [{model}].")
                if final:
                    raise RuntimeError(f"Quota exhausted on both {PRIMARY_MODEL} and {FALLBACK_MODEL}.") from e
                print(f"  Falling back to {FALLBACK_MODEL}...")
                return None
            print(f"  Server busy [{model}] attempt {attempt}/{len(RETRY_DELAYS)}, retrying in {delay}s...")
            time.sleep(delay)
            if attempt == len(RETRY_DELAYS):
                if final:
                    raise RuntimeError(f"All retries exhausted on both {PRIMARY_MODEL} and {FALLBACK_MODEL}.") from e
                print(f"  Falling back to {FALLBACK_MODEL}...")
                return None


def extract_fields(image_path: str, verbose: bool = False, use_fallback: bool = False) -> dict:
    """Send image to Gemini Flash, return parsed dict of 30 fields."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Set GEMINI_API_KEY in .env or environment.")

    client = genai.Client(api_key=api_key)
    image = Image.open(image_path)

    if verbose:
        print("--- PROMPT ---")
        print(PROMPT)
        print("--------------")

    if use_fallback:
        print(f"  Using fallback model: {FALLBACK_MODEL}")
        response = _call_with_retry(client, FALLBACK_MODEL, image, final=True)
    else:
        response = _call_with_retry(client, PRIMARY_MODEL, image) \
            or _call_with_retry(client, FALLBACK_MODEL, image, final=True)
    raw = response.text

    if verbose:
        print("--- RAW RESPONSE ---")
        print(raw)
        print("--------------------")

    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON.\nRaw response:\n{raw}") from e
