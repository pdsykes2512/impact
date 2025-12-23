"""
Episode API routes
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from ..models.surgery import Surgery, SurgeryCreate, SurgeryUpdate
from ..database import (
    get_episodes_collection,
    get_treatments_collection,
    get_tumours_collection,
    get_patients_collection
)


router = APIRouter(prefix="/api/episodes", tags=["episodes"])


@router.post("/", response_model=Surgery, status_code=status.HTTP_201_CREATED)
async def create_episode(surgery: SurgeryCreate):
    """Create a new episode record"""
    try:
        collection = await get_episodes_collection()
        patients_collection = await get_patients_collection()
        
        # Verify patient exists (patient_id is the record_number/MRN)
        patient = await patients_collection.find_one({"record_number": surgery.patient_id})
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patient with MRN {surgery.patient_id} not found"
            )
        
        # Check if episode_id already exists
        existing = await collection.find_one({"episode_id": surgery.surgery_id})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Episode with ID {surgery.surgery_id} already exists"
            )
        
        # Insert episode
        surgery_dict = surgery.model_dump()
        # Map surgery_id to episode_id for the new structure
        surgery_dict["episode_id"] = surgery_dict.get("surgery_id")
        
        result = await collection.insert_one(surgery_dict)
        
        # Retrieve and return created episode
        created_episode = await collection.find_one({"_id": result.inserted_id})
        if created_episode:
            created_episode["_id"] = str(created_episode["_id"])
            created_episode["treatments"] = []
            created_episode["tumours"] = []
        return Surgery(**created_episode)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error creating episode: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create episode: {str(e)}"
        )


@router.get("/", response_model=List[Surgery])
async def list_episodes(
    skip: int = 0,
    limit: int = 100,
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    urgency: Optional[str] = Query(None, description="Filter by urgency (elective/emergency/urgent)"),
    primary_surgeon: Optional[str] = Query(None, description="Filter by primary surgeon"),
    start_date: Optional[str] = Query(None, description="Filter surgeries after this date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter surgeries before this date (YYYY-MM-DD)")
):
    """List all episodes with pagination and optional filters"""
    collection = await get_episodes_collection()
    
    # Build query filters
    query = {}
    if patient_id:
        query["patient_id"] = patient_id
    if urgency:
        query["classification.urgency"] = urgency
    if primary_surgeon:
        query["team.primary_surgeon"] = primary_surgeon
    
    # Date range filtering
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_query["$lte"] = datetime.fromisoformat(end_date)
        query["perioperative_timeline.surgery_date"] = date_query
    
    cursor = collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
    episodes = await cursor.to_list(length=limit)
    
    # Convert ObjectIds to strings and add empty treatments/tumours arrays
    for episode in episodes:
        episode["_id"] = str(episode["_id"])
        episode["treatments"] = []
        episode["tumours"] = []
    
    return [Surgery(**episode) for episode in episodes]


@router.get("/{surgery_id}", response_model=Surgery)
async def get_episode(surgery_id: str):
    """Get a specific episode by episode_id with treatments and tumours"""
    episodes_col = await get_episodes_collection()
    treatments_col = await get_treatments_collection()
    tumours_col = await get_tumours_collection()
    
    # Find episode by episode_id field
    episode = await episodes_col.find_one({"episode_id": surgery_id})
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {surgery_id} not found"
        )
    
    # Load treatments for this episode
    treatments = await treatments_col.find({"episode_id": surgery_id}).to_list(length=None)
    print(f"DEBUG: Found {len(treatments)} treatments for episode {surgery_id}")
    for t in treatments:
        t["_id"] = str(t["_id"])
    
    # Load tumours for this episode
    tumours = await tumours_col.find({"episode_id": surgery_id}).to_list(length=None)
    print(f"DEBUG: Found {len(tumours)} tumours for episode {surgery_id}")
    for tu in tumours:
        tu["_id"] = str(tu["_id"])
    
    # Add treatments and tumours to episode
    episode["treatments"] = treatments
    episode["tumours"] = tumours
    episode["_id"] = str(episode["_id"])
    
    print(f"DEBUG: Episode dict has treatments: {len(episode.get('treatments', []))}, tumours: {len(episode.get('tumours', []))}")
    
    return Surgery(**episode)


@router.put("/{surgery_id}", response_model=Surgery)
async def update_episode(surgery_id: str, surgery_update: SurgeryUpdate):
    """Update an episode record"""
    collection = await get_episodes_collection()
    
    # Check if episode exists (using episode_id field)
    existing = await collection.find_one({"episode_id": surgery_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {surgery_id} not found"
        )
    
    # Update only provided fields
    update_data = surgery_update.model_dump(exclude_unset=True)
    if update_data:
        # Update last modified timestamp
        update_data["last_modified_at"] = datetime.utcnow()
        update_data["last_modified_by"] = "system"  # TODO: Replace with actual user from auth
        
        await collection.update_one(
            {"episode_id": surgery_id},
            {"$set": update_data}
        )
    
    # Return updated episode with treatments and tumours
    treatments_col = await get_treatments_collection()
    tumours_col = await get_tumours_collection()
    
    updated_episode = await collection.find_one({"episode_id": surgery_id})
    treatments = await treatments_col.find({"episode_id": surgery_id}).to_list(length=None)
    tumours = await tumours_col.find({"episode_id": surgery_id}).to_list(length=None)
    
    for t in treatments:
        t["_id"] = str(t["_id"])
    for tu in tumours:
        tu["_id"] = str(tu["_id"])
    
    updated_episode["_id"] = str(updated_episode["_id"])
    updated_episode["treatments"] = treatments
    updated_episode["tumours"] = tumours
    
    return Surgery(**updated_episode)


@router.delete("/{surgery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(surgery_id: str):
    """Delete an episode record"""
    collection = await get_episodes_collection()
    
    result = await collection.delete_one({"episode_id": surgery_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {surgery_id} not found"
        )
    
    return None
