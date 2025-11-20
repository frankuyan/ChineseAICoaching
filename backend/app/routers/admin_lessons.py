from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, Lesson, LessonStatus, LessonType, AIModelProvider
from ..schemas import (
    LessonResponse, LessonGenerateRequest, LessonGenerateResponse,
    LessonRefineRequest, LessonStatusUpdate, LessonUpdate
)
from ..routers.auth import get_current_admin_user
from ..services.document_service import document_service
from ..services.lesson_generator import lesson_generator
from loguru import logger

router = APIRouter(prefix="/admin/lessons", tags=["Admin Lessons"])


@router.post("/generate", response_model=LessonGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_lesson_from_documents(
    prompt: str = Form(...),
    lesson_type: LessonType = Form(...),
    ai_model: AIModelProvider = Form(AIModelProvider.ANTHROPIC),
    additional_context: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Generate a new lesson using AI from uploaded documents (Admin only)

    Upload one or more documents and provide a prompt describing the lesson you want to create.
    The AI will analyze the documents and generate a comprehensive lesson in draft status.
    """
    try:
        # Validate files
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one document is required"
            )

        # Parse all uploaded documents
        parsed_documents = []
        for file in files:
            if not document_service.is_supported(file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file format: {file.filename}"
                )

            content = await file.read()
            parsed_doc = await document_service.parse_document(content, file.filename)
            parsed_documents.append(parsed_doc)

        # Generate lesson using AI
        lesson_data = await lesson_generator.generate_lesson_from_documents(
            prompt=prompt,
            documents=parsed_documents,
            lesson_type=lesson_type,
            provider=ai_model,
            additional_context=additional_context
        )

        # Create lesson in database with DRAFT status
        new_lesson = Lesson(
            title=lesson_data["title"],
            description=lesson_data["description"],
            lesson_type=lesson_type,
            content=lesson_data["content"],
            scenario=lesson_data["scenario"],
            objectives=lesson_data["objectives"],
            difficulty_level=lesson_data.get("difficulty_level", 2),
            estimated_duration=lesson_data.get("estimated_duration", 30),
            tags=lesson_data.get("tags", []),
            status=LessonStatus.DRAFT,
            created_by=current_user.id,
            generation_prompt=prompt,
            source_documents=[
                {"filename": doc["filename"], "format": doc["format"]}
                for doc in parsed_documents
            ]
        )

        db.add(new_lesson)
        await db.commit()
        await db.refresh(new_lesson)

        logger.info(f"Admin {current_user.username} generated lesson {new_lesson.id}: {new_lesson.title}")

        return LessonGenerateResponse(
            lesson_id=new_lesson.id,
            title=new_lesson.title,
            status=new_lesson.status,
            message=f"Lesson generated successfully from {len(parsed_documents)} document(s)"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate lesson"
        )


@router.post("/{lesson_id}/refine", response_model=LessonResponse)
async def refine_lesson(
    lesson_id: int,
    refine_request: LessonRefineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Refine an existing draft lesson using AI (Admin only)

    Provide feedback or refinement instructions and the AI will update the lesson.
    """
    # Get lesson
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    if lesson.status not in [LessonStatus.DRAFT, LessonStatus.IN_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refine lessons in DRAFT or IN_REVIEW status"
        )

    try:
        # Build current lesson data
        current_lesson_data = {
            "title": lesson.title,
            "description": lesson.description,
            "scenario": lesson.scenario,
            "objectives": lesson.objectives,
            "content": lesson.content,
            "difficulty_level": lesson.difficulty_level,
            "estimated_duration": lesson.estimated_duration,
            "tags": lesson.tags
        }

        # Refine using AI
        refined_data = await lesson_generator.refine_lesson(
            lesson_data=current_lesson_data,
            refinement_prompt=refine_request.refinement_prompt,
            provider=refine_request.ai_model
        )

        # Update lesson
        lesson.title = refined_data.get("title", lesson.title)
        lesson.description = refined_data.get("description", lesson.description)
        lesson.scenario = refined_data.get("scenario", lesson.scenario)
        lesson.objectives = refined_data.get("objectives", lesson.objectives)
        lesson.content = refined_data.get("content", lesson.content)
        lesson.difficulty_level = refined_data.get("difficulty_level", lesson.difficulty_level)
        lesson.estimated_duration = refined_data.get("estimated_duration", lesson.estimated_duration)
        lesson.tags = refined_data.get("tags", lesson.tags)

        await db.commit()
        await db.refresh(lesson)

        logger.info(f"Admin {current_user.username} refined lesson {lesson_id}")

        return lesson

    except Exception as e:
        logger.error(f"Error refining lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine lesson: {str(e)}"
        )


@router.patch("/{lesson_id}/status", response_model=LessonResponse)
async def update_lesson_status(
    lesson_id: int,
    status_update: LessonStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update lesson status (Admin only)

    Transitions: DRAFT -> IN_REVIEW -> PUBLISHED
    Can also archive lessons.
    """
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Update status
    old_status = lesson.status
    lesson.status = status_update.status

    # If publishing, set published_at and reviewed_by
    if status_update.status == LessonStatus.PUBLISHED and old_status != LessonStatus.PUBLISHED:
        lesson.published_at = datetime.utcnow()
        lesson.reviewed_by = current_user.id

    await db.commit()
    await db.refresh(lesson)

    logger.info(f"Admin {current_user.username} changed lesson {lesson_id} status: {old_status} -> {status_update.status}")

    return lesson


@router.get("/drafts", response_model=List[LessonResponse])
async def get_draft_lessons(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """Get all draft lessons (Admin only)"""
    query = select(Lesson).where(Lesson.status == LessonStatus.DRAFT)
    query = query.order_by(Lesson.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    lessons = result.scalars().all()

    return lessons


@router.get("/in-review", response_model=List[LessonResponse])
async def get_lessons_in_review(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user)
):
    """Get all lessons in review (Admin only)"""
    query = select(Lesson).where(Lesson.status == LessonStatus.IN_REVIEW)
    query = query.order_by(Lesson.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    lessons = result.scalars().all()

    return lessons


@router.get("/all", response_model=List[LessonResponse])
async def get_all_lessons_admin(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[LessonStatus] = None,
    current_user: User = Depends(get_current_admin_user)
):
    """Get all lessons regardless of status (Admin only)"""
    query = select(Lesson)

    if status_filter:
        query = query.where(Lesson.status == status_filter)

    query = query.order_by(Lesson.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    lessons = result.scalars().all()

    return lessons


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_draft_lesson(
    lesson_id: int,
    lesson_data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Manually update a lesson (Admin only)"""
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

    logger.info(f"Admin {current_user.username} updated lesson {lesson_id}")

    return lesson


@router.get("/supported-formats")
async def get_supported_document_formats(
    current_user: User = Depends(get_current_admin_user)
):
    """Get list of supported document formats for upload"""
    return {
        "supported_formats": document_service.get_supported_formats(),
        "description": "Upload documents in these formats to generate lessons"
    }
