"""
Utility script to create an admin user for the AI Coaching Platform
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User
from app.services.auth_service import auth_service


async def create_admin_user(
    username: str,
    email: str,
    password: str,
    full_name: str = None
):
    """Create a new admin user"""
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(
            select(User).where(
                (User.email == email) | (User.username == username)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == username:
                print(f"❌ Error: Username '{username}' already exists")
                return
            if existing_user.email == email:
                print(f"❌ Error: Email '{email}' already exists")
                return

        # Create admin user
        hashed_password = auth_service.get_password_hash(password)
        admin_user = User(
            email=email,
            username=username,
            full_name=full_name or username,
            hashed_password=hashed_password,
            is_admin=True,
            is_active=True
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        print(f"✅ Admin user created successfully!")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Admin: {admin_user.is_admin}")
        print(f"   ID: {admin_user.id}")


async def make_user_admin(username: str):
    """Make an existing user an admin"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ Error: User '{username}' not found")
            return

        user.is_admin = True
        await db.commit()
        await db.refresh(user)

        print(f"✅ User '{username}' is now an admin!")


async def list_admins():
    """List all admin users"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.is_admin == True)
        )
        admins = result.scalars().all()

        if not admins:
            print("No admin users found")
            return

        print(f"\n{'='*60}")
        print(f"Admin Users ({len(admins)})")
        print(f"{'='*60}")
        for admin in admins:
            print(f"ID: {admin.id:4d} | Username: {admin.username:20s} | Email: {admin.email}")


async def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Create admin:    python create_admin.py create <username> <email> <password> [full_name]")
        print("  Make user admin: python create_admin.py promote <username>")
        print("  List admins:     python create_admin.py list")
        return

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 5:
            print("Error: Missing required arguments")
            print("Usage: python create_admin.py create <username> <email> <password> [full_name]")
            return

        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        full_name = sys.argv[5] if len(sys.argv) > 5 else None

        await create_admin_user(username, email, password, full_name)

    elif command == "promote":
        if len(sys.argv) < 3:
            print("Error: Missing username")
            print("Usage: python create_admin.py promote <username>")
            return

        username = sys.argv[2]
        await make_user_admin(username)

    elif command == "list":
        await list_admins()

    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, promote, list")


if __name__ == "__main__":
    asyncio.run(main())
