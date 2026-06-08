/** Pitt BDSA split schemas — loaded from the FastAPI backend. */

import {
  fetchCombinedSchema,
  fetchSchema,
  SCHEMA_API_PATHS,
  type SchemaId,
} from '../api/schemas'
import { apiHeaders } from '../api/client'

export const SCHEMA_PATHS = {
  clinical: SCHEMA_API_PATHS.clinical,
  region: SCHEMA_API_PATHS.region,
  stain: SCHEMA_API_PATHS.stain,
  slide: SCHEMA_API_PATHS.slide,
} as const

export type SchemaFileKey = keyof typeof SCHEMA_PATHS

export async function fetchSchemaFile(path: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${path}?t=${Date.now()}`, { headers: apiHeaders() })
  if (!response.ok) {
    throw new Error(`Failed to load schema: ${path}`)
  }
  return response.json() as Promise<Record<string, unknown>>
}

export async function loadAllSchemas(): Promise<{
  clinical: Record<string, unknown>
  region: Record<string, unknown>
  stain: Record<string, unknown>
  slide: Record<string, unknown>
  /** Combined object for flattened / CDE views */
  combined: Record<string, unknown>
}> {
  const combined = await fetchCombinedSchema()
  return {
    clinical: combined.clinicalMetadata,
    region: combined.regionMetadata,
    stain: combined.stainMetadata,
    slide: combined.slideLevelMetadata,
    combined: combined as unknown as Record<string, unknown>,
  }
}

/** Fetch a single schema by short id. */
export async function loadSchemaById(id: SchemaFileKey): Promise<Record<string, unknown>> {
  return fetchSchema(id)
}
