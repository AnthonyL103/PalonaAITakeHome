import httpx
import logging

logger = logging.getLogger(__name__)

async def send_to_frontend(message_content: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/internal/websocket_send",
                json={"message": message_content},
                timeout=5.0
            )
            if response.status_code == 200:
                logger.info(f"Sent WebSocket message via HTTP: {message_content}")
            else:
                logger.error(f"HTTP callback failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send WebSocket message via HTTP: {e}")