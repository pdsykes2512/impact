/**
 * Type Definitions Index
 *
 * Central export point for all TypeScript type definitions.
 * Import types from here in application code.
 *
 * Usage:
 *   import type { Patient, Episode, ApiError } from '@/types'
 */

// Domain models
export type {
  Patient,
  PatientDemographics,
  ContactInfo,
  Episode,
  ConditionType,
  CancerType,
  CancerData,
  Treatment,
  TreatmentIntent,
  Urgency,
  Approach,
  Team,
  Complication,
  Tumour,
  Investigation,
  InvestigationType,
  FollowUp,
  Clinician,
  SurgicalMetrics,
  YearlyMetrics,
  User,
  UserRole,
  AuthToken,
  BackupInfo,
  AuditLog,
  AuditAction,
  EntityType
} from './models'

// API types
export type {
  ApiListParams,
  ApiCountResponse,
  ApiError,
  PatientListParams,
  PatientListResponse,
  PatientCreateRequest,
  PatientUpdateRequest,
  PatientResponse,
  EpisodeListParams,
  EpisodeListResponse,
  EpisodeCreateRequest,
  EpisodeUpdateRequest,
  EpisodeResponse,
  TreatmentListParams,
  TreatmentListResponse,
  TreatmentCreateRequest,
  TreatmentUpdateRequest,
  TreatmentResponse,
  TumourCreateRequest,
  TumourUpdateRequest,
  TumourResponse,
  InvestigationCreateRequest,
  InvestigationUpdateRequest,
  InvestigationResponse,
  FollowUpCreateRequest,
  FollowUpUpdateRequest,
  FollowUpResponse,
  ClinicianCreateRequest,
  ClinicianUpdateRequest,
  ClinicianListResponse,
  ClinicianResponse,
  LoginRequest,
  LoginResponse,
  UserCreateRequest,
  UserUpdateRequest,
  UserListResponse,
  UserResponse,
  SummaryReportResponse,
  SurgeonPerformanceParams,
  BackupCreateRequest,
  BackupRestoreRequest,
  BackupListResponse,
  BackupResponse,
  AuditLogParams,
  AuditLogListResponse,
  ExportParams,
  ICD10Code,
  OPCS4Code,
  CodeValidationResponse,
  NHSProvider,
  NHSProviderSearchParams,
  NHSProviderListResponse
} from './api'
