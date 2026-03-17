"""
api.py — FastAPI wrapper for headers_transfer.

POST /extract   Upload a screenshot, get back the 30 extracted fields as JSON.
GET  /health    Health check for Docker / load balancers.
"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from google.genai.errors import ClientError

from gemini_client import extract_fields

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

app = FastAPI(title="headers-transfer", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    suffix = ext if ext else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        data = extract_fields(tmp_path)
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ClientError as e:
        raise HTTPException(status_code=429, detail=f"Gemini quota exhausted: {e}")
    finally:
        os.unlink(tmp_path)

    return JSONResponse({"status": "ok", "file": file.filename, "data": data})
