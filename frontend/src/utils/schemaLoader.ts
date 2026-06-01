/** Pitt BDSA split schemas (default for /schema page). */

export const SCHEMA_PATHS = {
  clinical: '/schemas/clinical-metadata.json',
  region: '/schemas/region-metadata.json',
  stain: '/schemas/stain-metadata.json',
  slide: '/schemas/slide-level-metadata.json',
} as const

export type SchemaFileKey = keyof typeof SCHEMA_PATHS

export async function fetchSchemaFile(path: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${path}?t=${Date.now()}`)
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
  const [clinical, region, stain, slide] = await Promise.all([
    fetchSchemaFile(SCHEMA_PATHS.clinical),
    fetchSchemaFile(SCHEMA_PATHS.region),
    fetchSchemaFile(SCHEMA_PATHS.stain),
    fetchSchemaFile(SCHEMA_PATHS.slide),
  ])
  return {
    clinical,
    region,
    stain,
    slide,
    combined: {
      clinicalMetadata: clinical,
      regionMetadata: region,
      stainMetadata: stain,
      slideLevelMetadata: slide,
    },
  }
}
