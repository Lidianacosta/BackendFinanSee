"""Service for generating financial reports in PDF format."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import Depends
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from weasyprint import HTML

from src.models.expenses import Expense
from src.models.users import User
from src.services.periods import PeriodServiceDep
from src.utils.database import AsyncSessionDep


class ReportService:
    """Service to handle the creation and rendering of PDF reports."""

    def __init__(
        self, session: AsyncSessionDep, period_service: PeriodServiceDep
    ) -> None:
        """Initialize ReportService with dependencies."""
        self.session = session
        self.period_service = period_service
        self.jinja_env = Environment(
            loader=FileSystemLoader("src/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _get_month_name(self, month: date) -> str:
        """Translate month number to Portuguese name."""
        months = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }
        return months.get(month.month, "")

    async def generate_period_pdf(
        self, period_id: uuid.UUID, user: User
    ) -> bytes:
        """Render and generate a PDF report for a financial period."""
        period = await self.period_service.read(period_id, user.id)
        summary = await self.period_service.get_summary(period_id, user.id)

        statement = (
            select(Expense)
            .where(col(Expense.period_id) == period_id)
            .options(selectinload(Expense.categories))  # type: ignore[arg-type]
            .order_by(col(Expense.due_date))
        )
        result = await self.session.exec(statement)
        expenses = list(result.all())

        template = self.jinja_env.get_template("report.html")
        html_content = template.render(
            user=user,
            period=period,
            summary=summary,
            expenses=expenses,
            period_month=self._get_month_name(period.month),
            today_str=date.today().strftime("%d/%m/%Y"),
        )

        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes


ReportServiceDep = Annotated[ReportService, Depends(ReportService)]
