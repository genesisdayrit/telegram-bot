"""Tests for the Telegram webhook endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def valid_secret():
    """Get the webhook secret from settings."""
    return get_settings().tg_webhook_secret


@pytest.fixture
def sample_channel_post():
    """Sample Telegram channel_post update."""
    return {
        "update_id": 123456789,
        "channel_post": {
            "message_id": 42,
            "chat": {
                "id": -1001234567890,
                "title": "Test Channel",
                "type": "channel"
            },
            "date": 1735500000,
            "text": "Hello from the test!"
        }
    }


class TestWebhookSecurity:
    """Test webhook authentication."""

    def test_missing_secret_returns_401(self, client):
        """Request without secret token should be rejected."""
        response = client.post(
            "/telegram/webhook",
            json={"update_id": 1}
        )
        assert response.status_code == 401
        assert "Invalid secret token" in response.json()["detail"]

    def test_invalid_secret_returns_401(self, client):
        """Request with wrong secret should be rejected."""
        response = client.post(
            "/telegram/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"}
        )
        assert response.status_code == 401

    def test_valid_secret_returns_200(self, client, valid_secret, sample_channel_post):
        """Request with correct secret should be accepted."""
        response = client.post(
            "/telegram/webhook",
            json=sample_channel_post,
            headers={"X-Telegram-Bot-Api-Secret-Token": valid_secret}
        )
        assert response.status_code == 200


class TestWebhookProcessing:
    """Test webhook message processing."""

    def test_channel_post_processed(self, client, valid_secret, sample_channel_post):
        """Channel posts should be processed and return 'ok'."""
        response = client.post(
            "/telegram/webhook",
            json=sample_channel_post,
            headers={"X-Telegram-Bot-Api-Secret-Token": valid_secret}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_non_channel_post_ignored(self, client, valid_secret):
        """Updates without channel_post should be ignored."""
        response = client.post(
            "/telegram/webhook",
            json={"update_id": 999},  # No channel_post field
            headers={"X-Telegram-Bot-Api-Secret-Token": valid_secret}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    def test_caption_used_for_media(self, client, valid_secret):
        """Caption should be used when text is not present (media messages)."""
        media_post = {
            "update_id": 123,
            "channel_post": {
                "message_id": 43,
                "chat": {"id": -100123, "title": "Test", "type": "channel"},
                "date": 1735500000,
                "caption": "Photo caption here"
                # Note: no "text" field, just "caption"
            }
        }
        response = client.post(
            "/telegram/webhook",
            json=media_post,
            headers={"X-Telegram-Bot-Api-Secret-Token": valid_secret}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestWebhookValidation:
    """Test request validation."""

    def test_invalid_json_returns_400(self, client, valid_secret):
        """Malformed JSON should return 400."""
        response = client.post(
            "/telegram/webhook",
            content="not valid json",
            headers={
                "X-Telegram-Bot-Api-Secret-Token": valid_secret,
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 400


class TestHealthCheck:
    """Test health and root endpoints."""

    def test_health_endpoint(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Root should return service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "telegram-ingestion"

