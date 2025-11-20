from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import AIModelProvider, TeamRole, LessonType, LessonStatus


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    preferred_ai_model: Optional[AIModelProvider] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    preferred_ai_model: AIModelProvider
    created_at: datetime

    class Config:
        from_attributes = True


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Team Schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TeamResponse(TeamBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TeamMemberAdd(BaseModel):
    user_id: int
    role: TeamRole = TeamRole.MEMBER


# Lesson Schemas
class LessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    lesson_type: LessonType


class LessonCreate(LessonBase):
    content: Dict[str, Any]
    scenario: str
    objectives: List[str]
    difficulty_level: int = Field(ge=1, le=5, default=1)
    estimated_duration: Optional[int] = None
    tags: Optional[List[str]] = None


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    scenario: Optional[str] = None
    objectives: Optional[List[str]] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)
    estimated_duration: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class LessonResponse(LessonBase):
    id: int
    content: Dict[str, Any]
    scenario: str
    objectives: List[str]
    difficulty_level: int
    estimated_duration: Optional[int]
    tags: Optional[List[str]]
    is_active: bool
    status: LessonStatus
    created_by: Optional[int]
    reviewed_by: Optional[int]
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Admin Lesson Schemas
class LessonGenerateRequest(BaseModel):
    prompt: str
    lesson_type: LessonType
    ai_model: AIModelProvider = AIModelProvider.ANTHROPIC
    additional_context: Optional[str] = None


class LessonGenerateResponse(BaseModel):
    lesson_id: int
    title: str
    status: LessonStatus
    message: str


class LessonRefineRequest(BaseModel):
    refinement_prompt: str
    ai_model: AIModelProvider = AIModelProvider.ANTHROPIC


class LessonStatusUpdate(BaseModel):
    status: LessonStatus
    notes: Optional[str] = None


class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    size: int


# Chat Session Schemas
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Session"
    lesson_id: Optional[int] = None
    ai_model: AIModelProvider = AIModelProvider.OPENAI


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    lesson_id: Optional[int]
    title: str
    ai_model: AIModelProvider
    is_active: bool
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Message Schemas
class MessageCreate(BaseModel):
    content: str
    role: str = "user"


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    ai_model_used: Optional[AIModelProvider]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    ai_model: Optional[AIModelProvider] = None


class ChatResponse(BaseModel):
    session_id: int
    message: MessageResponse
    ai_response: MessageResponse


# Progress Report Schemas
class ProgressReportResponse(BaseModel):
    id: int
    user_id: int
    period_start: datetime
    period_end: datetime
    summary: str
    strengths: List[str]
    areas_for_improvement: List[str]
    recommendations: List[str]
    total_sessions: int
    total_messages: int
    lessons_completed: int
    engagement_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
