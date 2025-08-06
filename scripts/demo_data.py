#!/usr/bin/env python3
"""
Demo data script for Stocky Backend

This script creates sample data for testing and demonstration purposes.
Run this after initial_data.py to populate the system with example inventory.

Usage:
    python scripts/demo_data.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add the src directory to the Python path
current_path = Path(__file__).parent.parent
src_path = current_path / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy.orm import Session

from stocky_backend.db.database import SessionLocal
from stocky_backend.models.models import User, Item, Location, SKU, Alert, UserRole, StorageType


def create_sample_items(db: Session, admin_user: User) -> list[Item]:
    """Create sample food items"""
    
    sample_items = [
        {"name": "Whole Milk", "description": "1 gallon whole milk", "upc": "012345678901", "default_storage_type": StorageType.REFRIGERATOR},
        {"name": "Bread - Whole Wheat", "description": "Whole wheat sandwich bread", "upc": "012345678902", "default_storage_type": StorageType.PANTRY},
        {"name": "Chicken Breast", "description": "Boneless skinless chicken breast", "upc": "012345678903", "default_storage_type": StorageType.FREEZER},
        {"name": "Bananas", "description": "Fresh bananas", "upc": "012345678904", "default_storage_type": StorageType.COUNTER},
        {"name": "Rice - Jasmine", "description": "Jasmine white rice, 5lb bag", "upc": "012345678905", "default_storage_type": StorageType.PANTRY},
        {"name": "Eggs - Large", "description": "Large white eggs, dozen", "upc": "012345678906", "default_storage_type": StorageType.REFRIGERATOR},
        {"name": "Pasta - Spaghetti", "description": "Whole wheat spaghetti pasta", "upc": "012345678907", "default_storage_type": StorageType.PANTRY},
        {"name": "Tomato Sauce", "description": "Organic tomato pasta sauce", "upc": "012345678908", "default_storage_type": StorageType.PANTRY},
        {"name": "Frozen Peas", "description": "Frozen green peas", "upc": "012345678909", "default_storage_type": StorageType.FREEZER},
        {"name": "Olive Oil", "description": "Extra virgin olive oil", "upc": "012345678910", "default_storage_type": StorageType.PANTRY},
        {"name": "Greek Yogurt", "description": "Plain Greek yogurt, 32oz", "upc": "012345678911", "default_storage_type": StorageType.REFRIGERATOR},
        {"name": "Oatmeal", "description": "Quick cooking oats", "upc": "012345678912", "default_storage_type": StorageType.PANTRY},
    ]
    
    items = []
    print("Creating sample items...")
    
    for item_data in sample_items:
        # Check if item already exists
        existing_item = db.query(Item).filter(Item.upc == item_data["upc"]).first()
        if existing_item:
            items.append(existing_item)
            continue
            
        item = Item(
            name=item_data["name"],
            description=item_data["description"],
            upc=item_data["upc"],
            default_storage_type=item_data["default_storage_type"],
            created_by=admin_user.id,
            is_active=True
        )
        db.add(item)
        items.append(item)
    
    db.commit()
    print(f"✅ Created {len(sample_items)} sample items")
    return items


def create_sample_skus(db: Session, admin_user: User, items: list[Item], locations: list[Location]) -> list[SKU]:
    """Create sample inventory (SKUs) with realistic quantities and expiry dates"""
    
    skus = []
    print("Creating sample inventory (SKUs)...")
    
    # Define some realistic quantity ranges for different item types
    quantity_ranges = {
        "Whole Milk": (1, 2),
        "Bread - Whole Wheat": (1, 3),
        "Chicken Breast": (2, 6),
        "Bananas": (3, 8),
        "Rice - Jasmine": (1, 1),
        "Eggs - Large": (1, 2),
        "Pasta - Spaghetti": (2, 4),
        "Tomato Sauce": (3, 6),
        "Frozen Peas": (2, 4),
        "Olive Oil": (1, 2),
        "Greek Yogurt": (1, 3),
        "Oatmeal": (1, 2),
    }
    
    units = {
        "Whole Milk": "gallons",
        "Bread - Whole Wheat": "loaves", 
        "Chicken Breast": "lbs",
        "Bananas": "bunches",
        "Rice - Jasmine": "bags",
        "Eggs - Large": "dozens",
        "Pasta - Spaghetti": "boxes",
        "Tomato Sauce": "jars",
        "Frozen Peas": "bags",
        "Olive Oil": "bottles",
        "Greek Yogurt": "containers",
        "Oatmeal": "containers",
    }
    
    for item in items:
        # Find appropriate location based on storage type
        appropriate_location = None
        for location in locations:
            if location.storage_type == item.default_storage_type:
                appropriate_location = location
                break
        
        if not appropriate_location:
            # Fallback to pantry
            appropriate_location = next((loc for loc in locations if loc.storage_type == StorageType.PANTRY), locations[0])
        
        # Check if SKU already exists
        existing_sku = db.query(SKU).filter(
            SKU.item_id == item.id,
            SKU.location_id == appropriate_location.id
        ).first()
        
        if existing_sku:
            skus.append(existing_sku)
            continue
        
        # Generate realistic quantity
        quantity_range = quantity_ranges.get(item.name, (1, 5))
        quantity = random.randint(*quantity_range)
        
        # Generate expiry date (some items expire sooner than others)
        days_to_expiry = {
            "Whole Milk": random.randint(5, 14),
            "Bread - Whole Wheat": random.randint(3, 7),
            "Chicken Breast": random.randint(2, 5),
            "Bananas": random.randint(3, 8),
            "Eggs - Large": random.randint(14, 30),
            "Greek Yogurt": random.randint(7, 21),
        }
        
        expiry_date = None
        if item.name in days_to_expiry:
            expiry_date = datetime.now() + timedelta(days=days_to_expiry[item.name])
        
        sku = SKU(
            item_id=item.id,
            location_id=appropriate_location.id,
            quantity=quantity,
            unit=units.get(item.name, "units"),
            expiry_date=expiry_date,
            created_by=admin_user.id,
            is_active=True
        )
        
        db.add(sku)
        skus.append(sku)
    
    db.commit()
    print(f"✅ Created {len(skus)} sample inventory entries (SKUs)")
    return skus


def create_sample_alerts(db: Session, admin_user: User, skus: list[SKU]) -> None:
    """Create sample alerts for low stock and expiring items"""
    
    print("Creating sample alerts...")
    
    # Create a few low stock alerts
    low_stock_skus = [sku for sku in skus if sku.quantity <= 2][:3]
    
    for sku in low_stock_skus:
        alert = Alert(
            alert_type="low_stock",
            message=f"Low stock alert: {sku.item.name} in {sku.location.name} is running low ({sku.quantity} {sku.unit} remaining)",
            threshold_value=3.0,
            sku_id=sku.id,
            created_by=admin_user.id,
            is_active=True,
            is_acknowledged=False
        )
        db.add(alert)
    
    # Create expiry warnings for items expiring soon
    soon_expiring_skus = [sku for sku in skus if sku.expiry_date and sku.expiry_date <= datetime.now() + timedelta(days=3)][:2]
    
    for sku in soon_expiring_skus:
        alert = Alert(
            alert_type="expiry_warning",
            message=f"Expiry warning: {sku.item.name} in {sku.location.name} expires on {sku.expiry_date.strftime('%Y-%m-%d')}",
            sku_id=sku.id,
            created_by=admin_user.id,
            is_active=True,
            is_acknowledged=False
        )
        db.add(alert)
    
    db.commit()
    print(f"✅ Created sample alerts")


def main():
    """Main function to create demo data"""
    
    print("🎯 Stocky Backend - Demo Data Setup")
    print("=" * 40)
    
    # Verify database exists
    if not os.path.exists("data/stocky.db"):
        print("❌ Database not found! Please run 'alembic upgrade head' first.")
        sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get admin user
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin_user:
            print("❌ No admin user found! Please run scripts/initial_data.py first.")
            sys.exit(1)
        
        # Get locations
        locations = db.query(Location).all()
        if not locations:
            print("❌ No locations found! Please run scripts/initial_data.py first.")
            sys.exit(1)
        
        # Create demo data
        items = create_sample_items(db, admin_user)
        skus = create_sample_skus(db, admin_user, items, locations)
        create_sample_alerts(db, admin_user, skus)
        
        print("\n✅ Demo data setup completed successfully!")
        print(f"📦 Created inventory for {len(items)} different items")
        print(f"📍 Distributed across {len(locations)} locations")
        print("🚨 Added sample alerts for testing")
        print("\nYou can now explore the Stocky Backend with realistic test data!")
        
    except Exception as e:
        print(f"❌ Error during demo setup: {e}")
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
