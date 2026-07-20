"""
WebSocket Chat Streaming endpoint.
Provides real-time token streaming for AI chat interactions.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from app.core.config import settings

router = APIRouter()


async def authenticate_websocket(token: str) -> dict | None:
    """Authenticate WebSocket connection via JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": user_id, "email": payload.get("email", "")}
    except JWTError:
        return None


async def run_security_check(message: str) -> dict:
    """
    Run security analysis on the incoming message.
    Returns security assessment before allowing the message through.
    """
    # Basic security patterns to detect
    injection_patterns = [
        "ignore previous instructions",
        "ignore all prior",
        "disregard your programming",
        "system prompt",
        "you are now",
        "pretend you are",
        "act as if you have no restrictions",
    ]

    message_lower = message.lower()
    detected_threats = []

    for pattern in injection_patterns:
        if pattern in message_lower:
            detected_threats.append(pattern)

    if detected_threats:
        return {
            "safe": False,
            "score": 0.2,
            "threats": detected_threats,
            "action": "blocked",
        }

    return {
        "safe": True,
        "score": 1.0,
        "threats": [],
        "action": "allowed",
    }


async def simulate_token_stream(message: str, model: str, use_rag: bool):
    """
    Simulate streaming tokens from an AI model.
    In production, this would connect to the actual AI gateway.
    """
    # Simulated response based on input
    response_text = (
        f"I received your message and I'm processing it using the {model} model. "
        f"{'RAG context has been applied. ' if use_rag else ''}"
        f"This is a streaming response demonstrating token-by-token delivery. "
        f"In production, this connects to the actual AI provider gateway with "
        f"circuit breaker protection and security monitoring enabled."
    )

    # Yield tokens (word by word to simulate streaming)
    words = response_text.split(" ")
    for i, word in enumerate(words):
        token = word + (" " if i < len(words) - 1 else "")
        yield token
        # Simulate variable latency between tokens
        await asyncio.sleep(0.05)


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = ""):
    """
    WebSocket endpoint for real-time chat streaming.

    Connect with: ws://host/ws/chat?token=<jwt_token>

    Send messages as JSON:
        {"message": "Hello", "model": "gpt-4", "use_rag": false}

    Receive structured JSON messages:
        {"type": "token", "data": "Hello"}
        {"type": "security", "data": {"safe": true, "score": 1.0}}
        {"type": "done", "data": {"tokens_used": 42, "latency_ms": 150}}
        {"type": "error", "data": {"message": "Error description"}}
    """
    # Authenticate the connection
    user = await authenticate_websocket(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    try:
        while True:
            # Receive message from client
            raw_data = await websocket.receive_text()

            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"},
                })
                continue

            message = data.get("message", "").strip()
            model = data.get("model", "gpt-4")
            use_rag = data.get("use_rag", False)

            if not message:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Message cannot be empty"},
                })
                continue

            # Run security check before processing
            security_result = await run_security_check(message)
            await websocket.send_json({
                "type": "security",
                "data": security_result,
            })

            # If message is blocked by security, don't proceed
            if not security_result["safe"]:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "message": "Message blocked by security engine",
                        "threats": security_result["threats"],
                    },
                })
                continue

            # Stream tokens back to client
            start_time = datetime.now(timezone.utc)
            token_count = 0

            async for token_text in simulate_token_stream(message, model, use_rag):
                await websocket.send_json({
                    "type": "token",
                    "data": token_text,
                })
                token_count += 1

            # Send completion message
            elapsed_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            await websocket.send_json({
                "type": "done",
                "data": {
                    "message_id": str(uuid.uuid4()),
                    "tokens_used": token_count,
                    "latency_ms": round(elapsed_ms, 2),
                    "model": model,
                    "security_score": security_result["score"],
                },
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Internal error: {str(e)}"},
            })
        except Exception:
            pass
