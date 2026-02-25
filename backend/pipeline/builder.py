"""
builder.py — Pipecat Pipeline Builder
=======================================
This is the HEART of the Vaani voice bot.

It assembles the full AI pipeline for one call session:

    User speaks
        ↓
    [transport.input()]     ← Audio comes in from browser via WebRTC
        ↓
    [SileroVADAnalyzer]     ← Detects when user stops speaking (in TransportParams)
        ↓
    [DeepgramSTTService]    ← Converts speech to text
        ↓
    [LLMContextAggregator]  ← Collects user text + conversation history
        ↓
    [OpenAILLMService]      ← Groq/Llama3 generates AI response
        |                       If a tool is needed:
        ├─ search_web()       ← Tavily Search API
        ├─ crawl_webpage()    ← Tavily Crawl API
        ├─ extract_webpage()  ← Tavily Extract API
        ├─ get_weather()      ← Open-Meteo API (free)
        ├─ calculate()        ← Python AST (safe eval)
        └─ get_current_time() ← Python datetime
        ↓
    [CartesiaTTSService]    ← Converts AI text to speech audio
        ↓
    [transport.output()]    ← Audio streams back to browser via WebRTC
        ↓
    [LLMContextAggregator]  ← Saves AI response to conversation history

Why one pipeline per session?
- Each user gets their own isolated pipeline
- Conversation history is separate for each user
- If one pipeline crashes, others are unaffected
"""

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
# SileroVADAnalyzer is configured in transport/webrtc.py via TransportParams.vad_analyzer
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.transports.base_transport import BaseTransport

from services.llm import create_llm_service
from services.stt import create_stt_service
from services.tts import create_tts_service
from pipeline.prompts import get_initial_messages
from tools import get_all_tool_schemas, register_all_tools
from core.logger import logger


def build_pipeline(transport: BaseTransport, session_id: str) -> PipelineTask:
    """
    Build and return a complete Pipecat pipeline for one call session.

    This function:
    1. Creates all AI services (STT, LLM, TTS)
    2. Sets up conversation context with the system prompt
    3. Assembles the pipeline in the correct order
    4. Returns a PipelineTask ready to run

    Args:
        transport: The SmallWebRTC transport for this session
                   (handles audio in/out with the browser)
        session_id: Unique ID for this session (used for logging)

    Returns:
        PipelineTask: Ready-to-run pipeline task

    Usage:
        task = build_pipeline(transport, session_id="sess-123")
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)
    """
    logger.info("Building pipeline | session={}", session_id)
    print(f"--- Building Pipeline for Session {session_id} ---")
    print(f"--- Tools Enabled: SEARCH, WEATHER, TIME, CALC, CRAWL ---")

    # ── Step 1: Create AI Services ─────────────────────────────────────────────
    # Each service is created fresh for this session
    stt = create_stt_service()                                  # Deepgram: voice → text
    llm = create_llm_service(tools=get_all_tool_schemas())      # Groq: text → AI response (with tools)
    tts = create_tts_service()                                  # Cartesia: AI response → voice

    # Register all tool handlers with the LLM service
    # When Groq decides to call a tool, Pipecat routes the call to these handlers
    register_all_tools(llm)
    logger.info("Tools registered | session={}", session_id)

    # ── Step 2: Set Up Conversation Context ────────────────────────────────────
    # The context holds the conversation history (all messages so far)
    # It starts with just the system prompt
    initial_messages = get_initial_messages()
    context = OpenAILLMContext(initial_messages)

    # The context aggregator pair manages the conversation flow:
    # - user_aggregator: collects what the user said + adds to history
    # - assistant_aggregator: collects what the AI said + adds to history
    context_aggregator = llm.create_context_aggregator(context)

    # ── Step 3: Assemble the Pipeline ─────────────────────────────────────────
    # Order matters! Each component passes its output to the next.
    pipeline = Pipeline([
        # 1. Receive audio from the browser
        #    VAD (SileroVADAnalyzer) is configured in TransportParams — not here
        transport.input(),

        # 2. Convert user's speech to text (Deepgram)
        #    Deepgram STT is triggered after VAD detects end-of-speech
        stt,

        # 3. Add user's text to conversation history
        context_aggregator.user(),

        # 4. Send conversation to Groq LLM → get AI response
        llm,

        # 5. Convert AI's text response to speech (Cartesia)
        tts,

        # 6. Send audio back to the browser
        transport.output(),

        # 7. Add AI's response to conversation history
        context_aggregator.assistant(),
    ])

    # ── Step 4: Create the Pipeline Task ──────────────────────────────────────
    # PipelineTask wraps the pipeline and manages its execution
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            # allow_interruptions: user can interrupt the AI mid-sentence
            # This makes conversation feel natural
            allow_interruptions=True,

            # Enable metrics logging (useful for debugging)
            enable_metrics=True,
            enable_usage_metrics=True,
        )
    )

    logger.info("Pipeline built successfully | session={}", session_id)
    return task
