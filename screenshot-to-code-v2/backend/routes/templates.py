from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from typing import List, Optional
from config import GEMINI_API_KEY
from prompts.template_prompts import TEMPLATE_CREATION_PROMPT, TEMPLATE_CREATION_SYSTEM_PROMPT
from models.gemini import stream_gemini_response
from llm import Llm

router = APIRouter()

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "user_templates")

# Ensure the directory exists
os.makedirs(TEMPLATE_DIR, exist_ok=True)

class SaveTemplateRequest(BaseModel):
    name: str
    content: str

class GenerateTemplateRequest(BaseModel):
    images: List[str]  # List of data URLs

@router.get("/templates", response_model=List[str])
async def get_templates():
    try:
        files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".html")]
        return sorted(files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{filename}")
async def get_template_content(filename: str):
    # Security check to prevent path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    filepath = os.path.join(TEMPLATE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Template not found")
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates")
async def save_template(request: SaveTemplateRequest):
    filename = request.name
    if not filename.endswith(".html"):
        filename += ".html"
        
    # Security check
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = os.path.join(TEMPLATE_DIR, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(request.content)
        return {"success": True, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/generate")
async def generate_template(request: GenerateTemplateRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="Gemini API key not found")

    try:
        # Construct messages for Gemini
        # We'll put all images in the user message
        content_block = []
        for img_url in request.images:
            content_block.append({
                "type": "image_url",
                "image_url": {"url": img_url}
            })
        
        content_block.append({
            "type": "text", 
            "text": TEMPLATE_CREATION_PROMPT
        })

        messages = [
            {
                "role": "system",
                "content": TEMPLATE_CREATION_SYSTEM_PROMPT
            },
            {
                "role": "user", 
                "content": content_block
            }
        ]

        # Dummy callback since we wait for the full response
        async def dummy_callback(chunk: str):
            pass

        # Use Gemini Flash as requested for free tier
        completion = await stream_gemini_response(
            messages=messages,
            api_key=GEMINI_API_KEY,
            callback=dummy_callback,
            model_name=Llm.GEMINI_3_FLASH_PREVIEW_HIGH.value
        )

        return {"content": completion["code"]}

    except Exception as e:
        print(f"Template generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
