"""
Tests for TelethonBot class.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from mobileinfoga import TelethonBot


@pytest.fixture
def mock_telegram_client():
    return AsyncMock()


class TestTelethonBot:
    """Test TelethonBot class."""

    def test_authenticate_with_retry(self, mock_telegram_client):
        """Test authentication with retry logic."""
        bot = TelethonBot()
        bot.client = mock_telegram_client

        # Simulate a failed authentication
        mock_telegram_client.is_user_authorized.return_value = False

        # Mock the send_code_request and sign_in methods
        with patch.object(bot.client, 'send_code_request') as mock_send_code,
             patch.object(bot.client, 'sign_in') as mock_sign_in:

            # Run the async function
            async def run_auth():
                await bot._authenticate_with_retry()

            asyncio.run(run_auth())

            # Verify that authentication was attempted
            assert mock_send_code.called
            assert mock_sign_in.called

    def test_send_message_with_retry(self, mock_telegram_client):
        """Test message sending with retry logic."""
        bot = TelethonBot()
        bot.client = mock_telegram_client

        # Simulate a failed send_message
        mock_telegram_client.send_message.side_effect = Exception("Failed to send message")

        # Mock the user entity
        mock_user_entity = AsyncMock()
        mock_user_entity.id = 123456
        mock_user_entity.access_hash = 789012
        bot.user_entity = mock_user_entity

        # Mock InputPeerUser
        mock_input_peer = AsyncMock()
        bot.client.send_message = AsyncMock(return_value=mock_input_peer)

        # Run the async function
        async def run_send():
            await bot._send_message("Test message")

        asyncio.run(run_send())

        # Verify that the message was sent
        assert mock_telegram_client.send_message.called