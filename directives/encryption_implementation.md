# Encryption Implementation Directive

> **Purpose**: Implement multi-layer encryption for UK GDPR and Caldicott Principles compliance

## Compliance Requirements

### UK GDPR Requirements
1. **Encryption at rest** - All patient data must be encrypted when stored
2. **Encryption in transit** - All data transmissions must use TLS/SSL
3. **Pseudonymization** - Use patient IDs instead of identifiable information in logs
4. **Access controls** - Role-based access with audit logging
5. **Data minimization** - Only collect and process necessary data
6. **Right to erasure** - Ability to securely delete patient data
7. **Breach notification** - Detect and report breaches within 72 hours

### Caldicott Principles
1. **Justify purpose** - Clear purpose for data processing
2. **Don't use unless absolutely necessary** - Minimize data collection
3. **Use minimum necessary** - Only access required fields
4. **Access on need-to-know basis** - Role-based permissions
5. **Everyone is responsible** - All staff aware of obligations
6. **Comply with the law** - UK GDPR, Data Protection Act 2018
7. **Duty to share information** - Balance privacy with care needs
8. **Inform patients** - Transparency about data usage

## Multi-Layer Encryption Strategy

### Layer 1: Filesystem Encryption (LUKS)
**Goal**: Encrypt MongoDB data directory at rest

**Implementation**:
- Use Linux Unified Key Setup (LUKS) for `/var/lib/mongodb` partition
- AES-256-XTS encryption algorithm
- Key stored securely (not in codebase)
- Automatic mount on system boot

**Script**: `execution/active/setup_database_encryption.sh`

**Inputs**:
- MongoDB data directory path
- Encryption passphrase (from secure input, not logged)

**Outputs**:
- Encrypted LUKS volume
- Systemd service updated to mount encrypted volume
- Documentation of encryption setup

**Edge Cases**:
- Existing MongoDB data must be migrated to encrypted volume
- System reboot requires passphrase or key file
- Performance impact (~5-10% overhead)

### Layer 2: Field-Level Encryption
**Goal**: Encrypt sensitive fields in MongoDB collections

**Sensitive Fields**:
- `patients.nhs_number` - NHS number (primary identifier)
- `patients.mrn` - Medical record number
- `patients.postcode` - Partial postcode (geographic identifier)
- `patients.date_of_birth` - Date of birth
- Future: pathology notes, surgery notes (free text fields)

**Implementation**:
- MongoDB Client-Side Field Level Encryption (CSFLE) or
- Python cryptography library (Fernet - AES-128-CBC with HMAC)
- Transparent encryption/decryption in backend
- Search still works for encrypted fields (deterministic encryption)

**Script**: `backend/app/utils/encryption.py`

**Inputs**:
- Field name and value to encrypt/decrypt
- Master encryption key (from environment or key management system)

**Outputs**:
- Encrypted field value (base64-encoded ciphertext)
- Decrypted plaintext value

**Edge Cases**:
- Key rotation requires re-encrypting all fields
- Search on encrypted fields requires deterministic encryption (same plaintext → same ciphertext)
- Performance impact for bulk operations

### Layer 3: Backup Encryption
**Goal**: Encrypt MongoDB backup files

**Implementation**:
- Update `execution/active/backup_database.py`
- Use `gpg` or `openssl` for AES-256 encryption
- Encrypted backups stored in `/var/backups/mongodb/`
- Encryption key separate from backup location

**Script**: `execution/active/backup_database.py` (modified)

**Inputs**:
- MongoDB dump file
- Encryption key (from environment or key file)

**Outputs**:
- Encrypted `.tar.gz.enc` backup file
- Backup metadata (timestamp, size, checksum)

**Edge Cases**:
- Restore process requires decryption key
- Key loss means permanent data loss
- Old backups must be re-encrypted after key rotation

### Layer 4: Transport Encryption
**Goal**: Ensure all network traffic is encrypted

**MongoDB Connections**:
- Enable TLS/SSL for MongoDB connections
- Update connection strings to use `tls=true`
- Certificate verification

**API Connections**:
- HTTPS for FastAPI backend (nginx reverse proxy)
- TLS 1.2+ minimum
- Strong cipher suites only

**Script**: `execution/active/verify_tls_config.py`

**Inputs**:
- MongoDB connection string
- API endpoint URL

**Outputs**:
- Verification report (TLS version, cipher suite, certificate validity)
- Warnings for weak configurations

**Edge Cases**:
- Self-signed certificates in development
- Certificate expiry monitoring
- Client compatibility with TLS versions

### Layer 5: Key Management
**Goal**: Secure storage and rotation of encryption keys

