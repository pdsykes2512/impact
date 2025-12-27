# Recent Changes Log

This file tracks significant changes made to the surg-db application. **Update this file at the end of each work session** to maintain continuity between AI chat sessions.

## Format
```
## YYYY-MM-DD - Brief Summary
**Changed by:** [User/AI Session]
**Issue:** What problem was being solved
**Changes:** What was modified
**Files affected:** List of files
**Testing:** How to verify it works
**Notes:** Any important context for future sessions
```

---

## 2025-12-27 - Patient Search Enhancement, Pagination & Modal Backdrop Fix

**Changed by:** AI Session
**Issue:** Multiple UI/UX improvements needed:
1. Patient search in cancer episode form needed to filter by MRN and NHS number
2. Patient ID field should be read-only in edit mode
3. MRN and NHS number should be visible for reference during episode creation
4. Pagination needed for large patient and episode lists
5. Modal backdrop not extending to top of viewport
6. Step titles in cancer episode form too long (wrapping to 3 lines)

**Changes:**

### 1. Patient Search Component Overhaul
- **PatientSearch.tsx**: Complete refactor from raw fetch() to api.get()
  - Fixed Patient interface to use correct field names (patient_id, mrn, nhs_number)
  - Changed to SearchableSelect component pattern for consistency
  - Added multi-field filter function (searches patient_id, MRN, NHS number)
  - Changed limit from 1000 to 100 (respecting backend limit)
  - Display label changed to show patient_id instead of mrn
  - Dropdown shows "MRN: xxx" and "NHS: xxx" for easy identification

### 2. Cancer Episode Form Enhancements
- **CancerEpisodeForm.tsx**:
  - Made Patient ID field read-only in edit mode with helper text
  - Added selectedPatientDetails state to store MRN and NHS number
  - Created 3-column grid layout: Patient Search | MRN | NHS Number
  - MRN and NHS number fields appear when patient is selected (read-only)
  - Updated step titles for better readability:
    - Step 1: "Patient Details" (was "Patient & Basics")
    - Step 2: "Referral Details" (was "Referral & Process")
  - Shorter titles prevent text wrapping in progress indicator

### 3. Pagination Implementation
- **Created Pagination.tsx**: Reusable pagination component
  - Shows page numbers with Previous/Next buttons
  - Displays "Showing X-Y of Z results"
  - Handles edge cases (first/last page, no results)
  - Consistent styling with application theme

- **PatientsPage.tsx**: Added pagination for patient list
  - 50 patients per page
  - Shows total count and current range
  - Pagination controls at bottom of table

- **EpisodesPage.tsx**: Added pagination for episode list
  - 50 episodes per page
  - Shows total count and current range
  - Pagination controls at bottom of table

### 4. API Layer Updates
- **api.ts**: Added count endpoints
  - apiService.patients.count() for patient totals
  - apiService.episodes.count() for episode totals

- **Backend routes updated**:
  - patients.py: Enhanced aggregation pipeline with better null handling
  - episodes_v2.py: Added count endpoint for pagination

### 5. Modal Backdrop Fix
- **All modal components**: Added `style={{ margin: 0 }}` to backdrop div
  - AddTreatmentModal.tsx
  - CancerEpisodeForm.tsx
  - EpisodeDetailModal.tsx
  - FollowUpModal.tsx
  - InvestigationModal.tsx
  - TreatmentSummaryModal.tsx
  - TumourModal.tsx
  - TumourSummaryModal.tsx
  - Fixes issue where dark background didn't extend to top of viewport
  - Overrides default body/html margins

### 6. SearchableSelect Enhancement
- **SearchableSelect.tsx**:
  - Shows first 100 options when search is empty (was showing nothing)
  - Increased z-index to z-[100] for better visibility

