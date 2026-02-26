"""
chat.py — Chat History Routes
================================
REST API endpoints for accessing and managing chat history.

These endpoints let the frontend:
- Fetch past messages for a session (to display in the UI)
- Send text messages (for text chat mode, not voice)

Routes:
    GET  /chat/{session_id}        → Get all messages for a session
    POST /chat/{session_id}        → Send a text message + get AI reply
    DELETE /chat/{session_id}      → Clear all messages for a session
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from openai import AsyncOpenAI, BadRequestError

from db.repositories.message_repo import (
    get_messages,
    save_message,
    delete_session_messages,
    get_message_count,
)
from db.models import Message, MessageRole
from core.config import settings
from core.logger import logger
from pipeline.prompts import get_system_prompt

router = APIRouter(prefix="/chat", tags=["Chat"])

# Groq client (OpenAI-compatible)
_groq_client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Groq's dedicated tool-use model — llama-3.3-70b-versatile often generates
# tool calls in XML format which Groq rejects with "tool_use_failed".
# llama-3.1-8b-instant handles function calling format correctly.
TOOL_USE_MODEL = "llama-3.1-8b-instant"


# ── Request/Response Models ────────────────────────────────────────────────────

class TextMessageRequest(BaseModel):
    """Request body for sending a text message."""
    content: str    # The message text


class ChatHistoryResponse(BaseModel):
    """Response containing chat history for a session."""
    session_id: str
    messages: List[Message]
    total: int


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, limit: int = 50):
    """
    Get all messages for a session.

    Args:
        session_id: The session to fetch messages for
        limit: Max number of messages to return (default: 50)

    Returns:
        ChatHistoryResponse with list of messages

    Example:
        GET /chat/sess-abc123
        → { "session_id": "sess-abc123", "messages": [...], "total": 12 }
    """
    try:
        messages = await get_messages(session_id, limit=limit)
        total = await get_message_count(session_id)

        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            total=total
        )
    except Exception as e:
        logger.error("Failed to get chat history | session={} error={}", session_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")


import json
from tools import get_all_tool_schemas, TOOL_HANDLERS
from pipecat.processors.frameworks.rtvi import FunctionCallParams

# ── Mock Params for Tool Handlers ──────────────────────────────────────────────
class MockFunctionCallParams:
    """
    Mocks Pipecat's FunctionCallParams so we can reuse the same tool handlers
    in the text chat route without needing the full Pipecat pipeline.
    """
    def __init__(self, name, arguments):
        self.function_name = name
        self.arguments = arguments
        self.result = None

    async def result_callback(self, result: str):
        self.result = result


@router.post("/{session_id}", response_model=Message)
async def send_text_message(session_id: str, request: TextMessageRequest):
    """
    Send a text message and get an AI reply (with tool support).
    """
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Message content cannot be empty")

        # ── Step 1: Save user message ──────────────────────────────────────────
        await save_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=request.content.strip()
        )
        logger.info("Text message saved | session={}", session_id)

        # ── Step 2: Fetch recent history & Prepare Messages ────────────────────
        history = await get_messages(session_id, limit=20)
        messages = [{"role": "system", "content": get_system_prompt()}]
        for msg in history:
            role = msg.role if isinstance(msg.role, str) else msg.role.value
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": msg.content})

        # ── Step 3: Tool Call Loop ──────────────────────────────────────────────
        # Strategy: Use small model (8b) for tool calling (correct JSON format),
        # then use big model (70b) WITHOUT tools for the final response.
        tools = get_all_tool_schemas()
        ai_text = ""
        tool_was_used = False

        # Turn 1: Ask the small model if it needs any tools
        logger.info("Calling Groq (turn 1 - tool decision) | session={}", session_id)

        try:
            completion = await _groq_client.chat.completions.create(
                model=TOOL_USE_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=1024,
                temperature=0.6,
            )
        except BadRequestError as e:
            if "tool_use_failed" in str(e):
                logger.warning("Groq tool_use_failed, skipping tools | session={}", session_id)
                # Fall through to final response without tools
                completion = await _groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.6,
                )
                ai_text = (completion.choices[0].message.content or "").strip()
                tool_was_used = False
            else:
                raise
        else:
            response_msg = completion.choices[0].message
            tool_calls = response_msg.tool_calls

            if not tool_calls:
                # No tools needed — use the response directly
                ai_text = (response_msg.content or "").strip()
            else:
                # Execute tool calls
                tool_was_used = True
                messages.append(response_msg)
                logger.info("Tool calls detected: {} | session={}", len(tool_calls), session_id)

                for tool_call in tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)

                    logger.info("Executing tool: {} | args={}", fn_name, fn_args)

                    handler = TOOL_HANDLERS.get(fn_name)
                    result_content = ""

                    if handler:
                        mock_params = MockFunctionCallParams(fn_name, fn_args)
                        await handler(mock_params)
                        result_content = mock_params.result or "No result returned"
                    else:
                        result_content = f"Error: Tool '{fn_name}' not found."

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": str(result_content)
                    })

        # Turn 2: If tools were used, send results to the BIG model for a proper answer
        if tool_was_used and not ai_text:
            logger.info("Calling Groq (turn 2 - final answer with 70b) | session={}", session_id)
            final_completion = await _groq_client.chat.completions.create(
                model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1024,
                temperature=0.6,
                # NO tools here — just summarize the tool results!
            )
            ai_text = (final_completion.choices[0].message.content or "").strip()

        # ── Step 4: Save AI reply ─────────────────────────────────────────────
        if not ai_text:
            ai_text = "I couldn't generate a response."

        ai_message = await save_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_text
        )
        logger.info("AI reply saved | session={}", session_id)

        # ── Step 5: Return AI reply ───────────────────────────────────────────
        return ai_message

    except Exception as e:
        logger.error("Failed to process chat message | session={} error={}", session_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.delete("/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Delete all messages for a session.

    Use this to clear chat history when a session ends
    or when the user wants to start fresh.

    Args:
        session_id: The session to clear

    Returns:
        dict with number of messages deleted
    """
    try:
        deleted_count = await delete_session_messages(session_id)
        return {
            "session_id": session_id,
            "deleted": deleted_count,
            "message": f"Deleted {deleted_count} messages"
        }
    except Exception as e:
        logger.error("Failed to clear chat | session={} error={}", session_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to clear chat history")
