"""Telegram Ingestion Service - A minimal webhook receiver for Telegram channels."""

import json
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app import __version__
from app.config import get_settings

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Models for Telegram Updates
# =============================================================================


class Chat(BaseModel):
    """Telegram chat object (minimal fields we need)."""
    id: int
    title: str | None = None
    type: str | None = None


class Message(BaseModel):
    """Telegram message object (minimal fields we need)."""
    message_id: int
    chat: Chat
    date: int
    text: str | None = None
    caption: str | None = None
    # We keep the raw data for anything else we might need later


class Update(BaseModel):
    """Telegram update object."""
    update_id: int
    channel_post: Message | None = None
    # We only care about channel_post for v0


# =============================================================================
# Normalized Message Format
# =============================================================================


class NormalizedMessage(BaseModel):
    """Our internal message format - clean and consistent."""
    source: str = "telegram"
    chat_id: str
    chat_title: str | None
    message_id: int
    timestamp: int
    text: str | None
    raw: dict[str, Any]


def normalize_update(update: Update, raw_payload: dict) -> NormalizedMessage | None:
    """Transform a Telegram update into our normalized format.
    
    Returns None if the update doesn't contain a channel_post.
    """
    if not update.channel_post:
        return None
    
    msg = update.channel_post
    
    return NormalizedMessage(
        source="telegram",
        chat_id=str(msg.chat.id),
        chat_title=msg.chat.title,
        message_id=msg.message_id,
        timestamp=msg.date,
        text=msg.text or msg.caption,  # text for regular messages, caption for media
        raw=raw_payload,
    )


# =============================================================================
# Output Handlers
# =============================================================================


def handle_stdout(message: NormalizedMessage) -> None:
    """Log the message to stdout."""
    timestamp = datetime.fromtimestamp(message.timestamp).isoformat()
    logger.info(
        "📨 New message | chat=%s | id=%s | time=%s | text=%s",
        message.chat_title or message.chat_id,
        message.message_id,
        timestamp,
        message.text[:100] if message.text else "(no text)",
    )


def handle_noop(message: NormalizedMessage) -> None:
    """Do nothing - useful for testing."""
    pass


# Handler dispatch
HANDLERS = {
    "stdout": handle_stdout,
    "noop": handle_noop,
}


# =============================================================================
# FastAPI Application
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Starting Telegram Ingestion Service v%s", __version__)
    logger.info("Log level: %s", settings.log_level)
    logger.info("Output handler: %s", settings.output_handler)
    logger.info("Listening on %s:%s", settings.host, settings.port)
    
    if settings.webhook_url:
        logger.info("Webhook URL: %s", settings.webhook_url)
    else:
        logger.warning("WEBHOOK_URL not set - remember to register your webhook")
    
    yield
    
    logger.info("Shutting down Telegram Ingestion Service")


app = FastAPI(
    title="Telegram Ingestion Service",
    description="A minimal service that listens to messages from a private Telegram channel via webhooks",
    version=__version__,
    lifespan=lifespan,
)


# =============================================================================
# Endpoints
# =============================================================================


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": __version__,
            "service": "telegram-ingestion",
        }
    )


@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint with service info."""
    return JSONResponse(
        content={
            "service": "telegram-ingestion",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }
    )


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> JSONResponse:
    """Receive webhook updates from Telegram.
    
    This endpoint:
    1. Validates the secret token
    2. Parses the Telegram update
    3. Normalizes the message
    4. Dispatches to the configured handler
    5. Returns 200 quickly (Telegram expects fast responses)
    """
    # Validate secret token
    if x_telegram_bot_api_secret_token != settings.tg_webhook_secret:
        logger.warning("Webhook rejected: invalid secret token")
        raise HTTPException(status_code=401, detail="Invalid secret token")
    
    # Parse the raw payload
    try:
        raw_payload = await request.json()
    except json.JSONDecodeError:
        logger.warning("Webhook rejected: invalid JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    logger.debug("Received update: %s", raw_payload)
    
    # Parse into our Telegram model
    try:
        update = Update(**raw_payload)
    except Exception as e:
        logger.warning("Webhook rejected: failed to parse update - %s", e)
        raise HTTPException(status_code=400, detail="Invalid update format")
    
    # Normalize the message
    normalized = normalize_update(update, raw_payload)
    
    if normalized is None:
        # Not a channel_post, ignore it
        logger.debug("Ignoring update (not a channel_post): %s", update.update_id)
        return JSONResponse(content={"status": "ignored"})
    
    # Dispatch to handler
    handler = HANDLERS.get(settings.output_handler, handle_stdout)
    try:
        handler(normalized)
    except Exception as e:
        logger.error("Handler error: %s", e)
        # Still return 200 - we don't want Telegram to retry
    
    return JSONResponse(content={"status": "ok"})


# =============================================================================
# Entrypoint
# =============================================================================


def run():
    """Run the application with uvicorn."""
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    run()
