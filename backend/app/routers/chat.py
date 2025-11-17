from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import User, ChatSession, Message, Lesson
from ..schemas import (
    ChatSessionCreate, ChatSessionResponse,
    MessageResponse, ChatRequest, ChatResponse
)
from ..services.ai_service import ai_service
from ..services.vector_service import vector_service
from .auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""

    # Validate lesson if provided
    if session_data.lesson_id:
        result = await db.execute(
            select(Lesson).where(Lesson.id == session_data.lesson_id, Lesson.is_active == True)
        )
        lesson = result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )

    # Create session
    new_session = ChatSession(
        user_id=current_user.id,
        lesson_id=session_data.lesson_id,
        title=session_data.title,
        ai_model=session_data.ai_model,
        vector_collection_id=f"user_{current_user.id}_session_{id}"
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return new_session


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get user's chat sessions"""

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()

    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific chat session"""

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a session"""

    # Verify session ownership
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return messages


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response"""

    session = None

    # Get or create session
    if chat_request.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == chat_request.session_id,
                ChatSession.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    else:
        # Create new session
        ai_model = chat_request.ai_model or current_user.preferred_ai_model
        session = ChatSession(
            user_id=current_user.id,
            title="New Chat",
            ai_model=ai_model,
            vector_collection_id=f"user_{current_user.id}_session"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # Store user message
    user_message = Message(
        session_id=session.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    # Store in vector DB
    await vector_service.store_message(
        user_id=current_user.id,
        session_id=session.id,
        message_id=user_message.id,
        role="user",
        content=chat_request.message
    )

    # Get conversation history
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
    )
    all_messages = result.scalars().all()

    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in all_messages[:-1]  # Exclude the message we just added
    ]

    # Get lesson context if applicable
    lesson_context = None
    if session.lesson_id:
        result = await db.execute(
            select(Lesson).where(Lesson.id == session.lesson_id)
        )
        lesson = result.scalar_one_or_none()
        if lesson:
            lesson_context = {
                "title": lesson.title,
                "lesson_type": lesson.lesson_type.value,
                "scenario": lesson.scenario,
                "objectives": lesson.objectives
            }

    # Generate AI response
    try:
        ai_response_data = await ai_service.generate_agentic_response(
            user_message=chat_request.message,
            conversation_history=conversation_history,
            lesson_context=lesson_context,
            provider=session.ai_model
        )

        # Store AI response
        ai_message = Message(
            session_id=session.id,
            role="assistant",
            content=ai_response_data['content'],
            ai_model_used=session.ai_model,
            tokens_used=ai_response_data.get('tokens_used')
        )
        db.add(ai_message)
        await db.commit()
        await db.refresh(ai_message)

        # Store AI response in vector DB
        await vector_service.store_message(
            user_id=current_user.id,
            session_id=session.id,
            message_id=ai_message.id,
            role="assistant",
            content=ai_response_data['content'],
            metadata={"ai_model": session.ai_model.value}
        )

        return ChatResponse(
            session_id=session.id,
            message=user_message,
            ai_response=ai_message
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating AI response: {str(e)}"
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Delete from vector DB
    await vector_service.delete_session_data(current_user.id, session_id)

    # Delete from database (cascade will handle messages)
    await db.delete(session)
    await db.commit()

    return None


@router.post("/sessions/{session_id}/complete", response_model=ChatSessionResponse)
async def complete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a session as completed"""

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    from datetime import datetime
    session.is_active = False
    session.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return session
