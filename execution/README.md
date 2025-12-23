# Execution Scripts

This directory contains Python scripts for database management and data operations.

## Scripts Overview

### Database Initialization

**`init_database.py`**
- Initializes MongoDB database with proper schemas and indexes
- Creates collections: users, patients, episodes, treatments, tumours, clinicians
- Sets up validation rules and performance indexes
- Run once during initial setup

```bash
python3 execution/init_database.py
```

### ID Migration

**`migrate_ids.py`**
- Migrates existing IDs from old format to new NHS Number-based format
- Updates all episodes, treatments, and tumours
- Maintains referential integrity across collections
- **WARNING**: Updates all IDs in the database - use with caution

```bash
python3 execution/migrate_ids.py
```

Format conversion:
- Old: `EPI-l5x2k8-ab3c9f` (timestamp-based)
- New: `EPI-1234567890-01` (NHS Number-based)

### Sample Data Creation

**`create_sample_data.py`**
- Creates realistic test data for development and testing
- Generates patients, clinicians, episodes, tumours, and treatments
- All IDs use new NHS Number-based format
- Safe to run multiple times (checks for existing records)

```bash
python3 execution/create_sample_data.py
```

Creates:
- 3 sample clinicians (consultant surgeons)
- 3 sample patients with NHS numbers
- 1-2 episodes per patient
- 1-2 tumours per episode
- 1-3 treatments per episode (surgery/chemo/radio)

### User Management

**`create_admin_user.py`**
- Creates an admin user account
- Interactive script prompts for email and password
- Useful for setting up initial admin access

```bash
python3 execution/create_admin_user.py
```

## ID Format Standards

All scripts follow the standardized ID format: **PREFIX-NHSNUMBER-COUNTER**

### Prefixes:
- **EPI**: Episodes
- **TUM**: Tumours
- **SUR**: Surgery treatments
- **ONC**: Chemotherapy treatments
- **DXT**: Radiotherapy treatments
- **IMM**: Immunotherapy treatments

### Examples:
```
EPI-1234567890-01  # First episode for patient with NHS number 1234567890
SUR-1234567890-02  # Second surgery for same patient
TUM-1234567890-01  # First tumour in an episode
ONC-1234567890-01  # First chemotherapy for patient
```

## Environment Setup

All scripts require:
1. MongoDB running and accessible
2. Environment variables configured in `.env`:
   ```
   MONGODB_URI=mongodb://admin:admin123@localhost:27017/surg_outcomes?authSource=admin
   MONGODB_DB_NAME=surg_outcomes
   ```
3. Python dependencies installed:
   ```bash
   pip install motor pymongo python-dotenv
   ```

## Script Execution Order

For a fresh setup:
1. `init_database.py` - Create database structure
2. `create_admin_user.py` - Create admin account
3. `create_sample_data.py` - Add test data (optional)

For migrating existing data:
1. `migrate_ids.py` - Convert IDs to new format
2. Verify data integrity in application

## Safety Notes

- **migrate_ids.py**: Prompts for confirmation before modifying database
- **create_sample_data.py**: Safe to run multiple times, skips duplicates
- **init_database.py**: Safe to run multiple times, won't overwrite existing collections

## Troubleshooting

**MongoDB Connection Error:**
- Check `.env` file has correct MongoDB URI
- Verify MongoDB is running: `systemctl status mongod`
- Check authentication credentials

**Schema Validation Error:**
- Ensure `created_by` field is included in all records
- Check date fields are proper datetime objects
- Verify required fields are present

**ID Migration Issues:**
- Patients must have NHS numbers before migration
- Run `migrate_ids.py` with database backup
- Check logs for skipped patients without NHS numbers
