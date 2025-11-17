from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import User, ProgressReport
from ..schemas import ProgressReportResponse
from ..services.analysis_service import analysis_service
from .auth import get_current_user

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.post("/generate", response_model=ProgressReportResponse)
async def generate_progress_report(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a new progress report for the current user"""

    if days < 1 or days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 90"
        )

    try:
        report = await analysis_service.generate_progress_report(
            db=db,
            user_id=current_user.id,
            days=days
        )

        return report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/reports", response_model=List[ProgressReportResponse])
async def get_progress_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """Get all progress reports for the current user"""

    result = await db.execute(
        select(ProgressReport)
        .where(ProgressReport.user_id == current_user.id)
        .order_by(ProgressReport.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    reports = result.scalars().all()

    return reports


@router.get("/reports/{report_id}", response_model=ProgressReportResponse)
async def get_progress_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific progress report"""

    result = await db.execute(
        select(ProgressReport).where(
            ProgressReport.id == report_id,
            ProgressReport.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    return report
