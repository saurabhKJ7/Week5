from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket
from fastapi.websockets.exceptions import WebSocketDisconnect
import asyncio
import json
from typing import List

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.websocket_manager import ConnectionManager

app = FastAPI(
    title="Stock Market Chat API",
    description="Real-time stock market data and AI-powered chat application",
    version="1.0.0",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
manager = ConnectionManager()

@app.websocket("/ws/stocks")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process the received data (e.g., subscribe to specific stocks)
            await manager.broadcast(json.dumps({"message": "Stock update"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Stock Market Chat API"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 