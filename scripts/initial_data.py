#!/usr/bin/env python3
"""
Initial data script for Stocky Backend

This script creates the first admin user and any other essential initial data.
Run this after setting up the database to bootstrap the application.

Usage:
    python scripts/initial_data.py
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
current_path = Path(__file__).parent.parent
src_path = current_path / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy.orm import Session
from passlib.context import CryptContext
import getpass

from stocky_backend.db.database import SessionLocal, engine
from stocky_backend.models.models import User, UserRole, StorageType, Location
from stocky_backend.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def create_admin_user(db: Session) -> User:
    """Create the first admin user"""
    
    # Check if any admin users already exist
    existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if existing_admin:
        print(f"Admin user already exists: {existing_admin.username}")
        return existing_admin
    
    print("Creating the first admin user...")
    
    # Get user input
    while True:
        username = input("Enter admin username: ").strip()
        if username:
            break
        print("Username cannot be empty!")
    
    while True:
        email = input("Enter admin email: ").strip()
        if email and "@" in email:
            break
        print("Please enter a valid email address!")
    
    while True:
        password = getpass.getpass("Enter admin password: ")
        if len(password) >= 8:
            break
        print("Password must be at least 8 characters long!")
    
    # Create the admin user
    admin_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"✅ Admin user '{username}' created successfully!")
    return admin_user


def create_default_locations(db: Session, admin_user: User) -> None:
    """Create some default storage locations"""
    
    # Check if locations already exist
    existing_locations = db.query(Location).count()
    if existing_locations > 0:
        print(f"Locations already exist ({existing_locations} found)")
        return
    
    print("Creating default storage locations...")
    
    default_locations = [
        {
            "name": "Pantry",
            "description": "Main pantry storage area",
            "storage_type": StorageType.PANTRY
        },
        {
            "name": "Refrigerator",
            "description": "Main refrigerator",
            "storage_type": StorageType.REFRIGERATOR
        },
        {
            "name": "Freezer",
            "description": "Main freezer",
            "storage_type": StorageType.FREEZER
        },
        {
            "name": "Counter",
            "description": "Kitchen counter storage",
            "storage_type": StorageType.COUNTER
        }
    ]
    
    for location_data in default_locations:
        location = Location(
            name=location_data["name"],
            description=location_data["description"],
            storage_type=location_data["storage_type"],
            created_by=admin_user.id,
            is_active=True
        )
        db.add(location)
    
    db.commit()
    print(f"✅ Created {len(default_locations)} default locations")


def main():
    """Main function to initialize the database with essential data"""
    
    print("🚀 Stocky Backend - Initial Data Setup")
    print("=" * 40)
    
    # Verify database exists
    if not os.path.exists("data/stocky.db"):
        print("❌ Database not found! Please run 'alembic upgrade head' first.")
        sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = create_admin_user(db)
        
        # Create default locations
        create_default_locations(db, admin_user)
        
        print("\n✅ Initial data setup completed successfully!")
        print("\nYou can now start the Stocky Backend server.")
        print("The admin user can create additional users and manage the system.")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
