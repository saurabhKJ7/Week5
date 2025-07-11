import os
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import socketio
import uuid
import asyncio
import numpy as np
from e2b_code_interpreter import AsyncSandbox  # Changed to AsyncSandbox
from openai import AsyncOpenAI
from load_docs import SimpleVectorStore

# Load environment variables
load_dotenv()

# Define allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Initialize FastAPI app
app = FastAPI(title="Smart Code Tutor")

# Configure CORS for FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO server with CORS configuration
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=ALLOWED_ORIGINS,
    logger=True,
    engineio_logger=True,
    ping_timeout=60000,
    ping_interval=25000,
    max_http_buffer_size=1e8,
    async_handlers=True,
    namespaces=['/']  # Enable default namespace
)

# Create ASGIApp for Socket.IO and FastAPI
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
    socketio_path='socket.io'
)

# Store active sessions
active_sessions: Dict[str, AsyncSandbox] = {}

class CodeExecution(BaseModel):
    code: str
    language: str

class CodeExplanation(BaseModel):
    code: str
    output: str

# Initialize E2B session for code execution
async def get_or_create_session(sid: str, language: str) -> AsyncSandbox:
    if sid not in active_sessions:
        # Create a new sandbox instance with the correct template name
        if language == "python":
            active_sessions[sid] = await AsyncSandbox.create()  # No template needed, it uses Python by default
        else:
            active_sessions[sid] = await AsyncSandbox.create()  # For JavaScript
    return active_sessions[sid]

# Initialize OpenAI client
openai_client = AsyncOpenAI()

# Load vector store from disk
vector_store = SimpleVectorStore.load("vector_store")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

async def similarity_search(query, k=2):
    # Get query embedding
    response = await openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Calculate similarities
    similarities = [
        cosine_similarity(query_embedding, doc_embedding)
        for doc_embedding in vector_store.embeddings
    ]
    
    # Get top k most similar documents
    top_k_indices = np.argsort(similarities)[-k:][::-1]
    return [vector_store.documents[i] for i in top_k_indices]

@sio.event
async def connect(sid, environ, auth):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    if sid in active_sessions:
        await active_sessions[sid].close()
        del active_sessions[sid]

@sio.event
async def execute(sid, data):
    try:
        session = await get_or_create_session(sid, data["language"])
        
        # Execute code
        execution = await session.run_code(data["code"])
        
        # Stream output
        if execution.logs.stdout:
            for line in execution.logs.stdout:
                if line.strip():
                    await sio.emit('output', line, room=sid)
                
        if execution.logs.stderr:
            for line in execution.logs.stderr:
                if line.strip():
                    await sio.emit('error', line, room=sid)
            
    except Exception as e:
        print(f"Error executing code: {str(e)}")
        await sio.emit('error', str(e), room=sid)

@sio.event
async def explain(sid, data):
    try:
        # Search for relevant documentation
        docs = await similarity_search(data["code"], k=2)
        context = "\n".join(docs)
        
        # Generate explanation
        response = await openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert programming tutor. Explain the following code and its output in a clear, step-by-step manner."},
                {"role": "user", "content": f"Code:\n{data['code']}\n\nOutput:\n{data['output']}\n\nContext:\n{context}\n\nPlease explain this code and its output."}
            ]
        )
        
        await sio.emit('explanation', response.choices[0].message.content, room=sid)
        
    except Exception as e:
        print(f"Error generating explanation: {str(e)}")
        await sio.emit('error', str(e), room=sid)

@app.get("/")
async def root():
    return {"message": "Smart Code Tutor API"} 