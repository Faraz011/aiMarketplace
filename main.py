import os
import json
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Import expert system after environment variables are loaded
import expert_system as es

app = FastAPI(
    title="AI Marketplace API",
    description="API for AI Marketplace with blockchain integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {
        "status": "AI Marketplace API is running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/api/task")
async def run_task(request: Request):
    try:
        data = await request.json()
        task = data.get("task")
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task is required in the request body"
            )
        
        # Run the expert system
        try:
            graph = es.build_graph()
            result = graph.invoke({"task": task})
            
            return {
                "success": True,
                "result": str(result.get("result", "")),
                "verdict": result.get("verdict"),
                "approved": result.get("approved"),
                "blockchain_registered": result.get("blockchain_registered"),
                "payment_released": result.get("payment_released"),
                "result_hash": result.get("result_hash")
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing task: {str(e)}"
            )
            
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
