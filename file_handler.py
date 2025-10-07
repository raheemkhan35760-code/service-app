from fastapi import UploadFile
import os
import uuid
import shutil
from pathlib import Path

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded image or video file"""
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

def get_file_url(file_path: str) -> str:
    """Convert file path to accessible URL"""
    return f"https://api.homeservepro.com/{file_path}"
