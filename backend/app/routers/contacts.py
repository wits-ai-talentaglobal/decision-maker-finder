from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Company
from app.schemas import CompanyOut

router = APIRouter(prefix="/companies", tags=["contacts"])


@router.get("", response_model=list[CompanyOut])
async def list_companies_with_contacts(session: AsyncSession = Depends(get_session)):
    """Flat listing of every resolved company and its contacts — the source data
    the frontend's expandable results table and CSV export are built from."""
    result = await session.execute(
        select(Company).options(selectinload(Company.contacts)).order_by(Company.id.desc())
    )
    companies = result.scalars().all()
    return [CompanyOut.model_validate(c) for c in companies]
