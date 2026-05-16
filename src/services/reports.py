"""Report service layer for PDF generation."""

from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from weasyprint import HTML

from src.models.expenses import Expense
from src.models.users import User
from src.services.periods import PeriodService
from src.utils.database import AsyncSessionDep


class ReportService:
    def __init__(
        self, session: AsyncSessionDep, period_service: PeriodService
    ) -> None:
        self.session = session
        self.period_service = period_service

        template_path = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(template_path))

    def _get_month_name(self, month_date: date) -> str:
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
        return f"{months[month_date.month]} de {month_date.year}"

    async def generate_period_pdf(self, period_id: str, user: User) -> bytes:
        """Generates a professional PDF report for a specific period."""
        period = await self.period_service.read(period_id, user.id)
        summary = await self.period_service.get_summary(period_id, user.id)

        statement = (
            select(Expense)
            .where(col(Expense.period_id) == period.id)
            .options(selectinload(Expense.categories))
            .order_by(col(Expense.due_date))
        )
        result = await self.session.exec(statement)
        expenses = result.all()

        template = self.jinja_env.get_template("report.html")
        html_content = template.render(
            user=user,
            period=period,
            period_month=self._get_month_name(period.month),
            summary=summary,
            expenses=expenses,
            today_str=date.today().strftime("%d/%m/%Y"),
        )

        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes


ReportServiceDep = Annotated[ReportService, Depends(ReportService)]
