from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import UploadFile, File
import uuid
from contextlib import asynccontextmanager
from servers.agent import fast
import asyncio
import logging
import uuid
import json
import time
from typing import Dict, Any, Optional
import re
import os


import time
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetryableError(Exception):
    pass

class NonRetryableError(Exception):
    pass

class AgentError(Exception):
    pass

RETRYABLE_ERROR_KEYWORDS = [
    'too many connections', 'server overloaded', 'temporary failure', 
    'try again', 'timeout', 'timed out', 'connection timeout',
    'read timeout', 'write timeout', 'operation timeout',
    
    'memory temporarily unavailable', 'disk space temporarily full',
    'resource temporarily unavailable', 'service temporarily unavailable',
    'temporarily unable', 'busy', 'locked', 'deadlock',
    
    'rate limit', 'throttled', 'quota exceeded', 'too many requests',
    'request limit', 'api limit',
    
    'server busy', 'service unavailable', 'maintenance mode',
    'overloaded', 'congestion', 'backpressure',
    
    'network unreachable', 'host temporarily unreachable',
    'dns temporarily failed', 'name resolution temporarily failed'
]

NON_RETRYABLE_ERROR_KEYWORDS = [
    'connection', 'network', 'socket', 'broken pipe', 
    'connection reset', 'host unreachable', 'connection refused',
    'no route to host', 'network is unreachable',
    
    'authentication failed', 'unauthorized', 'forbidden', 
    'access denied', 'permission denied', 'invalid credentials',
    'invalid token', 'expired token', 'invalid key',
    
    'column', 'table', 'syntax', 'type mismatch', 'invalid', 
    'does not exist', 'unknown', 'not found', 'missing',
    'duplicate key', 'constraint violation', 'foreign key',
    
    'validation error', 'invalid format', 'malformed',
    'bad request', 'invalid parameter', 'invalid input',
    'parse error', 'decode error', 'encoding error',
    
    'configuration error', 'config', 'misconfigured',
    'invalid configuration', 'missing configuration',
    
    'file not found', 'directory not found', 'path not found',
    'permission denied', 'disk full', 'no space left',
    
    'null pointer', 'index out of bounds', 'key error',
    'attribute error', 'type error', 'value error',
    'assertion error', 'not implemented',
    
    'version mismatch', 'incompatible', 'unsupported',
    'deprecated', 'not supported'
]

def is_retryable_error(error: Exception) -> bool:
    if isinstance(error, TimeoutError):
        return True
    
    if isinstance(error, (ConnectionError, ConnectionRefusedError)):
        return False
    
    if isinstance(error):
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in RETRYABLE_ERROR_KEYWORDS):
            return True
        
        if any(keyword in error_msg for keyword in NON_RETRYABLE_ERROR_KEYWORDS):
            return False
        
        return False
    
    return False

def retry_operation(func, retry_config, max_retries=None, base_delay=None, max_delay=None):
    max_retries = max_retries or retry_config.max_retries
    base_delay = base_delay or retry_config.base_delay
    max_delay = max_delay or retry_config.max_delay
    
    for attempt in range(max_retries + 1):  
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                if is_retryable_error(e):
                    logger.error(f"Operation failed after {max_retries} retries: {e}")
                    raise RetryableError(f"Max retries exceeded: {e}") from e
                else:
                    logger.error(f"Non-retryable error: {e}")
                    raise NonRetryableError(f"Operation failed: {e}") from e
            
            if not is_retryable_error(e):
                logger.error(f"Non-retryable error, failing fast: {e}")
                raise NonRetryableError(f"Operation failed: {e}") from e
            
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f} seconds...")
            time.sleep(delay)

class ChatManager:
    def __init__(self):
        self.agent = None
        self.agent_context = None
    
    async def start(self):
        try:
            if not self.agent_context:
                logger.info("Starting persistent agent context...")
                self.agent_context = fast.run()
                self.agent = await self.agent_context.__aenter__()
                logger.info("Agent context started successfully")
        except Exception as e:
            logger.error(f"Failed to start agent context: {e}")
            raise AgentError(f"Could not start agent context: {e}") from e
    
    async def stop(self):
        try:
            if self.agent_context:
                logger.info("Stopping agent context...")
                await self.agent_context.__aexit__(None, None, None)
                self.agent_context = None
                self.agent = None
                logger.info("Agent context stopped")
        except Exception as e:
            logger.error(f"Failed to stop agent context: {e}")
            raise AgentError(f"Could not stop agent context: {e}") from e
   
    
    async def chat(self, message: str) -> Dict[str, Any]:
        if not self.agent:
            await self.start()
            
        try:
            logger.info(f"Sending message to agent: {message}")
            result = await self.agent(message)
            logger.info("Received response from agent")
        
            return {
                "type": "normal_response",
                "result": str(result)
            }
        except Exception as e:
            logger.error(f"Error in chat method: {e}")
            raise AgentError(f"Failed to process chat message: {e}")

chat_manager = ChatManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await chat_manager.start()
        logger.info("FastAPI app started with persistent agent")
        yield
    except Exception as e:
        logger.error(f"Failed to start FastAPI app: {e}")
        raise 
    finally:
        await chat_manager.stop()
        logger.info("FastAPI app shutdown complete")

app = FastAPI(lifespan=lifespan)

@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, exc: AgentError):
    logger.error(f"Agent error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Agent Error", "detail": str(exc), "type": "agent_error"}
    )

@app.exception_handler(RetryableError)
async def retryable_error_handler(request: Request, exc: RetryableError):
    logger.error(f"Retryable error: {exc}")
    return JSONResponse(
        status_code=503,
        content={"error": "Service Temporarily Unavailable", "detail": str(exc), "type": "retryable_error"}
    )

