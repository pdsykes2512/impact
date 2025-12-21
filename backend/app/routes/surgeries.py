"""
Surgery API routes
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from ..models.surgery import Surgery, SurgeryCreate, SurgeryUpdate
from ..database import get_surgeries_collection, get_patients_collection


router = APIRouter(prefix="/api/surgeries", tags=["surgeries"])


@router.post("/", response_model=Surgery, status_code=status.HTTP_201_CREATED)
async def create_surgery(surgery: SurgeryCreate):
    """Create a new surgery record"""
    collection = await get_surgeries_collection()
    patients_collection = await get_patients_collection()
    
    # Verify patient exists
    patient = await patients_collection.find_one({"patient_id": surgery.patient_id})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient {surgery.patient_id} not found"
        )
    
    # Check if surgery_id already exists
    existing = await collection.find_one({"surgery_id": surgery.surgery_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Surgery with ID {surgery.surgery_id} already exists"
        )
    
    # Insert surgery
    surgery_dict = surgery.model_dump()
    surgery_dict["created_at"] = datetime.utcnow()
    surgery_dict["updated_at"] = datetime.utcnow()
    
    result = await collection.insert_one(surgery_dict)
    
    # Retrieve and return created surgery
    created_surgery = await collection.find_one({"_id": result.inserted_id})
    return Surgery(**created_surgery)


@router.get("/", response_model=List[Surgery])
async def list_surgeries(
    skip: int = 0,
    limit: int = 100,
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    procedure_type: Optional[str] = Query(None, description="Filter by procedure type")
):
    """List all surgeries with pagination and optional filters"""
    collection = await get_surgeries_collection()
    
    # Build query filters
    query = {}
    if patient_id:
        query["patient_id"] = patient_id
    if procedure_type:
        query["procedure.type"] = procedure_type
    
    cursor = collection.find(query).skip(skip).limit(limit)
    surgeries = await cursor.to_list(length=limit)
    
    return [Surgery(**surgery) for surgery in surgeries]


@router.get("/{surgery_id}", response_model=Surgery)
async def get_surgery(surgery_id: str):
    """Get a specific surgery by surgery_id"""
    collection = await get_surgeries_collection()
    
    surgery = await collection.find_one({"surgery_id": surgery_id})
    if not surgery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surgery {surgery_id} not found"
        )
    
    return Surgery(**surgery)


@router.put("/{surgery_id}", response_model=Surgery)
async def update_surgery(surgery_id: str, surgery_update: SurgeryUpdate):
    """Update a surgery record"""
    collection = await get_surgeries_collection()
    
    # Check if surgery exists
    existing = await collection.find_one({"surgery_id": surgery_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surgery {surgery_id} not found"
        )
    
    # Update only provided fields
    update_data = surgery_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await collection.update_one(
            {"surgery_id": surgery_id},
            {"$set": update_data}
        )
    
    # Return updated surgery
    updated_surgery = await collection.find_one({"surgery_id": surgery_id})
    return Surgery(**updated_surgery)


@router.delete("/{surgery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_surgery(surgery_id: str):
    """Delete a surgery record"""
    collection = await get_surgeries_collection()
    
    result = await collection.delete_one({"surgery_id": surgery_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surgery {surgery_id} not found"
        )
    
    return None
