#!/usr/bin/env python3
"""
Fix MRN and NHS Number fields that are stored as numbers instead of strings
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import Database, get_patients_collection
import asyncio

async def fix_patient_field_types():
    """Convert numeric mrn and nhs_number fields to strings"""
    await Database.connect_db()
    collection = await get_patients_collection()
    
    # Find all patients
    patients = await collection.find({}).to_list(length=None)
    
    fixed_count = 0
    
    for patient in patients:
        updates = {}
        
        # Check if mrn is a number
        if patient.get('mrn') is not None and isinstance(patient['mrn'], (int, float)):
            updates['mrn'] = str(int(patient['mrn']))
            print(f"Patient {patient.get('patient_id')}: Converting MRN from {type(patient['mrn']).__name__} to string: {updates['mrn']}")
        
        # Check if nhs_number is a number
        if patient.get('nhs_number') is not None and isinstance(patient['nhs_number'], (int, float)):
            updates['nhs_number'] = str(int(patient['nhs_number']))
            print(f"Patient {patient.get('patient_id')}: Converting NHS Number from {type(patient['nhs_number']).__name__} to string: {updates['nhs_number']}")
        
        # Apply updates if any
        if updates:
            await collection.update_one(
                {'_id': patient['_id']},
                {'$set': updates}
            )
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} patients with numeric MRN/NHS Number fields")
    
    # Show a sample of fixed patient
    if fixed_count > 0:
        sample = await collection.find_one({'patient_id': 'BDC741'})
        if sample:
            print(f"\nPatient BDC741 after fix:")
            print(f"  MRN: {sample.get('mrn')} (type: {type(sample.get('mrn')).__name__})")
            print(f"  NHS Number: {sample.get('nhs_number')} (type: {type(sample.get('nhs_number')).__name__})")

if __name__ == "__main__":
    asyncio.run(fix_patient_field_types())