@app.exception_handler(NonRetryableError)
async def non_retryable_error_handler(request: Request, exc: NonRetryableError):
    logger.error(f"Non-retryable error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Service Error", "detail": str(exc), "type": "non_retryable_error"}
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "detail": exc.errors(), "type": "validation_error"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error(f"Value error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid Input", "detail": str(exc), "type": "value_error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred", "type": "internal_error"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str
    image: Optional[str] = None
    
class Data_config_request(BaseModel):
    interceptedQueries: list[str]
    interceptedTables: list[str]

class HumanInputRequest(BaseModel):
    request_id: str
    user_input: str

class PromptResponse(BaseModel):
    text_result: Optional[str] = None
    image_result: Optional[str] = None
    status: str = "success"
    type: str = "normal_response"
    request_id: Optional[str] = None
    prompt: Optional[str] = None
    description: Optional[str] = None

def parse_agent_response(raw_response: str) -> dict:
    text_result = None
    image_urls = []
    print(raw_response)
    
    text_match = re.search(r'%%RESPONSE\s*(.*?)\s*%%', raw_response, re.DOTALL)
    if text_match:
        text_result = text_match.group(1).strip()
    
    image_match = re.search(r'%%RESPONSE_IMAGE\s*(.*?)\s*%%', raw_response, re.DOTALL)
    if image_match:
        image_section = image_match.group(1)
        url_matches = re.findall(r'##IMAGE_URL:\s*(.*?)\s*##', image_section)
        image_urls = [url.strip() for url in url_matches]
    
    return {
        "text_result": text_result,
        "image_urls": image_urls
    }

@app.post("/upload_image")
async def upload_image(image: UploadFile = File(...)):
    image_id = str(uuid.uuid4())
    image_path = f"./temp_images/{image_id}.jpg"
    
    os.makedirs("./temp_images", exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(await image.read())
    
    return {"image_path": image_path}

@app.post("/agent", response_model=PromptResponse)
async def search_logs(prompt_request: PromptRequest):
    try:
        user_text_query = prompt_request.prompt
        user_image_query = prompt_request.image 
        
        
        if not user_text_query.strip() and not user_image_query:
            raise HTTPException(status_code=400, detail="Either text prompt or image must be provided")
        
        message_parts = []
        
        if user_text_query.strip():
            message_parts.append(user_text_query)
        
        if user_image_query:
            message_parts.append(f"[IMAGE_UPLOADED: {user_image_query}]")
            if not user_text_query.strip():
                message_parts.append("Find products similar to this image.")
        
        combined_message = " ".join(message_parts)
        
        logger.info(f"Processing query with text: {bool(user_text_query.strip())}, image: {bool(user_image_query)}")
        
        result = await chat_manager.chat(combined_message)
        raw_response = result["result"]
        
        logger.info(f"Raw agent response: {raw_response[:200]}...")
        
        parsed = parse_agent_response(raw_response)
        
        logger.info(f"Parsed response - Text length: {len(parsed['text_result']) if parsed['text_result'] else 0}, Images: {len(parsed['image_urls'])}")
        
        return PromptResponse(
            text_result=parsed["text_result"],
            image_result=json.dumps(parsed["image_urls"]) if parsed["image_urls"] else None,
            status="success",
            type="normal_response"
        )
        
    except HTTPException:
        raise
    except AgentError as e:
        logger.error(f"Agent error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")



@app.post("/reset_conversation")
async def reset_conversation():
    try:
        logger.info("Resetting conversation...")
        
        await chat_manager.stop()
        logger.info("Agent stopped")
        
        await chat_manager.start()
        logger.info("Agent restarted")
        
        
        return {
            "status": "success", 
            "message": "Conversation history and configuration reset",
        }
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset conversation: {str(e)}")



@app.get("/health")
async def health_check():
    try:
        if chat_manager.agent:
            return {"status": "healthy", "agent_status": "running"}
        else:
            return {"status": "healthy", "agent_status": "not_initialized"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
    
@app.get("/agent_status")
async def agent_status():
    try:
        return {
            "agent_initialized": chat_manager.agent is not None,
            "context_active": chat_manager.agent_context is not None,
            "status": "ready" if chat_manager.agent else "not_ready"
        }
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent status")

class SimpleConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        return connection_id

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

    async def send_to_frontend(self, message: dict):
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(connection_id)
        
        for connection_id in disconnected:
            self.disconnect(connection_id)
            
websocket_manager = SimpleConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = await websocket_manager.connect(websocket)
    logger.info(f"WebSocket connected: {connection_id}")
    
    try:
        while True:
            await asyncio.sleep(10)  
            
    except WebSocketDisconnect:
        logger.info(f"Client {connection_id} disconnected")
    finally:
        websocket_manager.disconnect(connection_id)

async def send_to_frontend(message_content: str):
    logger.info(f"sending tool calls to frontend")
    message = {
        "type": "tool",
        "content": message_content,
        "timestamp": time.time()
    }
    await websocket_manager.send_to_frontend(message)
    
class WebSocketMessage(BaseModel):
    message: str
    
@app.post("/internal/websocket_send")
async def internal_websocket_send(data: WebSocketMessage):
    try:
        logger.info(f"Received internal WebSocket message: {data.message}")
        message = {
            "type": "tool",
            "content": data.message,
            "timestamp": time.time()
        }
        await websocket_manager.send_to_frontend(message)
        return {"status": "sent", "connections": len(websocket_manager.active_connections)}
    except Exception as e:
        logger.error(f"Error sending internal WebSocket message: {e}")
        return {"status": "error", "error": str(e)}
            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)