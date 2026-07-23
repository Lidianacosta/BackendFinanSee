"""Unit tests for EmailService methods (no SMTP, just message assembly)."""

from unittest.mock import patch

import pytest
from fastapi import BackgroundTasks

from src.services.emails import EmailService


@pytest.mark.asyncio
async def test_send_welcome_email_schedules_background_task():
    """send_welcome_email should enqueue a send_message task."""
    service = EmailService()
    bg = BackgroundTasks()

    with patch("src.services.emails.FastMail") as fm_mock:
        await service.send_welcome_email("user@test.com", "Alice", bg)

    assert fm_mock.called
    assert len(bg.tasks) == 1


@pytest.mark.asyncio
async def test_send_password_reset_email_schedules_background_task():
    """send_password_reset_email should enqueue a send_message task."""
    service = EmailService()
    bg = BackgroundTasks()

    with patch("src.services.emails.FastMail") as fm_mock:
        await service.send_password_reset_email(
            "user@test.com", "reset-token-123", bg
        )

    assert fm_mock.called
    assert len(bg.tasks) == 1


@pytest.mark.asyncio
async def test_welcome_email_uses_site_name_in_subject_and_body():
    """Verify FastMail received a MessageSchema with FinanSee references."""
    service = EmailService()
    bg = BackgroundTasks()

    with patch("src.services.emails.FastMail") as fm_mock:
        await service.send_welcome_email("user@test.com", "Bob", bg)

    fm_instance = fm_mock.return_value
    assert fm_instance is not None
    assert len(bg.tasks) == 1
    fn = bg.tasks[0]
    message_schema = fn.args[0]
    template_name = fn.kwargs["template_name"]
    assert template_name == "welcome.html"
    assert "FinanSee" in message_schema.subject
    assert message_schema.template_body["name"] == "Bob"
    assert message_schema.template_body["site_name"] == "FinanSee"


@pytest.mark.asyncio
async def test_password_reset_email_uses_site_name_in_subject():
    """Verify the reset template carries the token and site_name."""
    service = EmailService()
    bg = BackgroundTasks()

    with patch("src.services.emails.FastMail"):
        await service.send_password_reset_email(
            "user@test.com", "TOKEN-XYZ", bg
        )

    fn = bg.tasks[0]
    message_schema = fn.args[0]
    assert "FinanSee" in message_schema.subject
    assert message_schema.template_body["token"] == "TOKEN-XYZ"
    assert message_schema.template_body["site_name"] == "FinanSee"
