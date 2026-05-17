"""Email service layer for asynchronous email sending."""

from pathlib import Path
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from src.core.config import settings


class EmailService:
    def __init__(self) -> None:
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
        self.fastmail = FastMail(self.config)

    async def send_email(
        self,
        subject: str,
        recipients: list[str],
        template_name: str,
        context: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> None:
        """Sends an asynchronous email using background tasks."""
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            template_body=context,
            subtype=MessageType.html,
        )
        background_tasks.add_task(
            self.fastmail.send_message, message, template_name=template_name
        )

    async def send_welcome_email(
        self, email: str, name: str, background_tasks: BackgroundTasks
    ) -> None:
        """Sends a welcome email to a new user."""
        await self.send_email(
            subject="Bem-vindo ao FinanSee!",
            recipients=[email],
            template_name="welcome.html",
            context={"name": name, "site_name": "FinanSee"},
            background_tasks=background_tasks,
        )

    async def send_password_reset_email(
        self, email: str, token: str, background_tasks: BackgroundTasks
    ) -> None:
        """Sends a password reset email."""
        await self.send_email(
            subject="Recuperação de Senha - FinanSee",
            recipients=[email],
            template_name="password_reset.html",
            context={"token": token, "site_name": "FinanSee"},
            background_tasks=background_tasks,
        )


EmailServiceDep = Annotated[EmailService, Depends(EmailService)]
