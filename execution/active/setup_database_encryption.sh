#!/bin/bash

# Setup LUKS Filesystem Encryption for MongoDB Data Directory
#
# Purpose: Encrypt MongoDB data directory using LUKS (Linux Unified Key Setup)
# Compliance: UK GDPR Article 32 (Security of Processing)
#
# WARNING: This script will:
# 1. Stop MongoDB service
# 2. Create encrypted LUKS volume
# 3. Migrate existing data to encrypted volume
# 4. Update systemd service to mount encrypted volume on boot
#
# CRITICAL: Backup all data before running this script!
#
# Usage: sudo ./setup_database_encryption.sh
#
# Prerequisites:
# - Root access (sudo)
# - cryptsetup installed (apt-get install cryptsetup)
# - Sufficient disk space for temporary data migration
# - MongoDB backup completed and verified

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
MONGODB_DATA_DIR="/var/lib/mongodb"
ENCRYPTED_VOLUME_NAME="mongodb-encrypted"
MOUNT_POINT="/var/lib/mongodb-encrypted"
BACKUP_DIR="/var/backups/mongodb-migration"
KEY_FILE="/root/.mongodb-encryption-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if cryptsetup is installed
if ! command -v cryptsetup &> /dev/null; then
    log_error "cryptsetup not found. Install with: apt-get install cryptsetup"
    exit 1
fi

# Pre-flight checks
log_info "Starting MongoDB encryption setup..."
log_info "This will encrypt: $MONGODB_DATA_DIR"

# Check if MongoDB is running
if systemctl is-active --quiet mongod; then
    log_warn "MongoDB is currently running"
else
    log_warn "MongoDB is not running (this is expected)"
fi

# Confirm with user
echo ""
log_warn "⚠️  CRITICAL WARNING ⚠️"
echo "This script will:"
echo "  1. Stop MongoDB"
echo "  2. Create encrypted LUKS volume"
echo "  3. Migrate data to encrypted volume"
echo "  4. Configure automatic mounting"
echo ""
echo "BEFORE PROCEEDING:"
echo "  ✓ Have you backed up MongoDB? (backup_database.py)"
echo "  ✓ Have you verified the backup? (restore_database.py --verify)"
echo "  ✓ Do you have sufficient disk space?"
echo ""
read -p "Continue with encryption setup? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "Encryption setup cancelled"
    exit 0
fi

# Step 1: Stop MongoDB
log_info "Step 1/7: Stopping MongoDB service..."
systemctl stop mongod || true
sleep 2

if systemctl is-active --quiet mongod; then
    log_error "Failed to stop MongoDB service"
    exit 1
fi
log_info "MongoDB stopped successfully"

# Step 2: Create backup of current data
log_info "Step 2/7: Creating safety backup of MongoDB data..."
mkdir -p "$BACKUP_DIR"
rsync -av --progress "$MONGODB_DATA_DIR/" "$BACKUP_DIR/" || {
    log_error "Failed to backup MongoDB data"
    exit 1
}
log_info "Data backed up to: $BACKUP_DIR"

# Step 3: Determine device for encrypted volume
log_info "Step 3/7: Setting up encrypted volume..."

# Option A: Use a separate partition (recommended for production)
# You would specify a dedicated partition like /dev/sdb1
# For this script, we'll use a loop device with a file-based volume

VOLUME_SIZE="20G"  # Adjust based on your data size
VOLUME_FILE="/opt/mongodb-encrypted.img"

log_info "Creating $VOLUME_SIZE volume file at $VOLUME_FILE..."
fallocate -l "$VOLUME_SIZE" "$VOLUME_FILE" || {
    log_error "Failed to create volume file"
    exit 1
}

# Step 4: Setup LUKS encryption
log_info "Step 4/7: Initializing LUKS encryption..."

# Generate encryption key
log_info "Generating encryption key..."
dd if=/dev/urandom of="$KEY_FILE" bs=1024 count=4
chmod 600 "$KEY_FILE"

# Initialize LUKS volume with key file
log_info "Formatting LUKS volume (this may take a few minutes)..."
cryptsetup luksFormat "$VOLUME_FILE" "$KEY_FILE" \
    --type luks2 \
    --cipher aes-xts-plain64 \
    --key-size 512 \
    --hash sha256 \
    --iter-time 5000 \
    --use-random || {
    log_error "Failed to format LUKS volume"
    exit 1
}

log_info "LUKS volume created successfully"

# Step 5: Open and format encrypted volume
log_info "Step 5/7: Opening encrypted volume..."
cryptsetup luksOpen "$VOLUME_FILE" "$ENCRYPTED_VOLUME_NAME" --key-file="$KEY_FILE" || {
    log_error "Failed to open LUKS volume"
    exit 1
}

# Create filesystem on encrypted volume
log_info "Creating ext4 filesystem on encrypted volume..."
mkfs.ext4 "/dev/mapper/$ENCRYPTED_VOLUME_NAME" || {
    log_error "Failed to create filesystem"
    cryptsetup luksClose "$ENCRYPTED_VOLUME_NAME"
    exit 1
}

# Step 6: Mount and migrate data
log_info "Step 6/7: Mounting encrypted volume and migrating data..."
mkdir -p "$MOUNT_POINT"
mount "/dev/mapper/$ENCRYPTED_VOLUME_NAME" "$MOUNT_POINT" || {
    log_error "Failed to mount encrypted volume"
    cryptsetup luksClose "$ENCRYPTED_VOLUME_NAME"
    exit 1
}

