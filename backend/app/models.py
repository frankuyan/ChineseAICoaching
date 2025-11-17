from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Table,
    Text, Boolean, Float, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base


# Enum for AI model providers
class AIModelProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"


# Enum for user roles in teams
class TeamRole(str, enum.Enum):
    MEMBER = "member"
    LEADER = "leader"
    ADMIN = "admin"


# Enum for lesson types
class LessonType(str, enum.Enum):
    BUSINESS_PRACTICE = "business_practice"
    CLIENT_INTERACTION = "client_interaction"
    LEADERSHIP = "leadership"
    NEGOTIATION = "negotiation"
    COMMUNICATION = "communication"
    DECISION_MAKING = "decision_making"
    CUSTOM = "custom"


# Association table for user-team relationship
user_teams = Table(
    'user_teams',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('team_id', Integer, ForeignKey('teams.id', ondelete='CASCADE')),
    Column('role', SQLEnum(TeamRole), default=TeamRole.MEMBER),
    Column('joined_at', DateTime(timezone=True), server_default=func.now())
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Preferences
    preferred_ai_model = Column(SQLEnum(AIModelProvider), default=AIModelProvider.OPENAI)

    # Relationships
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    teams = relationship("Team", secondary=user_teams, back_populates="members")
    progress_reports = relationship("ProgressReport", back_populates="user", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    members = relationship("User", secondary=user_teams, back_populates="teams")
    shared_lessons = relationship("Lesson", secondary="team_lessons", back_populates="teams")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    lesson_type = Column(SQLEnum(LessonType), nullable=False)

    # Lesson content
    content = Column(JSON)  # Stores structured lesson content
    scenario = Column(Text)  # Scenario description
    objectives = Column(JSON)  # List of learning objectives

    # Difficulty and metadata
    difficulty_level = Column(Integer, default=1)  # 1-5
    estimated_duration = Column(Integer)  # in minutes
    tags = Column(JSON)  # List of tags

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sessions = relationship("ChatSession", back_populates="lesson")
    teams = relationship("Team", secondary="team_lessons", back_populates="shared_lessons")


# Association table for team-lesson relationship
team_lessons = Table(
    'team_lessons',
    Base.metadata,
    Column('team_id', Integer, ForeignKey('teams.id', ondelete='CASCADE')),
    Column('lesson_id', Integer, ForeignKey('lessons.id', ondelete='CASCADE')),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    lesson_id = Column(Integer, ForeignKey('lessons.id', ondelete='SET NULL'), nullable=True)

    title = Column(String, default="New Session")
    ai_model = Column(SQLEnum(AIModelProvider), default=AIModelProvider.OPENAI)

    # Session metadata
    session_metadata = Column(JSON)  # Additional metadata
    vector_collection_id = Column(String)  # Reference to ChromaDB collection

    # Session state
    is_active = Column(Boolean, default=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")
    lesson = relationship("Lesson", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id', ondelete='CASCADE'))

    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # AI metadata
    ai_model_used = Column(SQLEnum(AIModelProvider), nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Vector embedding reference
    embedding_id = Column(String)  # Reference to ChromaDB document

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class ProgressReport(Base):
    __tablename__ = "progress_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))

    # Report period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Analysis results
    analysis = Column(JSON)  # Structured analysis data
    summary = Column(Text)  # Human-readable summary
    strengths = Column(JSON)  # List of identified strengths
    areas_for_improvement = Column(JSON)  # List of areas to improve
    recommendations = Column(JSON)  # List of recommendations

    # Metrics
    total_sessions = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    engagement_score = Column(Float)  # 0-100

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="progress_reports")
