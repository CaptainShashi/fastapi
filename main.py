from fastapi import FastAPI, UploadFile, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import os
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="JSON File Upload API",
    description="API for uploading JSON files",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load password from environment variable
PASSWORD = os.getenv("API_PASSWORD")
if not PASSWORD:
    logger.error("API_PASSWORD not set in environment variables")
    raise RuntimeError("API_PASSWORD must be set")

# Dependency for password authentication
async def verify_password(x_password: Optional[str] = Header(None)):
    if x_password != PASSWORD:
        logger.warning("Invalid password attempt")
        raise HTTPException(status_code=401, detail="Invalid password")
    return x_password

@app.post("/upload-json")
async def upload_json(
    file: UploadFile,
    password: str = Depends(verify_password)
):
    # Capture upload time
    upload_time = datetime.now().isoformat()
    
    # Get file size (in bytes)
    file_size = file.size if file.size is not None else 0
    
    # Log upload details
    logger.info(
        f"File upload: time={upload_time}, filename={file.filename}, size={file_size} bytes"
    )
    
    # Check if the uploaded file is a JSON file
    if not file.filename.endswith(".json"):
        logger.error(f"Invalid file type: filename={file.filename}, size={file_size} bytes")
        raise HTTPException(status_code=400, detail="File must be a JSON file")

    try:
        # Read and parse the JSON file
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        logger.info(
            f"Successfully parsed JSON file: filename={file.filename}, size={file_size} bytes"
        )

        # Return the parsed JSON data
        return {
            "message": "JSON file processed successfully",
            "filename": file.filename,
            "data": data
        }

    except json.JSONDecodeError:
        logger.error(
            f"Invalid JSON format: filename={file.filename}, size={file_size} bytes"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.exception(
            f"Error processing file: filename={file.filename}, size={file_size} bytes, error={str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Error processing JSON: {str(e)}")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to the JSON File Upload API. Use /upload-json to upload a JSON file.",
        "docs": "/docs"
    }