# Set ownership
chown -R mongodb:mongodb "$MOUNT_POINT"

# Copy data to encrypted volume
log_info "Migrating MongoDB data to encrypted volume (this may take a while)..."
rsync -av --progress "$MONGODB_DATA_DIR/" "$MOUNT_POINT/" || {
    log_error "Failed to migrate data"
    umount "$MOUNT_POINT"
    cryptsetup luksClose "$ENCRYPTED_VOLUME_NAME"
    exit 1
}

# Verify data was copied
ORIGINAL_SIZE=$(du -sb "$MONGODB_DATA_DIR" | cut -f1)
ENCRYPTED_SIZE=$(du -sb "$MOUNT_POINT" | cut -f1)

if [[ $ORIGINAL_SIZE -ne $ENCRYPTED_SIZE ]]; then
    log_warn "Size mismatch detected! Original: $ORIGINAL_SIZE, Encrypted: $ENCRYPTED_SIZE"
    log_warn "Please verify data integrity before proceeding"
fi

log_info "Data migration complete"

# Step 7: Update MongoDB configuration and systemd
log_info "Step 7/7: Updating MongoDB configuration..."

# Backup original MongoDB data directory
mv "$MONGODB_DATA_DIR" "${MONGODB_DATA_DIR}.original"

# Create symbolic link to encrypted mount
ln -s "$MOUNT_POINT" "$MONGODB_DATA_DIR"

# Create systemd service for automatic mounting
cat > /etc/systemd/system/mongodb-encrypted.service <<EOF
[Unit]
Description=Mount encrypted MongoDB volume
Before=mongod.service
DefaultDependencies=no

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/cryptsetup luksOpen $VOLUME_FILE $ENCRYPTED_VOLUME_NAME --key-file=$KEY_FILE
ExecStart=/bin/mount /dev/mapper/$ENCRYPTED_VOLUME_NAME $MOUNT_POINT
ExecStop=/bin/umount $MOUNT_POINT
ExecStop=/usr/sbin/cryptsetup luksClose $ENCRYPTED_VOLUME_NAME

[Install]
WantedBy=multi-user.target
EOF

# Enable automatic mounting on boot
systemctl daemon-reload
systemctl enable mongodb-encrypted.service

# Update mongod service to depend on encrypted volume
mkdir -p /etc/systemd/system/mongod.service.d
cat > /etc/systemd/system/mongod.service.d/encrypted-volume.conf <<EOF
[Unit]
Requires=mongodb-encrypted.service
After=mongodb-encrypted.service
EOF

systemctl daemon-reload

# Start encrypted volume service
systemctl start mongodb-encrypted.service

# Verify mount
if ! mountpoint -q "$MOUNT_POINT"; then
    log_error "Encrypted volume not mounted correctly"
    exit 1
fi

# Start MongoDB
log_info "Starting MongoDB with encrypted storage..."
systemctl start mongod

sleep 5

if systemctl is-active --quiet mongod; then
    log_info "✅ MongoDB started successfully with encrypted storage"
else
    log_error "Failed to start MongoDB. Check logs: journalctl -u mongod -n 50"
    exit 1
fi

# Verification
log_info ""
log_info "🔒 Encryption Setup Complete!"
log_info ""
log_info "Summary:"
log_info "  ✓ LUKS volume created: $VOLUME_FILE"
log_info "  ✓ Encryption: AES-256-XTS"
log_info "  ✓ Encrypted volume: /dev/mapper/$ENCRYPTED_VOLUME_NAME"
log_info "  ✓ Mount point: $MOUNT_POINT"
log_info "  ✓ MongoDB data: $MONGODB_DATA_DIR -> $MOUNT_POINT"
log_info "  ✓ Automatic mount: Enabled (mongodb-encrypted.service)"
log_info "  ✓ MongoDB: Running with encrypted storage"
log_info ""
log_info "CRITICAL - Store securely:"
log_info "  📁 Encryption key: $KEY_FILE"
log_info "  📁 Original data backup: $BACKUP_DIR"
log_info ""
log_warn "⚠️  IMPORTANT SECURITY NOTES:"
log_warn "  1. Backup encryption key to secure offline location"
log_warn "  2. Without key file, data cannot be recovered"
log_warn "  3. Test database restore procedure"
log_warn "  4. Keep original backup for 1 week, then securely delete"
log_warn "  5. Document key location in disaster recovery plan"
log_info ""

# Test database connection
log_info "Testing database connection..."
python3 - <<PYTHON
import pymongo
import sys

try:
    client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Database connection successful")

    # Count patients
    db = client['surgical_outcomes']
    patient_count = db.patients.count_documents({})
    print(f"✅ Found {patient_count} patients in encrypted database")

except Exception as e:
    print(f"❌ Database connection failed: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON

if [[ $? -eq 0 ]]; then
    log_info ""
    log_info "🎉 Encryption setup completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Verify application works correctly"
    log_info "  2. Test backup and restore procedures"
    log_info "  3. Securely store encryption key offline"
    log_info "  4. Update disaster recovery documentation"
    log_info "  5. After 1 week of verified operation, remove original data:"
    log_info "     rm -rf ${MONGODB_DATA_DIR}.original"
    log_info "     rm -rf $BACKUP_DIR"
else
    log_error "Database verification failed. Check MongoDB logs."
    exit 1
fi
