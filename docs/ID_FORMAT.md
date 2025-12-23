# ID Format Standards

All entity IDs in the Surgical Outcomes Database follow a standardized format: **PREFIX-NHSNUMBER-COUNTER**

## Format Structure

- **PREFIX**: 3-4 character code identifying the entity type
- **NHSNUMBER**: 10-digit NHS number (without spaces)
- **COUNTER**: 2-digit zero-padded incremental number per patient

Example: `EPI-1234567890-01`

## Prefixes by Entity Type

### Episodes
- **Prefix**: `EPI`
- **Example**: `EPI-1234567890-01`
- Patient's first episode, second episode, etc.

### Tumours
- **Prefix**: `TUM`
- **Example**: `TUM-1234567890-01`
- Tumours are numbered per episode

### Treatments
Treatment prefixes are based on the treatment type:

- **Surgery**: `SUR`
  - Example: `SUR-1234567890-01`
- **Chemotherapy**: `ONC`
  - Example: `ONC-1234567890-01`
- **Radiotherapy**: `DXT`
  - Example: `DXT-1234567890-01`
- **Immunotherapy**: `IMM`
  - Example: `IMM-1234567890-01`

## ID Generation Logic

### Episodes
When a patient is selected in the episode creation form:
1. Fetch the patient's NHS number from the patient record
2. Count existing episodes for that patient (by patient_id)
3. Generate ID: `EPI-{cleanNHS}-{count+1}`

### Treatments
When creating a treatment within an episode:
1. Fetch the episode's patient_id
2. Fetch the patient's NHS number
3. Count existing treatments for that patient (all episodes)
4. Generate ID based on treatment type: `{PREFIX}-{cleanNHS}-{count+1}`
5. Prefix changes dynamically if treatment type is changed before submission

### Tumours
When creating a tumour within an episode:
1. Fetch the episode's patient_id
2. Fetch the patient's NHS number
3. Count existing tumours for that episode
4. Generate ID: `TUM-{cleanNHS}-{count+1}`

## Implementation Details

### Frontend Components

#### `CancerEpisodeForm.tsx`
- `generateEpisodeId(nhsNumber: string, count: number)`: Generates episode IDs
- Episode ID is generated when patient is selected (not at form init)
- PatientSearch onChange handler fetches episode count and generates ID

#### `AddTreatmentModal.tsx`
- `generateTreatmentId(type: string, nhsNumber: string, count: number)`: Generates treatment IDs
- Treatment ID is generated after fetching episode and patient data
- ID prefix updates dynamically when treatment type changes

#### `TumourModal.tsx`
- `generateTumourId(nhsNumber: string, count: number)`: Generates tumour IDs
- Tumour ID is generated after fetching episode and patient data

#### `PatientSearch.tsx`
- Updated to pass full patient object to onChange callback
- Enables immediate access to NHS number upon patient selection

### API Endpoints Used

The ID generation relies on these API calls:

```typescript
// Get patient data (including NHS number)
GET /api/patients/{patient_id}

// Count existing episodes for a patient
GET /api/episodes?patient_id={mrn}

// Count existing treatments for an episode
GET /api/treatments?episode_id={episode_id}

// Count existing tumours for an episode
GET /api/tumours?episode_id={episode_id}

// Get episode details (to get patient_id)
GET /api/episodes/{episode_id}
```

## Benefits

1. **Traceability**: IDs are tied directly to patient identity (NHS number)
2. **Meaningful**: The ID format clearly identifies entity type and patient
3. **Sequential**: Easy to see how many episodes/treatments a patient has had
4. **Consistent**: All IDs follow the same pattern across the system
5. **Readable**: Human-readable format vs timestamp-based random strings

## Migration Notes

**Previous Format**: `PREFIX-timestamp36-randomhash`
- Example: `EPI-l5x2k8-ab3c9f`

**Current Format**: `PREFIX-NHSNUMBER-counter`
- Example: `EPI-1234567890-01`

Existing records with old format IDs will continue to work. New records will use the new format.
