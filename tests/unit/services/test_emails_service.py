"""Unit tests for EmailService methods (no SMTP, just message assembly)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.services.emails import EmailService


@pytest.mark.asyncio
async def test_send_welcome_email_schedules_background_task():
    """send_welcome_email should enqueue a send_message task."""
    service = EmailService()
    with patch("src.services.emails.FastMail") as fm_mock:
        fm_instance = fm_mock.return_value
        fm_instance.send_message = AsyncMock()

        await service.send_welcome_email("user@test.com", "Alice")

    assert fm_mock.called
    assert fm_instance.send_message.called


@pytest.mark.asyncio
async def test_send_password_reset_email_schedules_background_task():
    """send_password_reset_email should enqueue a send_message task."""
    service = EmailService()
    with patch("src.services.emails.FastMail") as fm_mock:
        fm_instance = fm_mock.return_value
        fm_instance.send_message = AsyncMock()

        await service.send_password_reset_email(
            "user@test.com", "reset-token-123"
        )

    assert fm_mock.called
    assert fm_instance.send_message.called


@pytest.mark.asyncio
async def test_welcome_email_uses_site_name_in_subject_and_body():
    """Verify FastMail received a MessageSchema with FinanSee references."""
    service = EmailService()
    with patch("src.services.emails.FastMail") as fm_mock:
        fm_instance = fm_mock.return_value
        fm_instance.send_message = AsyncMock()

        await service.send_welcome_email("user@test.com", "Bob")

    fm_instance = fm_mock.return_value
    assert fm_instance is not None
    call_args = fm_instance.send_message.call_args
    message_schema = call_args[0][0]
    template_name = call_args[1]["template_name"]
    assert template_name == "welcome.html"
    assert "FinanSee" in message_schema.subject
    assert message_schema.template_body["name"] == "Bob"
    assert message_schema.template_body["site_name"] == "FinanSee"


@pytest.mark.asyncio
async def test_password_reset_email_uses_site_name_in_subject():
    """Verify the reset template carries the token and site_name."""
    service = EmailService()
    with patch("src.services.emails.FastMail") as fm_mock:
        fm_instance = fm_mock.return_value
        fm_instance.send_message = AsyncMock()

        await service.send_password_reset_email("user@test.com", "TOKEN-XYZ")

    call_args = fm_instance.send_message.call_args
    message_schema = call_args[0][0]
    assert "FinanSee" in message_schema.subject
    assert message_schema.template_body["token"] == "TOKEN-XYZ"
    assert message_schema.template_body["site_name"] == "FinanSee"