**Files affected:**
- `frontend/src/components/PatientSearch.tsx` - Complete refactor
- `frontend/src/components/CancerEpisodeForm.tsx` - Patient selection UI, step titles
- `frontend/src/components/Pagination.tsx` - New component
- `frontend/src/components/SearchableSelect.tsx` - Empty search behavior
- `frontend/src/pages/PatientsPage.tsx` - Added pagination
- `frontend/src/pages/EpisodesPage.tsx` - Added pagination
- `frontend/src/services/api.ts` - Added count endpoints
- `backend/app/routes/patients.py` - Aggregation improvements
- `backend/app/routes/episodes_v2.py` - Added count endpoint
- `frontend/src/components/AddTreatmentModal.tsx` - Modal backdrop fix
- `frontend/src/components/EpisodeDetailModal.tsx` - Modal backdrop fix
- `frontend/src/components/FollowUpModal.tsx` - Modal backdrop fix
- `frontend/src/components/InvestigationModal.tsx` - Modal backdrop fix
- `frontend/src/components/TreatmentSummaryModal.tsx` - Modal backdrop fix
- `frontend/src/components/TumourModal.tsx` - Modal backdrop fix
- `frontend/src/components/TumourSummaryModal.tsx` - Modal backdrop fix
- `STYLE_GUIDE.md` - Updated with modal backdrop requirement

**Testing:**
1. **Patient Search**:
   - Navigate to Cancer Episodes page
   - Click "New Cancer Episode"
   - Test patient search by typing MRN, NHS number, or Patient ID
   - Verify dropdown shows MRN and NHS number for each patient
   - Select a patient and verify Patient ID appears in search box
   - Verify MRN and NHS Number fields populate in same row

2. **Edit Mode**:
   - Open existing cancer episode
   - Click Edit
   - Verify Patient ID field is read-only with gray background
   - Verify helper text "Patient cannot be changed in edit mode"

3. **Pagination**:
   - Navigate to Patients page with >50 patients
   - Verify pagination controls appear
   - Test Previous/Next buttons
   - Verify "Showing 1-50 of X results" text
   - Navigate to Episodes page and repeat

4. **Modal Backdrop**:
   - Open any modal (patient, episode, treatment, etc.)
   - Verify dark backdrop extends fully to top of viewport
   - No white gap at top of screen

5. **Step Titles**:
   - Create new cancer episode
   - Verify step titles fit on 1-2 lines (not 3)
   - Check all 6 step titles display cleanly

**Notes:**
- Patient search now uses centralized API service (api.get) instead of raw fetch()
- Backend enforces 100 result limit for /patients/ endpoint
- Patient ID is always saved (not MRN) ensuring proper linking
- Pagination state managed at page level (currentPage state)
- Modal backdrop fix uses inline style to override browser defaults
- SearchableSelect now shows options on click (was requiring search input)
- Step title changes improve mobile/small screen readability

---

## 2025-12-27 - Backup System Frontend Integration

**Changed by:** AI Session
**Issue:** Backup system only accessible via CLI - users needed web UI for managing backups without SSH access.

