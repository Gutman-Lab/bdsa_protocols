import { apiPath, fetchApi } from './client'

export interface SchemaSummary {
  id: string
  filename: string
  title: string
  url: string
}

export interface SchemasListResponse {
  schemas: SchemaSummary[]
  combined_url: string
  source: string
}

export interface CombinedSchemaResponse {
  clinicalMetadata: Record<string, unknown>
  regionMetadata: Record<string, unknown>
  stainMetadata: Record<string, unknown>
  slideLevelMetadata: Record<string, unknown>
}

/** API paths for each split schema (for components that fetch by URL). */
export const SCHEMA_API_PATHS = {
  clinical: apiPath('/schemas/clinical'),
  region: apiPath('/schemas/region'),
  stain: apiPath('/schemas/stain'),
  slide: apiPath('/schemas/slide'),
  combined: apiPath('/schemas/combined'),
} as const

export type SchemaId = keyof typeof SCHEMA_API_PATHS

export function fetchSchemaList(): Promise<SchemasListResponse> {
  return fetchApi('/schemas')
}

export function fetchSchema(schemaId: Exclude<SchemaId, 'combined'>): Promise<Record<string, unknown>> {
  return fetchApi(`/schemas/${schemaId}`)
}

export function fetchCombinedSchema(): Promise<CombinedSchemaResponse> {
  return fetchApi('/schemas/combined')
}

/** Download URL for a schema file (attachment). */
export function schemaDownloadUrl(schemaId: Exclude<SchemaId, 'combined'>): string {
  return `${apiPath(`/schemas/${schemaId}`)}?download=true`
}
