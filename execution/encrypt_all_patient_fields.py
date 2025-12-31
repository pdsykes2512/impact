#!/usr/bin/env python3
"""
Encrypt all unencrypted fields that should be encrypted according to ENCRYPTED_FIELDS
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load environment including secrets
from dotenv import load_dotenv
load_dotenv('/root/impact/.env')
load_dotenv('/etc/impact/secrets.env')

from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.encryption import encrypt_field, is_encrypted, ENCRYPTED_FIELDS
import asyncio

async def encrypt_patient_fields():
    """Encrypt unencrypted fields in all patient records"""
    # Connect to MongoDB with authentication
    mongodb_uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('MONGODB_DB_NAME', 'impact')
    
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[db_name]
    collection = db['patients']
    
    print(f"Connected to MongoDB: {db_name}")
    
    # Find all patients
    patients = await collection.find({}).to_list(length=None)
    print(f"Found {len(patients)} patients to check\n")
    
    encrypted_count = 0
    fields_encrypted = 0
    
    # Get list of encrypted fields that apply to patients
    patient_encrypted_fields = ['mrn', 'nhs_number', 'hospital_number']
    
    # Also check demographics fields
    demographics_encrypted_fields = ['first_name', 'last_name', 'date_of_birth', 'deceased_date', 'postcode']
    
    for patient in patients:
        updates = {}
        patient_id = patient.get('patient_id', 'unknown')
        
        # Check top-level fields
        for field in patient_encrypted_fields:
            value = patient.get(field)
            if value is not None and not is_encrypted(value):
                updates[field] = encrypt_field(field, str(value))
                print(f"  Patient {patient_id}: Encrypting {field}")
                fields_encrypted += 1
        
        # Check demographics fields
        demographics = patient.get('demographics', {})
        if demographics:
            demo_updates = {}
            for field in demographics_encrypted_fields:
                value = demographics.get(field)
                if value is not None and not is_encrypted(value):
                    demo_updates[field] = encrypt_field(field, str(value))
                    print(f"  Patient {patient_id}: Encrypting demographics.{field}")
                    fields_encrypted += 1
            
            if demo_updates:
                # Update demographics as a nested document
                for field, encrypted_value in demo_updates.items():
                    updates[f'demographics.{field}'] = encrypted_value
        
        # Apply updates if any
        if updates:
            await collection.update_one(
                {'_id': patient['_id']},
                {'$set': updates}
            )
            encrypted_count += 1
    
    print(f"\n✅ Updated {encrypted_count} patients")
    print(f"🔒 Encrypted {fields_encrypted} fields")
    print(f"📊 Total patients checked: {len(patients)}")

if __name__ == "__main__":
    asyncio.run(encrypt_patient_fields())
