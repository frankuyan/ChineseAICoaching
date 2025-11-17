from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import User, Lesson
from ..schemas import LessonCreate, LessonUpdate, LessonResponse
from .auth import get_current_user

router = APIRouter(prefix="/lessons", tags=["Lessons"])


@router.get("", response_model=List[LessonResponse])
async def get_lessons(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    lesson_type: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get all active lessons"""

    query = select(Lesson).where(Lesson.is_active == True)

    if lesson_type:
        query = query.where(Lesson.lesson_type == lesson_type)

    query = query.order_by(Lesson.difficulty_level.asc(), Lesson.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    lessons = result.scalars().all()

    return lessons


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific lesson"""

    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    return lesson


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new lesson (admin/coach only)"""

    # In production, you'd check for admin role here
    # For now, any authenticated user can create lessons

    new_lesson = Lesson(
        title=lesson_data.title,
        description=lesson_data.description,
        lesson_type=lesson_data.lesson_type,
        content=lesson_data.content,
        scenario=lesson_data.scenario,
        objectives=lesson_data.objectives,
        difficulty_level=lesson_data.difficulty_level,
        estimated_duration=lesson_data.estimated_duration,
        tags=lesson_data.tags
    )

    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)

    return new_lesson


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a lesson (admin/coach only)"""

    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Update fields
    update_data = lesson_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)

    await db.commit()
    await db.refresh(lesson)

    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a lesson (admin/coach only)"""

    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Soft delete
    lesson.is_active = False
    await db.commit()

    return None
