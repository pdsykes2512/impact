#!/usr/bin/env python3
"""
Migrate Patient Data to Encrypted Fields

Encrypts sensitive fields in the patients collection:
- nhs_number
- mrn
- postcode
- date_of_birth

This script is idempotent - it will only encrypt fields that are not already encrypted.

Usage:
    python migrate_to_encrypted_fields.py [--dry-run] [--batch-size 100]
"""

import os
import sys
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
import argparse

# Add backend to path to import encryption module
backend_path = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.utils.encryption import (
    encrypt_field,
    decrypt_field,
    is_encrypted,
    ENCRYPTED_FIELDS,
    ENCRYPTION_PREFIX
)

# Load environment
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('MONGODB_DB_NAME', 'surgical_outcomes')


def analyze_collection(collection, field_name):
    """Analyze how many documents need encryption"""
    total = collection.count_documents({})
    encrypted = collection.count_documents({
        field_name: {'$regex': f'^{ENCRYPTION_PREFIX}'}
    })
    unencrypted = collection.count_documents({
        field_name: {
            '$exists': True,
            '$ne': None,
            '$ne': '',
            '$not': {'$regex': f'^{ENCRYPTION_PREFIX}'}
        }
    })
    missing = total - encrypted - unencrypted

    return {
        'total': total,
        'encrypted': encrypted,
        'unencrypted': unencrypted,
        'missing': missing
    }


def migrate_field(collection, field_name, batch_size=100, dry_run=False):
    """Migrate a single field to encrypted format"""
    print(f"\n📊 Analyzing {field_name}...")
    stats = analyze_collection(collection, field_name)

    print(f"  Total documents: {stats['total']}")
    print(f"  Already encrypted: {stats['encrypted']}")
    print(f"  Need encryption: {stats['unencrypted']}")
    print(f"  Missing/null: {stats['missing']}")

    if stats['unencrypted'] == 0:
        print(f"  ✓ All {field_name} fields already encrypted")
        return 0

    if dry_run:
        print(f"  [DRY RUN] Would encrypt {stats['unencrypted']} documents")
        return stats['unencrypted']

    # Find documents that need encryption
    query = {
        field_name: {
            '$exists': True,
            '$ne': None,
            '$ne': '',
            '$not': {'$regex': f'^{ENCRYPTION_PREFIX}'}
        }
    }

    print(f"\n🔒 Encrypting {stats['unencrypted']} documents...")

    processed = 0
    errors = 0
    cursor = collection.find(query).batch_size(batch_size)

    for doc in cursor:
        try:
            if field_name in doc and doc[field_name]:
                # Encrypt the value
                plaintext = doc[field_name]
                encrypted_value = encrypt_field(field_name, plaintext)

                # Update in database
                collection.update_one(
                    {'_id': doc['_id']},
                    {'$set': {field_name: encrypted_value}}
                )

                processed += 1

                # Progress indicator
                if processed % batch_size == 0:
                    print(f"  Progress: {processed}/{stats['unencrypted']} documents encrypted")

        except Exception as e:
            print(f"  ❌ Error encrypting document {doc.get('_id')}: {e}")
            errors += 1

    print(f"  ✓ Encrypted {processed} documents")
    if errors > 0:
        print(f"  ⚠️  {errors} errors encountered")

    return processed


def verify_encryption(collection, field_name, sample_size=10):
    """Verify that encryption/decryption works correctly"""
    print(f"\n🔍 Verifying {field_name} encryption...")

    # Get sample of encrypted documents
    query = {field_name: {'$regex': f'^{ENCRYPTION_PREFIX}'}}
    sample = list(collection.find(query).limit(sample_size))

    if not sample:
        print(f"  ⚠️  No encrypted documents found for {field_name}")
        return False

    print(f"  Testing {len(sample)} encrypted documents...")

    for doc in sample:
        encrypted_value = doc[field_name]

        # Try to decrypt
        try:
            decrypted = decrypt_field(field_name, encrypted_value)

            # Verify it's different from encrypted value
            if decrypted == encrypted_value:
                print(f"  ❌ Decryption failed for {doc.get('_id')}: value unchanged")
                return False

            # Verify it doesn't have encryption prefix
            if decrypted.startswith(ENCRYPTION_PREFIX):
                print(f"  ❌ Decryption failed for {doc.get('_id')}: still has prefix")
                return False

        except Exception as e:
            print(f"  ❌ Decryption error for {doc.get('_id')}: {e}")
            return False

    print(f"  ✓ All {len(sample)} samples decrypted successfully")
    return True


def main():
    parser = argparse.ArgumentParser(description='Migrate patient data to encrypted fields')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be encrypted without making changes')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of documents to process at once (default: 100)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify encryption, do not migrate')
    args = parser.parse_args()

    print("=" * 60)
    print("Field-Level Encryption Migration")
    print("=" * 60)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    # Connect to MongoDB
    print(f"\n🔌 Connecting to MongoDB...")
    try:
        client = MongoClient(MONGODB_URI)
        client.admin.command('ping')
        print(f"✓ Connected to {DB_NAME}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    db = client[DB_NAME]
    patients = db.patients

    # Verify collection exists
    total_patients = patients.count_documents({})
    print(f"✓ Found {total_patients} patients")

    if total_patients == 0:
        print("⚠️  No patients found in database")
        sys.exit(0)

    # Verify only mode
    if args.verify_only:
        print("\n🔍 Verification Mode")
        all_verified = True
        for field in ENCRYPTED_FIELDS:
            if not verify_encryption(patients, field):
                all_verified = False

        if all_verified:
            print("\n✅ All encrypted fields verified successfully!")
            sys.exit(0)
        else:
            print("\n❌ Verification failed")
            sys.exit(1)

    # Migrate each sensitive field
    print("\n📋 Fields to encrypt:")
    for field in ENCRYPTED_FIELDS:
        print(f"  - {field}")

    total_encrypted = 0

    for field in ENCRYPTED_FIELDS:
        encrypted = migrate_field(patients, field, args.batch_size, args.dry_run)
        total_encrypted += encrypted

    # Verification
    if not args.dry_run and total_encrypted > 0:
        print("\n" + "=" * 60)
        print("Verifying Encryption")
        print("=" * 60)

        all_verified = True
        for field in ENCRYPTED_FIELDS:
            if not verify_encryption(patients, field):
                all_verified = False

        if all_verified:
            print("\n✅ Migration completed and verified successfully!")
            print(f"📊 Total documents encrypted: {total_encrypted}")
        else:
            print("\n⚠️  Migration completed but verification failed")
            print("   Please investigate encrypted fields manually")
    elif args.dry_run:
        print("\n" + "=" * 60)
        print(f"[DRY RUN] Would encrypt {total_encrypted} total field values")
        print("Run without --dry-run to perform actual encryption")
        print("=" * 60)
    else:
        print("\n✅ No documents needed encryption")

    print("\n⚠️  IMPORTANT:")
    print("  - Backup encryption keys to secure offline location")
    print("  - Test application with encrypted data")
    print("  - Verify queries still work correctly")


if __name__ == '__main__':
    sys.exit(main())
