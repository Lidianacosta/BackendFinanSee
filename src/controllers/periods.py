import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.models.users import User
from src.schemas.periods import PeriodCreate, PeriodRead, PeriodSummary
from src.services.periods import PeriodServiceDep
from src.utils.security import get_current_active_user

router = APIRouter(prefix="/periods", tags=["Periods"])


@router.post(
    "/", response_model=PeriodRead, status_code=status.HTTP_201_CREATED
)
async def create_period(
    period_data: PeriodCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Cria um novo período (mês) de controle financeiro."""
    return await service.create(period_data, current_user.id)


@router.get("/", response_model=list[PeriodRead])
async def read_periods(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Lista todos os períodos cadastrados do usuário."""
    return await service.read_all(current_user.id)


@router.get("/{period_id}", response_model=PeriodRead)
async def read_period(
    period_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Busca detalhes de um período específico."""
    return await service.read(period_id, current_user.id)


@router.get("/{period_id}/summary", response_model=PeriodSummary)
async def read_period_summary(
    period_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: PeriodServiceDep,
):
    """Retorna o resumo financeiro (Saldo, Despesas Pagas/Pendentes) do período."""
    return await service.get_summary(period_id, current_user.id)
