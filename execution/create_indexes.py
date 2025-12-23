#!/usr/bin/env python3
"""
Add database indexes for better query performance
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient


async def create_indexes():
    """Create indexes on frequently queried fields"""
    client = AsyncIOMotorClient('mongodb://admin:admin123@localhost:27017/surg_outcomes?authSource=admin')
    db = client.surg_outcomes
    
    print("Creating indexes for surgeries collection...")
    
    # Indexes for filtering
    await db.surgeries.create_index([("patient_id", 1)])
    print("✓ Index created: patient_id")
    
    await db.surgeries.create_index([("classification.urgency", 1)])
    print("✓ Index created: classification.urgency")
    
    await db.surgeries.create_index([("team.primary_surgeon", 1)])
    print("✓ Index created: team.primary_surgeon")
    
    await db.surgeries.create_index([("perioperative_timeline.surgery_date", -1)])
    print("✓ Index created: perioperative_timeline.surgery_date (descending)")
    
    # Compound index for common filter combinations
    await db.surgeries.create_index([
        ("perioperative_timeline.surgery_date", -1),
        ("classification.urgency", 1)
    ])
    print("✓ Compound index created: surgery_date + urgency")
    
    # Indexes for reports/analytics
    await db.surgeries.create_index([("postoperative_events.complications", 1)])
    print("✓ Index created: postoperative_events.complications")
    
    await db.surgeries.create_index([("outcomes.readmission_30day", 1)])
    print("✓ Index created: outcomes.readmission_30day")
    
    await db.surgeries.create_index([("outcomes.mortality_30day", 1)])
    print("✓ Index created: outcomes.mortality_30day")
    
    # Indexes for patient collection
    print("\nCreating indexes for patients collection...")
    await db.patients.create_index([("record_number", 1)], unique=True)
    print("✓ Unique index created: record_number")
    
    # Indexes for surgeons collection
    print("\nCreating indexes for surgeons collection...")
    await db.surgeons.create_index([("gmc_number", 1)], unique=True, sparse=True)
    print("✓ Unique sparse index created: gmc_number")
    
    await db.surgeons.create_index([("first_name", 1), ("surname", 1)])
    print("✓ Compound index created: first_name + surname")
    
    print("\n✅ All indexes created successfully!")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
