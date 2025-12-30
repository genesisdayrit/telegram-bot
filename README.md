# Telegram Ingestion

A minimal, self-hostable service that listens to messages from a **private Telegram channel** via webhooks and forwards them to pluggable downstream handlers.

## Why?

Telegram is a great "capture tool" for notes, ideas, tasks, voice messages, and files. This service provides a **transparent, hackable base** to build your own personal inbox that can power knowledge bases, automation pipelines, or note systems.

## Features

- ✅ Receives messages from a private Telegram channel
- ✅ Uses webhooks (not polling) for real-time updates
- ✅ Validates webhook authenticity via secret token
- ✅ Normalizes Telegram's complex message format
- ✅ Pluggable output handlers (stdout, noop, extensible)
- ✅ Easy to self-host and reason about

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- A Telegram bot (create one via [@BotFather](https://t.me/botfather))
- A private Telegram channel with your bot as admin
- HTTPS endpoint (use [ngrok](https://ngrok.com) for local dev)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/telegram-ingestion.git
cd telegram-ingestion

# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your bot token and webhook secret
```

### Configuration

Edit `.env` with your credentials:

```bash
BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TG_WEBHOOK_SECRET=your_secret_here
WEBHOOK_URL=https://your-domain.com/telegram/webhook
```

### Running Locally

```bash
# Terminal 1: Start ngrok tunnel
ngrok http 8000

# Terminal 2: Update WEBHOOK_URL in .env with ngrok URL, then:
make webhook-set  # Register webhook with Telegram
make run          # Start the server
```

### Verify It Works

1. Post a message to your private channel
2. Check your terminal for the logged message

## Available Commands

```bash
make install       # Install production dependencies
make dev           # Install all dependencies including dev
make run           # Run the development server
make lint          # Run linter
make test          # Run tests
make webhook-set   # Register webhook with Telegram
make webhook-info  # Get current webhook info
make webhook-delete # Delete webhook
make clean         # Clean cache files
```

## Project Structure

```
telegram-ingestion/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration management
│   ├── webhook.py       # Webhook endpoint
│   ├── models.py        # Pydantic models
│   ├── normalize.py     # Message normalizer
│   └── handlers/        # Output handlers
│       ├── __init__.py
│       ├── stdout.py
│       └── noop.py
├── scripts/
│   └── set_webhook.py   # Webhook management script
├── docs/
│   └── RFC-0001-telegram-ingestion.md
├── tests/
├── .env.example
├── pyproject.toml
├── Makefile
└── README.md
```

## How It Works

```
Telegram Channel
       │
       │ (Webhook POST)
       ▼
┌─────────────────────┐
│   FastAPI Webhook   │
│  /telegram/webhook  │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  Update Normalizer  │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  Output Handler(s)  │
│  (stdout, HTTP,     │
│   noop, etc.)       │
└─────────────────────┘
```

## Roadmap

See [RFC-0001](docs/RFC-0001-telegram-ingestion.md) for the full design document.

Future RFCs planned:
- RFC-0002: Action buttons and approvals
- RFC-0003: Media ingestion (voice, files)
- RFC-0004: Structured commands and tagging
- RFC-0005: Storage backends
- RFC-0006: Obsidian integration

## License

MIT License - see [LICENSE](LICENSE) for details.
