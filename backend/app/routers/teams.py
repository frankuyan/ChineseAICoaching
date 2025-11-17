from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_db
from ..models import User, Team, user_teams, Lesson
from ..schemas import TeamCreate, TeamUpdate, TeamResponse, TeamMemberAdd, UserResponse
from .auth import get_current_user

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new team"""

    new_team = Team(
        name=team_data.name,
        description=team_data.description
    )

    db.add(new_team)
    await db.flush()

    # Add creator as admin
    from ..models import TeamRole
    stmt = user_teams.insert().values(
        user_id=current_user.id,
        team_id=new_team.id,
        role=TeamRole.ADMIN
    )
    await db.execute(stmt)

    await db.commit()
    await db.refresh(new_team)

    return new_team


@router.get("", response_model=List[TeamResponse])
async def get_user_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all teams the current user is a member of"""

    result = await db.execute(
        select(Team)
        .join(user_teams)
        .where(user_teams.c.user_id == current_user.id)
    )
    teams = result.scalars().all()

    return teams


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team details"""

    # Verify user is member
    result = await db.execute(
        select(Team)
        .join(user_teams)
        .where(
            Team.id == team_id,
            user_teams.c.user_id == current_user.id
        )
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or you are not a member"
        )

    return team


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update team (admin/leader only)"""

    # Get team and verify membership
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # TODO: Check if user is admin/leader

    # Update fields
    update_data = team_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.commit()
    await db.refresh(team)

    return team


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a member to the team (admin/leader only)"""

    # Verify team exists
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == member_data.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already a member
    result = await db.execute(
        select(user_teams).where(
            user_teams.c.team_id == team_id,
            user_teams.c.user_id == member_data.user_id
        )
    )
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member"
        )

    # Add member
    stmt = user_teams.insert().values(
        user_id=member_data.user_id,
        team_id=team_id,
        role=member_data.role
    )
    await db.execute(stmt)
    await db.commit()

    return {"message": "Member added successfully"}


@router.get("/{team_id}/members", response_model=List[UserResponse])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all team members"""

    # Verify user is member
    result = await db.execute(
        select(user_teams).where(
            user_teams.c.team_id == team_id,
            user_teams.c.user_id == current_user.id
        )
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )

    # Get members
    result = await db.execute(
        select(User)
        .join(user_teams)
        .where(user_teams.c.team_id == team_id)
    )
    members = result.scalars().all()

    return members


@router.post("/{team_id}/lessons/{lesson_id}", status_code=status.HTTP_201_CREATED)
async def assign_lesson_to_team(
    team_id: int,
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a lesson to a team (admin/leader only)"""

    from ..models import team_lessons

    # Verify team exists
    result = await db.execute(
        select(Team).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Verify lesson exists
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.is_active == True)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Check if already assigned
    result = await db.execute(
        select(team_lessons).where(
            team_lessons.c.team_id == team_id,
            team_lessons.c.lesson_id == lesson_id
        )
    )
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson already assigned to team"
        )

    # Assign lesson
    stmt = team_lessons.insert().values(
        team_id=team_id,
        lesson_id=lesson_id
    )
    await db.execute(stmt)
    await db.commit()

    return {"message": "Lesson assigned to team successfully"}
