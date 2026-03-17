import json
import os
import re
import time
from pathlib import Path

from google import genai
from google.genai.errors import ServerError, ClientError
from google.genai.types import GenerateContentConfig, ThinkingConfig
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# Load waterfall model list sorted by priority order
_limits_path = Path(__file__).parent / "docs" / "GEMINI_usage_limits.json"
with open(_limits_path) as _f:
    _plan = json.load(_f)
MODELS = [m["model_name"] for m in sorted(_plan["fallback_strategy"], key=lambda m: m["order"])]

MAX_MINUTE_RETRIES = 3  # max sleeps per model before giving up on rate limit

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


def extract_fields(image_path: str, verbose: bool = False, use_fallback: bool = False) -> dict:
    """Send image to Gemini, return parsed dict of 30 fields.

    Waterfall strategy: tries models in order from GEMINI_usage_limits.json.
    - PerMinute quota hit  → sleep 60 s, retry same model (up to MAX_MINUTE_RETRIES times).
    - PerDay quota hit     → move immediately to next model in the list.
    - All models drained   → raise RuntimeError.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Set GEMINI_API_KEY in .env or environment.")

    client = genai.Client(api_key=api_key)
    image = Image.open(image_path)

    if verbose:
        print("--- PROMPT ---")
        print(PROMPT)
        print("--------------")

    models = MODELS[1:] if use_fallback else MODELS

    response = None
    for model_idx, model in enumerate(models):
        minute_retries = 0

        while True:  # inner loop: retry same model on PerMinute errors
            try:
                if model != models[0]:
                    print(f"  Using model: {model}", flush=True)
                response = client.models.generate_content(
                    model=model,
                    contents=[PROMPT, image],
                    config=GenerateContentConfig(
                        thinking_config=ThinkingConfig(thinking_budget=0)
                    ),
                )
                break  # success — exit inner loop

            except ClientError as e:
                err = str(e)
                if "RESOURCE_EXHAUSTED" in err:
                    if "PerMinute" in err and minute_retries < MAX_MINUTE_RETRIES:
                        minute_retries += 1
                        print(f"  Rate limited [{model}] ({minute_retries}/{MAX_MINUTE_RETRIES}), sleeping 60s...")
                        time.sleep(60)
                    else:
                        # PerDay exhausted, or PerMinute retries exceeded
                        print(f"  Daily quota exhausted [{model}], switching to next model...")
                        break  # exit inner loop to pick next model
                else:
                    raise

            except ServerError:
                print(f"  Server busy [{model}], retrying in 30s...")
                time.sleep(30)

        if response is not None:
            break  # got a response — exit model loop

    if response is None:
        raise RuntimeError("Critical: All free tier models exhausted for today.")

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
