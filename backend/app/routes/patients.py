"""
Patient API routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import re

from ..models.patient import Patient, PatientCreate, PatientUpdate
from ..database import get_patients_collection, get_episodes_collection
from ..utils.encryption import encrypt_document, decrypt_document
from ..auth import get_current_user, require_data_entry_or_higher, require_admin


router = APIRouter(prefix="/api/patients", tags=["patients"])


def sanitize_search_input(search: str) -> str:
    """
    Sanitize search input to prevent NoSQL injection via regex

    Args:
        search: Raw search string from user

    Returns:
        Escaped search string safe for regex use
    """
    # Remove spaces and escape regex special characters
    return re.escape(search.replace(" ", ""))


@router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    current_user: dict = Depends(require_data_entry_or_higher)
):
    """Create a new patient (requires data_entry role or higher)"""
    collection = await get_patients_collection()

    # Check if record_number already exists
    existing = await collection.find_one({"record_number": patient.record_number})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with record number {patient.record_number} already exists"
        )

    # Insert patient with encrypted sensitive fields
    patient_dict = patient.model_dump()
    patient_dict["created_at"] = datetime.utcnow()
    patient_dict["updated_at"] = datetime.utcnow()
    patient_dict["created_by"] = current_user["username"]
    patient_dict["updated_by"] = current_user["username"]

    # Encrypt sensitive fields before storing
    encrypted_patient = encrypt_document(patient_dict)

    result = await collection.insert_one(encrypted_patient)

    # Retrieve and return created patient (decrypted for response)
    created_patient = await collection.find_one({"_id": result.inserted_id})
    created_patient["_id"] = str(created_patient["_id"])
    # Decrypt before returning
    decrypted_patient = decrypt_document(created_patient)
    return Patient(**decrypted_patient)


@router.get("/count")
async def count_patients(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get total count of patients with optional search filter (requires authentication)"""
    collection = await get_patients_collection()

    # Build query with search filter if provided
    query = {}
    if search:
        # Sanitize search input to prevent NoSQL injection
        safe_search = sanitize_search_input(search)
        search_pattern = {"$regex": safe_search, "$options": "i"}
        query = {
            "$or": [
                {"patient_id": search_pattern},
                {"mrn": search_pattern},
                {"nhs_number": search_pattern}
            ]
        }

    total = await collection.count_documents(query)
    return {"count": total}


@router.get("/", response_model=List[Patient])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all patients with pagination and optional search, sorted by most recent episode referral date (requires authentication)"""
    collection = await get_patients_collection()
    episodes_collection = await get_episodes_collection()

    # Build query with search filter if provided
    query = {}
    if search:
        # Sanitize search input to prevent NoSQL injection
        safe_search = sanitize_search_input(search)
        search_pattern = {"$regex": safe_search, "$options": "i"}
        query = {
            "$or": [
                {"patient_id": search_pattern},
                {"mrn": search_pattern},
                {"nhs_number": search_pattern}
            ]
        }

    # Use aggregation to join with episodes and get most recent referral date
    pipeline = [
        {"$match": query},
        # Lookup episodes for each patient
        {
            "$lookup": {
                "from": "episodes",
                "localField": "patient_id",
                "foreignField": "patient_id",
                "as": "episodes"
            }
        },
        # Add fields for episode count and most recent referral date
        {
            "$addFields": {
                "episode_count": {"$size": "$episodes"},
                "most_recent_referral": {
                    "$max": {
                        "$map": {
                            "input": "$episodes",
                            "as": "ep",
                            "in": "$$ep.referral_date"
                        }
                    }
                }
            }
        },
        # Sort by most recent referral date (nulls last), then by patient_id
        {"$sort": {"most_recent_referral": -1, "patient_id": 1}},
        # Remove the episodes array from output
        {"$project": {"episodes": 0}},
        # Pagination
        {"$skip": skip},
        {"$limit": limit}
    ]

    patients = await collection.aggregate(pipeline).to_list(length=None)

    # Convert ObjectId to string, decrypt sensitive fields, and handle datetime conversion
    decrypted_patients = []
    for patient in patients:
        patient["_id"] = str(patient["_id"])
        # Remove most_recent_referral from output (only used for sorting)
        patient.pop("most_recent_referral", None)

        # Decrypt sensitive fields
        patient = decrypt_document(patient)

        # Convert datetime objects to ISO format strings for Pydantic validation
        if patient.get("demographics"):
            demo = patient["demographics"]
            # Convert date_of_birth if it's a datetime object
            if demo.get("date_of_birth") and hasattr(demo["date_of_birth"], "isoformat"):
                demo["date_of_birth"] = demo["date_of_birth"].isoformat()
            # Convert deceased_date if it's a datetime object
            if demo.get("deceased_date") and hasattr(demo["deceased_date"], "isoformat"):
                demo["deceased_date"] = demo["deceased_date"].isoformat()

        decrypted_patients.append(patient)

    return [Patient(**patient) for patient in decrypted_patients]


@router.get("/{patient_id}", response_model=Patient)
async def get_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific patient by patient_id (requires authentication)"""
    collection = await get_patients_collection()

    patient = await collection.find_one({"patient_id": patient_id})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    patient["_id"] = str(patient["_id"])
    # Decrypt sensitive fields before returning
    patient = decrypt_document(patient)
    return Patient(**patient)


@router.put("/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    current_user: dict = Depends(require_data_entry_or_higher)
):
    """Update a patient (requires data_entry role or higher)"""
    collection = await get_patients_collection()

    # Check if patient exists
    existing = await collection.find_one({"patient_id": patient_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    # Update only provided fields
    update_data = patient_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by"] = current_user["username"]

        # Encrypt sensitive fields before updating
        encrypted_update = encrypt_document(update_data)

        await collection.update_one(
            {"patient_id": patient_id},
            {"$set": encrypted_update}
        )

    # Return updated patient (decrypted)
    updated_patient = await collection.find_one({"patient_id": patient_id})
    updated_patient["_id"] = str(updated_patient["_id"])
    # Decrypt before returning
    decrypted_patient = decrypt_document(updated_patient)
    return Patient(**decrypted_patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a patient (requires admin role)"""
    collection = await get_patients_collection()

    result = await collection.delete_one({"patient_id": patient_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    return None
