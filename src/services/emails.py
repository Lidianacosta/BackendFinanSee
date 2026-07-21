"""Email service for sending notifications and authentication emails."""

from pathlib import Path
from typing import Annotated

from fastapi import BackgroundTasks, Depends
from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
)

from src.core.config import settings


class EmailService:
    """Service responsible for sending asynchronous emails."""

    def __init__(self) -> None:
        """Initialize the email service with SMTP configuration."""
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_FROM_NAME=settings.mail_from_name,
            MAIL_STARTTLS=settings.mail_starttls,
            MAIL_SSL_TLS=settings.mail_ssl_tls,
            USE_CREDENTIALS=settings.use_credentials,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=Path(__file__).parent.parent
            / "templates"
            / "email",
        )

        self.site_name = "FinanSee"

    async def send_welcome_email(
        self, email: str, name: str, background_tasks: BackgroundTasks
    ) -> None:
        """Send a welcome email to a newly registered user."""
        message = MessageSchema(
            subject=f"Bem-vindo ao {self.site_name}!",
            recipients=[email],
            template_body={"name": name, "site_name": self.site_name},
            subtype=MessageType.html,
        )
        fm = FastMail(self.config)
        background_tasks.add_task(
            fm.send_message, message, template_name="welcome.html"
        )

    async def send_password_reset_email(
        self, email: str, token: str, background_tasks: BackgroundTasks
    ) -> None:
        """Send an email with instructions and token for password reset."""
        message = MessageSchema(
            subject=f"Recuperação de Senha - {self.site_name}",
            recipients=[email],
            template_body={"token": token, "site_name": self.site_name},
            subtype=MessageType.html,
        )
        fm = FastMail(self.config)
        background_tasks.add_task(
            fm.send_message, message, template_name="password_reset.html"
        )


EmailServiceDep = Annotated[EmailService, Depends(EmailService)]