**Changes:**
1. **Created Backend API** (`backend/app/routes/backups.py`):
   - 7 RESTful endpoints for backup management:
     - `GET /api/admin/backups/` - List all backups
     - `GET /api/admin/backups/status` - System status (counts, sizes, free space)
     - `POST /api/admin/backups/create` - Create manual backup with note
     - `GET /api/admin/backups/{backup_name}` - Get backup details
     - `DELETE /api/admin/backups/{backup_name}` - Delete backup
     - `POST /api/admin/backups/restore` - Get restore instructions (can't execute via web)
     - `POST /api/admin/backups/cleanup` - Run retention policy
     - `GET /api/admin/backups/logs/latest` - Last 50 log lines
   - All endpoints protected with `require_admin` auth
   - Background tasks for long operations (create, cleanup)
   - Calls Python scripts via subprocess

2. **Updated Backend Main** (`backend/app/main.py`):
   - Added backups router import and inclusion
   - Router available at `/api/admin/backups/`

3. **Added Backups Tab to Admin Page** (`frontend/src/pages/AdminPage.tsx`):
   - New "Backups" tab (4th tab alongside Users, Clinicians, Exports)
   - Added 6 state variables:
     - `backups: any[]` - List of backups
     - `backupStatus: any` - System status metrics
     - `backupLoading: boolean` - Loading state
     - `backupNote: string` - User input for manual backup notes
     - `showRestoreConfirm: boolean` - Restore modal visibility
     - `selectedBackup: string | null` - Selected backup for restore
   - Added `fetchBackups()` function with dual API calls (list + status)
   - Added helper functions:
     - `createBackup()` - POST to /create, auto-refresh after 5s
     - `deleteBackup()` - DELETE with confirmation
     - `formatBytes()` - Convert bytes to MB
     - `formatTimestamp()` - Format ISO date to locale string

4. **Backup Tab UI** (~200 lines of React components):
   - **Status Dashboard** - 4 metric cards with colored backgrounds:
     - Total Backups (blue bg)
     - Total Size (green bg)
     - Free Space (purple bg)
     - Total Documents (orange bg)
   - **Latest Backup Card** - Gradient styled card showing:
     - Timestamp
     - Type (Manual/Automatic)
     - Size
     - Collections count
     - Optional note
   - **Manual Backup Form** - Yellow warning-styled section:
     - Optional note input
     - "Create Backup Now" button
     - Warning text about duration
   - **Automatic Backups Info** - Info-styled section explaining:
     - Cron schedule (2 AM daily)
     - Retention policy (30d/3m/1y)
     - Manual backup protection
   - **Backup List Table** - Using standardized Table component:
     - 6 columns: Timestamp, Type, Size, Collections, Note, Actions
     - Delete button for each backup
     - "View Details" button to show restore modal
   - **Restore Confirmation Modal** - Warning-styled modal with:
     - Backup details display
     - SSH command with exact restore instructions
     - Red warning text about service restart
     - Safety guidelines
     - Close button (no web-based restore)

**Files affected:**
- `backend/app/routes/backups.py` - New API router (340 lines)
- `backend/app/main.py` - Added backups router import/inclusion
- `frontend/src/pages/AdminPage.tsx` - Added backups tab (~250 lines added)

**Testing:**
```bash
# Verify backend API (requires admin token)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/admin/backups/
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/admin/backups/status

# Web UI testing:
# 1. Log in as admin user
# 2. Navigate to Admin page
# 3. Click "Backups" tab
# 4. Verify status cards show correct counts
# 5. Create manual backup with note
# 6. Wait 5-10 seconds, verify new backup appears
# 7. Click "View Details" on a backup
# 8. Verify restore modal shows SSH command
# 9. Test delete backup (with confirmation)
# 10. Verify backup disappears from list

# Check services
sudo systemctl status surg-db-backend
sudo systemctl status surg-db-frontend
```

**Bug Fixes:**
- Fixed backend import error: Changed `get_current_admin_user` to `require_admin` in backups.py (function didn't exist)
- Fixed frontend TypeScript error: Added `fetchBackups()` function that was referenced but not defined
- Added missing state updates: `setBackups()` and `setBackupStatus()` calls in fetchBackups

**Security:**
- All endpoints require admin role via `require_admin` dependency
- Restore operations cannot be executed via web UI (requires SSH for service restart)
- Delete confirmations prevent accidental deletion
- Modal shows exact SSH command for manual restoration

**Notes:**
- Backup creation takes 5-10 seconds depending on database size - UI shows loading spinner
- Manual backups never auto-deleted by retention policy
- Restore instructions provided via modal, but actual restore requires SSH (service restart needed)
- Backend uses subprocess to call Python scripts (backup_database.py, cleanup_old_backups.py)
- Background tasks prevent API timeout during long operations

---

