#!/usr/bin/env python3
"""
Move postcode from contact.postcode to demographics.postcode.

The database stores postcodes in contact.postcode but the API model
expects them in demographics.postcode. This script migrates the data.
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
    print("Move Postcode to Demographics")
    print("=" * 70)
    print(f"Mode: {'LIVE - Will modify database' if live_mode else 'DRY RUN - No changes will be made'}")
    print()

    # Find all patients with contact.postcode
    patients_with_contact_postcode = list(db.patients.find(
        {'contact.postcode': {'$exists': True, '$ne': None, '$ne': ''}},
        {'patient_id': 1, 'contact.postcode': 1, 'demographics.postcode': 1}
    ))

    print(f"Found {len(patients_with_contact_postcode)} patients with contact.postcode")
    print()

    # Analyze what needs to be migrated
    updates_needed = []
    for patient in patients_with_contact_postcode:
        contact_postcode = patient.get('contact', {}).get('postcode')
        demographics_postcode = patient.get('demographics', {}).get('postcode')

        if contact_postcode and not demographics_postcode:
            updates_needed.append({
                'patient_id': patient['patient_id'],
                'postcode': contact_postcode
            })

    print(f"Patients needing migration: {len(updates_needed)}")
    print()

    if updates_needed:
        print("Sample migrations (first 10):")
        for update in updates_needed[:10]:
            print(f"  {update['patient_id']}: '{update['postcode']}'")

        if len(updates_needed) > 10:
            print(f"  ... and {len(updates_needed) - 10} more")
        print()

    # Apply updates if in live mode
    if live_mode and updates_needed:
        print("Applying migrations...")

        updated_count = 0
        for update in updates_needed:
            # Move postcode from contact to demographics
            result = db.patients.update_one(
                {'patient_id': update['patient_id']},
                {
                    '$set': {
                        'demographics.postcode': update['postcode'],
                        'updated_at': datetime.utcnow()
                    },
                    '$unset': {
                        'contact.postcode': ''
                    }
                }
            )
            if result.modified_count > 0:
                updated_count += 1

        print(f"✅ Migrated {updated_count} patients")

        # Clean up empty contact objects
        print("\nCleaning up empty contact objects...")
        cleanup_result = db.patients.update_many(
            {'contact': {'$eq': {}}},
            {'$unset': {'contact': ''}}
        )
        print(f"✅ Removed {cleanup_result.modified_count} empty contact objects")

        # Verify
        print("\nVerification:")
        with_demo_postcode = db.patients.count_documents({'demographics.postcode': {'$exists': True, '$ne': None, '$ne': ''}})
        with_contact_postcode = db.patients.count_documents({'contact.postcode': {'$exists': True, '$ne': None, '$ne': ''}})
        print(f"  Patients with demographics.postcode: {with_demo_postcode}")
        print(f"  Patients with contact.postcode: {with_contact_postcode}")

    elif not live_mode:
        print("⚠️  DRY RUN MODE - No changes made")
        print("Run with --live flag to apply changes")

    client.close()

if __name__ == '__main__':
    main()
