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

        # ── Step 3: Tool Call Loop (Max 3 turns to prevent infinite loops) ─────
        tools = get_all_tool_schemas()
        ai_text = ""
        use_tools = True  # Can be disabled on retry if Groq fails with tool format

        for turn in range(3):
            logger.info("Calling Groq (turn {}) | session={} tools={}", turn + 1, session_id, use_tools)

            try:
                call_params = {
                    "model": settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.6,
                }
                # Only include tools if enabled (disabled on retry after tool_use_failed)
                if use_tools:
                    call_params["tools"] = tools
                    call_params["tool_choice"] = "auto"

                completion = await _groq_client.chat.completions.create(**call_params)

            except BadRequestError as e:
                # Groq returns 400 "tool_use_failed" when Llama generates
                # malformed tool calls (XML format instead of JSON).
                # Retry WITHOUT tools to get a plain text answer.
                if "tool_use_failed" in str(e):
                    logger.warning("Groq tool_use_failed, retrying without tools | session={}", session_id)
                    use_tools = False
                    continue
                raise

            response_msg = completion.choices[0].message
            tool_calls = response_msg.tool_calls

            # If no tool calls, we have the final answer
            if not tool_calls:
                ai_text = (response_msg.content or "").strip()
                break

            # If tool calls, execute them
            messages.append(response_msg)  # Add assistant's "I want to call X" message
            logger.info("Tool calls detected: {} | session={}", len(tool_calls), session_id)

            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                logger.info("Executing tool: {} | args={}", fn_name, fn_args)

                handler = TOOL_HANDLERS.get(fn_name)
                result_content = ""

                if handler:
                    # Execute locally using our existing handler logic
                    mock_params = MockFunctionCallParams(fn_name, fn_args)
                    await handler(mock_params)
                    result_content = mock_params.result or "No result returned"
                else:
                    result_content = f"Error: Tool '{fn_name}' not found."

                # Append tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": str(result_content)
                })
        else:
            # If loop finishes without break, it means we hit max turns
            ai_text = "I'm having trouble retrieving that information right now. Please try again."

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
