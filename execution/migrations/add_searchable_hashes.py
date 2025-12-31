"""
Migration: Add Searchable Hash Fields to Patient Records

Adds nhs_number_hash and mrn_hash fields to all existing patient documents
to enable fast O(log n) searches on encrypted NHS numbers and MRNs.

This migration:
1. Generates SHA-256 hashes for existing NHS numbers and MRNs
2. Adds hash fields to patient documents
3. Enables indexed hash-based lookups instead of full collection scans

Performance impact: Reduces encrypted field searches from O(n) to O(log n)
Expected speedup: ~100x for 8,000 patients (seconds → milliseconds)

Usage:
    python execution/migrations/add_searchable_hashes.py
"""

import sys
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import encryption utilities
from backend.app.utils.encryption import generate_search_hash, is_encrypted, decrypt_field

def migrate_patient_hashes(dry_run=False):
    """
    Add searchable hash fields to patient documents

    Args:
        dry_run: If True, only count documents that need migration
    """
    # Connect to MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    mongodb_db_name = os.getenv('MONGODB_DB_NAME', 'impact')

    print(f"Connecting to MongoDB: {mongodb_uri}")
    client = MongoClient(mongodb_uri)
    db = client[mongodb_db_name]
    collection = db.patients

    # Count total patients
    total_patients = collection.count_documents({})
    print(f"\nTotal patients in database: {total_patients}")

    # Find patients missing hash fields
    missing_nhs_hash = collection.count_documents({
        "nhs_number": {"$exists": True},
        "nhs_number_hash": {"$exists": False}
    })

    missing_mrn_hash = collection.count_documents({
        "mrn": {"$exists": True},
        "mrn_hash": {"$exists": False}
    })

    print(f"Patients missing nhs_number_hash: {missing_nhs_hash}")
    print(f"Patients missing mrn_hash: {missing_mrn_hash}")

    if dry_run:
        print("\n[DRY RUN MODE] - No changes will be made")
        return

    # Migrate NHS number hashes
    print("\n" + "="*60)
    print("MIGRATING NHS NUMBER HASHES")
    print("="*60)

    nhs_patients = collection.find({
        "nhs_number": {"$exists": True},
        "nhs_number_hash": {"$exists": False}
    })

    nhs_updated = 0
    nhs_skipped = 0

    for patient in nhs_patients:
        nhs_number = patient.get("nhs_number")

        if not nhs_number or nhs_number == "":
            nhs_skipped += 1
            continue

        # Decrypt if encrypted
        if is_encrypted(nhs_number):
            nhs_number = decrypt_field('nhs_number', nhs_number)

        # Generate hash
        nhs_hash = generate_search_hash('nhs_number', nhs_number)

        if nhs_hash:
            collection.update_one(
                {"_id": patient["_id"]},
                {"$set": {"nhs_number_hash": nhs_hash}}
            )
            nhs_updated += 1

            if nhs_updated % 100 == 0:
                print(f"  Progress: {nhs_updated} NHS hashes added...")
        else:
            nhs_skipped += 1

    print(f"✅ NHS number hashes added: {nhs_updated}")
    print(f"⏭️  Skipped (empty/invalid): {nhs_skipped}")

    # Migrate MRN hashes
    print("\n" + "="*60)
    print("MIGRATING MRN HASHES")
    print("="*60)

    mrn_patients = collection.find({
        "mrn": {"$exists": True},
        "mrn_hash": {"$exists": False}
    })

    mrn_updated = 0
    mrn_skipped = 0

    for patient in mrn_patients:
        mrn = patient.get("mrn")

        if not mrn or mrn == "":
            mrn_skipped += 1
            continue

        # Decrypt if encrypted
        if is_encrypted(mrn):
            mrn = decrypt_field('mrn', mrn)

        # Generate hash
        mrn_hash = generate_search_hash('mrn', mrn)

        if mrn_hash:
            collection.update_one(
                {"_id": patient["_id"]},
                {"$set": {"mrn_hash": mrn_hash}}
            )
            mrn_updated += 1

            if mrn_updated % 100 == 0:
                print(f"  Progress: {mrn_updated} MRN hashes added...")
        else:
            mrn_skipped += 1

    print(f"✅ MRN hashes added: {mrn_updated}")
    print(f"⏭️  Skipped (empty/invalid): {mrn_skipped}")

    # Summary
    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)
    print(f"Total patients: {total_patients}")
    print(f"NHS number hashes added: {nhs_updated}")
    print(f"MRN hashes added: {mrn_updated}")
    print(f"Total hash fields added: {nhs_updated + mrn_updated}")
    print("\n✨ Encrypted field searches will now use O(log n) indexed lookups!")

    # Verify indexes exist
    print("\n" + "="*60)
    print("VERIFYING INDEXES")
    print("="*60)

    indexes = list(collection.list_indexes())
    hash_indexes = [idx for idx in indexes if 'hash' in idx['name']]

    if hash_indexes:
        print("✅ Hash indexes found:")
        for idx in hash_indexes:
            print(f"  - {idx['name']}: {idx['key']}")
    else:
        print("⚠️  WARNING: No hash indexes found!")
        print("   Run 'sudo systemctl restart surg-db-backend' to create indexes")

    client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add searchable hash fields to patient records")
    parser.add_argument('--dry-run', action='store_true', help='Count documents without making changes')
    args = parser.parse_args()

    print("="*60)
    print("SEARCHABLE HASH MIGRATION")
    print("="*60)
    print("\nThis migration adds hash fields for fast encrypted field searches:")
    print("  - nhs_number_hash: SHA-256 hash of NHS number")
    print("  - mrn_hash: SHA-256 hash of MRN")
    print("\nBenefits:")
    print("  - O(log n) indexed lookups instead of O(n) full scans")
    print("  - ~100x faster searches on 8,000 patients")
    print("  - No decryption overhead during search")

    if args.dry_run:
        print("\n🔍 Running in DRY RUN mode - no changes will be made\n")
    else:
        print("\n⚠️  This will modify patient documents in the database")
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            sys.exit(0)
        print()

    migrate_patient_hashes(dry_run=args.dry_run)
