import { fetchApi } from './client'

/** External ID crosswalk keyed by system name (e.g. nacc, ndd). */
export type AlternateCaseIds = Record<string, string>

export interface CaseIdMappingItem {
  localCaseId: string
  bdsaCaseId: string
  alternateIds?: AlternateCaseIds
}

export interface CaseIdMappingsPayload {
  institutionId?: string
  mappings: CaseIdMappingItem[]
  lastUpdated?: string | null
  source?: string
  version?: string
  totalMappings?: number
}

export interface CaseIdMappingsResponse {
  success?: boolean
  collection_id: string
  caseIdMappings: CaseIdMappingsPayload | null
}

export interface PatientIdMappingItem {
  localPatientId: string
  bdsaPatientId?: string | null
}

export interface PatientIdMappingsPayload {
  institutionId?: string
  mappings: PatientIdMappingItem[]
  lastUpdated?: string | null
  source?: string
  version?: string
  totalMappings?: number
}

export interface PatientIdMappingsResponse {
  success?: boolean
  collection_id: string
  patientIdMappings: PatientIdMappingsPayload | null
}

export function fetchCaseIdMappings(collectionId: string): Promise<CaseIdMappingsResponse> {
  return fetchApi(`/collections/${encodeURIComponent(collectionId)}/case-id-mappings`)
}

export function fetchPatientIdMappings(
  collectionId: string,
): Promise<PatientIdMappingsResponse> {
  return fetchApi(`/collections/${encodeURIComponent(collectionId)}/patient-id-mappings`)
}
