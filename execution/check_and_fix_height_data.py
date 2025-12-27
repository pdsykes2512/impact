#!/usr/bin/env python3
"""
Check and Fix Patient Height Data

This script checks all patient height values in the database and identifies
any that appear to be stored incorrectly (e.g., in meters when they should be in cm).

Since the field is height_cm, values should be in the range 100-250 cm.
Values < 3 are likely stored in meters and need to be converted to cm.
"""

import os
import sys
import argparse
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('MONGODB_DB_NAME', 'surgdb')


def main():
    parser = argparse.ArgumentParser(description='Check and fix patient height data')
    parser.add_argument('--fix', action='store_true', help='Automatically fix heights without prompting')
    args = parser.parse_args()

    print("=" * 60)
    print("Patient Height Data Check")
    print("=" * 60)

    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    patients_collection = db.patients

    # Find all patients with height data
    query = {'demographics.height_cm': {'$exists': True, '$ne': None}}
    patients_with_height = list(patients_collection.find(query, {
        'patient_id': 1,
        'demographics.height_cm': 1
    }))

    total = len(patients_with_height)
    print(f"\nTotal patients with height data: {total}")

    if total == 0:
        print("✓ No height data found in database - all new entries will use meters (m)")
        return 0

    # Analyze the data
    heights = [p['demographics']['height_cm'] for p in patients_with_height]

    print(f"\nHeight Statistics:")
    print(f"  Min: {min(heights)}")
    print(f"  Max: {max(heights)}")
    print(f"  Average: {sum(heights)/len(heights):.1f}")

    # Find values that look like they're in meters (< 3)
    meters_like = [p for p in patients_with_height if p['demographics']['height_cm'] < 3]

    if meters_like:
        print(f"\n⚠️  Found {len(meters_like)} patients with height < 3 (likely in meters):")
        for p in meters_like[:10]:
            print(f"  Patient {p['patient_id']}: {p['demographics']['height_cm']}")

        if len(meters_like) > 10:
            print(f"  ... and {len(meters_like) - 10} more")

        # Ask for confirmation to fix
        print("\n" + "=" * 60)
        print("FIX REQUIRED")
        print("=" * 60)
        print("These values appear to be stored in meters but should be in centimeters.")
        print(f"This will multiply all {len(meters_like)} values by 100.")
        print("\nExample conversions:")
        for p in meters_like[:3]:
            old = p['demographics']['height_cm']
            new = old * 100
            print(f"  {p['patient_id']}: {old} m → {new} cm")

        if not args.fix:
            response = input("\nProceed with conversion? (type 'yes' to confirm): ")
            proceed = response.lower() == 'yes'
        else:
            proceed = True
            print("\n--fix flag provided, proceeding with automatic conversion...")

        if proceed:
            fixed = 0
            for p in meters_like:
                old_height = p['demographics']['height_cm']
                new_height = old_height * 100

                result = patients_collection.update_one(
                    {'_id': p['_id']},
                    {'$set': {'demographics.height_cm': new_height}}
                )

                if result.modified_count > 0:
                    fixed += 1
                    print(f"✓ Fixed {p['patient_id']}: {old_height} m → {new_height} cm")

            print(f"\n✅ Successfully converted {fixed} heights from meters to centimeters")
        else:
            print("Conversion cancelled")

    # Find values that look suspicious (too small or too large for cm)
    suspicious = [p for p in patients_with_height if
                  p['demographics']['height_cm'] >= 3 and
                  (p['demographics']['height_cm'] < 100 or p['demographics']['height_cm'] > 250)]

    if suspicious:
        print(f"\n⚠️  Found {len(suspicious)} patients with suspicious heights (3-100 cm or > 250 cm):")
        for p in suspicious:
            print(f"  Patient {p['patient_id']}: {p['demographics']['height_cm']} cm")
        print("\nThese should be reviewed manually.")

    # Show normal values
    normal = [p for p in patients_with_height if
              100 <= p['demographics']['height_cm'] <= 250]

    if normal:
        print(f"\n✓ Found {len(normal)} patients with normal heights (100-250 cm)")

    print("\n" + "=" * 60)
    print("Check Complete")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