**Options**:
1. **Environment variables** (.env file) - Simple, not recommended for production
2. **File-based** (encrypted key file) - Better, requires secure file permissions
3. **HashiCorp Vault** (recommended) - Enterprise key management, audit logs, rotation
4. **Cloud KMS** (AWS KMS, Azure Key Vault) - If cloud-hosted

**Implementation** (Vault):
- Install HashiCorp Vault
- Store master encryption keys in Vault
- Backend retrieves keys via Vault API
- Automatic key rotation policy (quarterly)

**Script**: `execution/active/setup_vault.sh`

**Inputs**:
- Vault server address
- Authentication credentials
- Key paths in Vault

**Outputs**:
- Vault initialized and unsealed
- Encryption keys stored securely
- Backend configured to use Vault

**Edge Cases**:
- Vault downtime breaks application (need fallback or cache)
- Initial Vault setup requires manual unsealing
- Key rotation requires coordinated re-encryption

## Implementation Phases

### Tier 1: Immediate (Week 1)
✅ **Critical compliance items**
1. LUKS filesystem encryption for MongoDB data
2. Backup encryption (AES-256)
3. Verify TLS/SSL for all connections
4. Create security documentation

**Deliverables**:
- Encrypted MongoDB data directory
- Encrypted backup files
- TLS verification report
- ENCRYPTION_COMPLIANCE.md documentation

### Tier 2: Short-term (Weeks 2-3)
✅ **Field-level encryption and key management**
1. Field-level encryption for NHS numbers, postcodes, DOB
2. HashiCorp Vault setup (or file-based keys for MVP)
3. Pseudonymization in audit logs
4. Update API to handle encrypted fields transparently

**Deliverables**:
- Encryption utility module
- Encrypted sensitive fields in database
- Key management system operational
- Updated audit logging (no PII in logs)

### Tier 3: Long-term (Month 2+)
✅ **Advanced features and optimization**
1. MongoDB Enterprise (or continue with LUKS + CSFLE)
2. Automated key rotation
3. External security audit
4. Performance optimization for encrypted queries

**Deliverables**:
- Production-grade encryption solution
- Security audit report
- Key rotation procedures
- Performance benchmarks

## Testing Strategy

### Unit Tests
- Encryption/decryption roundtrip
- Key derivation
- Error handling (wrong key, corrupted data)

### Integration Tests
- API endpoints with encrypted fields
- Backup and restore with encryption
- MongoDB queries on encrypted fields

### Compliance Tests
- Verify no PII in logs
- Verify encryption at rest (filesystem check)
- Verify TLS in transit (network capture)
- Verify access controls (role-based tests)

### Performance Tests
- Query performance with encrypted fields
- Backup/restore time with encryption
- API response times

## Security Best Practices

1. **Never log encryption keys** - Keys only in memory or secure storage
2. **Use strong passphrases** - Minimum 20 characters, high entropy
3. **Separate key storage** - Keys not on same system as data
4. **Regular key rotation** - Quarterly or after suspected compromise
5. **Audit all access** - Who accessed what data, when
6. **Principle of least privilege** - Minimal permissions for each role
7. **Secure key backup** - Offline backup of master keys
8. **Encryption testing** - Regular verification that encryption is active

## Rollback Plan

If encryption causes issues:
1. **Filesystem encryption**: Boot from recovery, decrypt LUKS volume, copy data out
2. **Field-level encryption**: Migration script to decrypt all fields
3. **Backup encryption**: Keep unencrypted backups for transition period (1 week)
4. **Always test restore** before considering backup strategy complete

## Success Criteria

✅ All patient data encrypted at rest (LUKS or TDE)
✅ All sensitive fields encrypted in database (NHS number, MRN, postcode, DOB)
✅ All backups encrypted with AES-256
✅ All network traffic uses TLS/SSL
✅ No PII in application logs
✅ Key management system operational
✅ Security documentation complete
✅ Restore procedures tested and documented
✅ Performance acceptable (<20% overhead)
✅ Compliance audit passes (GDPR + Caldicott)

## Documentation Requirements

1. **ENCRYPTION_COMPLIANCE.md** - Compliance mapping to GDPR and Caldicott
2. **ENCRYPTION_OPERATIONS.md** - How to manage keys, rotate, restore
3. **ENCRYPTION_ARCHITECTURE.md** - Technical implementation details
4. **INCIDENT_RESPONSE.md** - What to do if breach suspected

---

**Status**: IMPLEMENTATION IN PROGRESS
**Created**: 2025-12-27
**Owner**: AI Agent
**Compliance**: UK GDPR, Data Protection Act 2018, Caldicott Principles
