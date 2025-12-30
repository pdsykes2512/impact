#!/usr/bin/env python3
"""
Copy height, weight, and BMI from patient demographics to treatment documents.

These measurements can vary over time, so they should be recorded with each
treatment rather than stored once in the patient's demographics.
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

def main():
    # Check for --live flag
    live_mode = '--live' in sys.argv

    # Load environment
    load_dotenv('/etc/impact/secrets.env')
    load_dotenv('.env')

    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['impact']

    print("=" * 70)
    print("Copy Vitals (Height, Weight, BMI) to Treatments")
    print("=" * 70)
    print(f"Mode: {'LIVE - Will modify database' if live_mode else 'DRY RUN - No changes will be made'}")
    print()

    # Get all patients with demographics
    patients = list(db.patients.find(
        {},
        {'patient_id': 1, 'demographics.height_cm': 1, 'demographics.weight_kg': 1, 'demographics.bmi': 1}
    ))

    print(f"Found {len(patients)} patients")
    print()

    # Track statistics
    stats = {
        'patients_processed': 0,
        'treatments_updated': 0,
        'patients_with_vitals': 0,
        'treatments_with_vitals': 0
    }

    updates_to_apply = []

    for patient in patients:
        patient_id = patient['patient_id']
        demographics = patient.get('demographics', {})

        height_cm = demographics.get('height_cm')
        weight_kg = demographics.get('weight_kg')
        bmi = demographics.get('bmi')

        # Only process if patient has at least one vital measurement
        if not any([height_cm, weight_kg, bmi]):
            continue

        stats['patients_with_vitals'] += 1

        # Find all treatments for this patient
        treatments = list(db.treatments.find({'patient_id': patient_id}, {'treatment_id': 1}))

        if treatments:
            for treatment in treatments:
                updates_to_apply.append({
                    'treatment_id': treatment['treatment_id'],
                    'patient_id': patient_id,
                    'height_cm': height_cm,
                    'weight_kg': weight_kg,
                    'bmi': bmi
                })
                stats['treatments_with_vitals'] += 1

        stats['patients_processed'] += 1

    print(f"Analysis:")
    print(f"  Patients with vitals: {stats['patients_with_vitals']}")
    print(f"  Treatments to update: {len(updates_to_apply)}")
    print()

    if updates_to_apply:
        print(f"Sample updates (first 10):")
        for update in updates_to_apply[:10]:
            vitals = []
            if update['height_cm']:
                vitals.append(f"height={update['height_cm']}cm")
            if update['weight_kg']:
                vitals.append(f"weight={update['weight_kg']}kg")
            if update['bmi']:
                vitals.append(f"BMI={update['bmi']}")
            vitals_str = ', '.join(vitals) if vitals else 'none'
            print(f"  {update['treatment_id']} (patient {update['patient_id']}): {vitals_str}")

        if len(updates_to_apply) > 10:
            print(f"  ... and {len(updates_to_apply) - 10} more")
        print()

    # Apply updates if in live mode
    if live_mode and updates_to_apply:
        print("Applying updates...")

        for update in updates_to_apply:
            update_fields = {
                'updated_at': datetime.utcnow()
            }

            if update['height_cm'] is not None:
                update_fields['height_cm'] = update['height_cm']
            if update['weight_kg'] is not None:
                update_fields['weight_kg'] = update['weight_kg']
            if update['bmi'] is not None:
                update_fields['bmi'] = update['bmi']

            result = db.treatments.update_one(
                {'treatment_id': update['treatment_id']},
                {'$set': update_fields}
            )

            if result.modified_count > 0:
                stats['treatments_updated'] += 1

        print(f"✅ Updated {stats['treatments_updated']} treatments")

        # Verify
        print("\nVerification:")
        with_bmi = db.treatments.count_documents({'bmi': {'$exists': True, '$ne': None}})
        with_weight = db.treatments.count_documents({'weight_kg': {'$exists': True, '$ne': None}})
        with_height = db.treatments.count_documents({'height_cm': {'$exists': True, '$ne': None}})
        print(f"  Treatments with BMI: {with_bmi}")
        print(f"  Treatments with weight_kg: {with_weight}")
        print(f"  Treatments with height_cm: {with_height}")

    elif not live_mode:
        print("⚠️  DRY RUN MODE - No changes made")
        print("Run with --live flag to apply changes")

    client.close()

if __name__ == '__main__':
    main()
