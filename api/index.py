from fastapi import FastAPI
import sys
import os
from mangum import Mangum

# Add the root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from main.py
from main import app

# This is required for Vercel serverless functions
app.root_path = "/api"

# Create handler for AWS Lambda/Vercel
handler = Mangum(app)

# Add error handling for serverless environment
@app.middleware("http")
async def add_custom_header(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        return {
            "status": "error",
            "message": "An error occurred in the serverless function",
            "error": str(e)
        } 