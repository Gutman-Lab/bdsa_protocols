import {
  fetchCaseIdMappings,
  fetchPatientIdMappings,
  type CaseIdMappingItem,
  type PatientIdMappingItem,
} from './idMappings'
import { fetchApi } from './client'
import { fetchCollectionProtocols, type ProtocolsPayload } from './protocols'

export interface StainLabelMappingItem {
  stainLabel: string
  normalized?: string | null
  stainProtocolId: string
  validated?: boolean
  sourceField?: string
  source?: string | null
}

export interface StainLabelMappingsPayload {
  mappings: StainLabelMappingItem[]
  lastUpdated?: string | null
  source?: string
  version?: string
  totalMappings?: number
}

export interface StainLabelMappingsResponse {
  success?: boolean
  collection_id: string
  stainLabelMappings: StainLabelMappingsPayload | null
}

export interface RegionLabelMappingItem {
  regionLabel: string
  normalized?: string | null
  regionProtocolId: string
  validated?: boolean
  sourceField?: string
  source?: string | null
}

export interface RegionLabelMappingsPayload {
  mappings: RegionLabelMappingItem[]
  lastUpdated?: string | null
  source?: string
  version?: string
  totalMappings?: number
}

export interface RegionLabelMappingsResponse {
  success?: boolean
  collection_id: string
  regionLabelMappings: RegionLabelMappingsPayload | null
}

export function fetchStainLabelMappings(
  collectionId: string,
): Promise<StainLabelMappingsResponse> {
  return fetchApi(`/collections/${encodeURIComponent(collectionId)}/stain-label-mappings`)
}

export function fetchRegionLabelMappings(
  collectionId: string,
): Promise<RegionLabelMappingsResponse> {
  return fetchApi(`/collections/${encodeURIComponent(collectionId)}/region-label-mappings`)
}

export interface SlideMappingBundle {
  protocols: ProtocolsPayload
  stainLabelMappings: StainLabelMappingItem[]
  regionLabelMappings: RegionLabelMappingItem[]
  caseMappings: CaseIdMappingItem[]
  caseInstitutionId?: string
  caseLastUpdated?: string | null
  caseSource?: string
  patientMappings: PatientIdMappingItem[]
  patientInstitutionId?: string
  patientLastUpdated?: string | null
  patientSource?: string
}

export async function fetchSlideMappingBundle(
  collectionId: string,
): Promise<SlideMappingBundle> {
  const [protocolsRes, stainRes, regionRes, caseRes, patientRes] = await Promise.all([
    fetchCollectionProtocols(collectionId),
    fetchStainLabelMappings(collectionId),
    fetchRegionLabelMappings(collectionId),
    fetchCaseIdMappings(collectionId),
    fetchPatientIdMappings(collectionId),
  ])
  const casePayload = caseRes.caseIdMappings
  const patientPayload = patientRes.patientIdMappings
  return {
    protocols: protocolsRes.protocols,
    stainLabelMappings: stainRes.stainLabelMappings?.mappings ?? [],
    regionLabelMappings: regionRes.regionLabelMappings?.mappings ?? [],
    caseMappings: casePayload?.mappings ?? [],
    caseInstitutionId: casePayload?.institutionId,
    caseLastUpdated: casePayload?.lastUpdated,
    caseSource: casePayload?.source,
    patientMappings: patientPayload?.mappings ?? [],
    patientInstitutionId: patientPayload?.institutionId,
    patientLastUpdated: patientPayload?.lastUpdated,
    patientSource: patientPayload?.source,
  }
}
