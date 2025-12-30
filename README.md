# Telegram Ingestion

A minimal, self-hostable service that listens to messages from a **private Telegram channel** via webhooks and logs them to stdout.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- A Telegram bot (create via [@BotFather](https://t.me/botfather))
- A private Telegram channel with your bot as admin

### Setup

```bash
# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # From @BotFather
TG_WEBHOOK_SECRET=your_secret_here                       # Generate: openssl rand -hex 32
WEBHOOK_URL=https://your-ngrok-url.ngrok-free.app/telegram/webhook
```

## Development

### Option A: Test Locally with curl (no Telegram needed)

Start the server:

```bash
make run
# or: uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Simulate a Telegram webhook:

```bash
# Test with valid secret (should return 200 and log the message)
curl -X POST http://localhost:8000/telegram/webhook \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: YOUR_TG_WEBHOOK_SECRET" \
  -d '{
    "update_id": 123,
    "channel_post": {
      "message_id": 1,
      "chat": {"id": -100123, "title": "Test Channel", "type": "channel"},
      "date": 1735500000,
      "text": "Hello from curl!"
    }
  }'

# Test with invalid secret (should return 401)
curl -X POST http://localhost:8000/telegram/webhook \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: wrong_secret" \
  -d '{"update_id": 1}'
```

### Option B: Test with Real Telegram

```bash
# Terminal 1: Start ngrok tunnel
ngrok http 8000
# Copy the https URL (e.g., https://abc123.ngrok-free.app)

# Terminal 2: Update WEBHOOK_URL in .env, then:
make webhook-set   # Register webhook with Telegram
make run           # Start the server

# Now post a message in your Telegram channel - it will appear in the logs!
```

## Available Commands

```bash
make run            # Start dev server with reload
make webhook-set    # Register webhook with Telegram
make webhook-info   # Check current webhook status
make webhook-delete # Remove webhook from Telegram
make lint           # Run linter
make clean          # Clean cache files
```

Or use uv directly:

```bash
uv run uvicorn app.main:app --reload
uv run python scripts/set_webhook.py set
uv run python scripts/set_webhook.py info
```

## Project Structure

```
telegram-bot/
├── app/
│   ├── __init__.py    # Package version
│   ├── config.py      # Environment config
│   └── main.py        # FastAPI app, webhook, models, handlers
├── scripts/
│   └── set_webhook.py # Telegram webhook management
├── .env.example       # Template for environment variables
├── pyproject.toml     # Dependencies (uv/pip)
└── Makefile           # Convenience commands
```

## How It Works

```
Telegram Channel
       │
       │ (Webhook POST)
       ▼
┌─────────────────────┐
│  POST /telegram/    │
│      webhook        │
│  (validates secret) │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  Normalize message  │
│  to clean format    │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  Output to stdout   │
│  (or other handler) │
└─────────────────────┘
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `TG_WEBHOOK_SECRET` | Yes | Secret for webhook validation |
| `WEBHOOK_URL` | Yes* | Public HTTPS URL (*for Telegram registration) |
| `LOG_LEVEL` | No | `debug`, `info`, `warning`, `error` (default: `info`) |
| `OUTPUT_HANDLER` | No | `stdout` or `noop` (default: `stdout`) |
