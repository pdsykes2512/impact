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

    # Check if search looks like MRN or NHS number (encrypted fields)
    search_encrypted_fields = False
    if search:
        clean_search = search.replace(" ", "").upper()
        # MRN patterns: 8+ digits, IW+6digits, or C+6digits+2alphanumeric
        is_mrn_pattern = (
            (clean_search.isdigit() and len(clean_search) >= 8) or
            (clean_search.startswith('IW') and len(clean_search) == 8 and clean_search[2:].isdigit()) or
            (clean_search.startswith('C') and len(clean_search) == 9 and clean_search[1:7].isdigit() and clean_search[7:9].isalnum())
        )
        if is_mrn_pattern:
            search_encrypted_fields = True

    # If searching encrypted fields, we need to fetch all, decrypt, and count
    if search and search_encrypted_fields:
        clean_search = search.replace(" ", "").lower()
        patients = await collection.find({}).to_list(length=None)
        
        count = 0
        for patient in patients:
            # Decrypt patient
            decrypted = decrypt_document(patient)
            # Check MRN or NHS number
            if decrypted.get("mrn") and clean_search in str(decrypted["mrn"]).replace(" ", "").lower():
                count += 1
            elif decrypted.get("nhs_number") and clean_search in str(decrypted["nhs_number"]).replace(" ", "").lower():
                count += 1
        
        return {"count": count}

    # Build query with search filter for non-encrypted fields
    query = {}
    if search:
        safe_search = sanitize_search_input(search)
        search_pattern = {"$regex": safe_search, "$options": "i"}
        query = {"patient_id": search_pattern}

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

    # Check if search looks like MRN or NHS number (encrypted fields that need special handling)
    search_encrypted_fields = False
    if search:
        # Remove spaces and check patterns
        clean_search = search.replace(" ", "").upper()
        # MRN patterns: 8+ digits, IW+6digits, or C+6digits+2alphanumeric
        # NHS number: 10 digits
        is_mrn_pattern = (
            (clean_search.isdigit() and len(clean_search) >= 8) or  # 8+ digits
            (clean_search.startswith('IW') and len(clean_search) == 8 and clean_search[2:].isdigit()) or  # IW+6digits
            (clean_search.startswith('C') and len(clean_search) == 9 and clean_search[1:7].isdigit() and clean_search[7:9].isalnum())  # C+6digits+2alphanumeric
        )
        if is_mrn_pattern:
            search_encrypted_fields = True
            print(f"Searching encrypted fields (MRN/NHS): {clean_search}")

    # Build query with search filter if provided
    query = {}
    if search and not search_encrypted_fields:
        # Sanitize search input to prevent NoSQL injection
        safe_search = sanitize_search_input(search)
        search_pattern = {"$regex": safe_search, "$options": "i"}
        
        # Only search non-encrypted fields (patient_id)
        query = {"patient_id": search_pattern}
        print(f"Search non-encrypted: {search} -> query: {query}")

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
    ]
    
    # If NOT searching encrypted fields, apply pagination in database
    if not search_encrypted_fields:
        pipeline.extend([
            {"$skip": skip},
            {"$limit": limit}
        ])

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

    # If searching encrypted fields, filter after decryption
    if search and search_encrypted_fields:
        clean_search = search.replace(" ", "").lower()
        filtered_patients = []
        for patient in decrypted_patients:
            # Check MRN
            if patient.get("mrn") and clean_search in str(patient["mrn"]).replace(" ", "").lower():
                filtered_patients.append(patient)
                continue
            # Check NHS number
            if patient.get("nhs_number") and clean_search in str(patient["nhs_number"]).replace(" ", "").lower():
                filtered_patients.append(patient)
                continue
        
        print(f"Filtered {len(filtered_patients)} patients from {len(decrypted_patients)} by encrypted field search")
        decrypted_patients = filtered_patients
        
        # Apply pagination after filtering
        decrypted_patients = decrypted_patients[skip:skip+limit]

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
