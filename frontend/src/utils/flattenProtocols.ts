/** Flatten stain/region protocols into QC-friendly rows and CSV exports. */

import { REGION_SUMMARY_KEYS, STAIN_SUMMARY_KEYS } from './protocolDisplay'

export const LANDMARK_SLOT_COUNT = 3

const PROTOCOL_META_KEYS = new Set([
  'id',
  'type',
  'name',
  'description',
  'landmarks',
  '_localModified',
  '_remoteVersion',
  '_isDefault',
])

export interface FlatColumn {
  key: string
  label: string
}

export interface LandmarkAppendixRow {
  regionType: string
  regionTitle: string
  landmark: string
  sortOrder: number
}

function cell(value: unknown): string {
  if (value == null || value === '') return ''
  if (Array.isArray(value)) return value.join('; ')
  return String(value)
}

function landmarkSlots(landmarks: string[]): Record<string, string> {
  const slots: Record<string, string> = {}
  for (let i = 0; i < LANDMARK_SLOT_COUNT; i += 1) {
    slots[`landmark_${i + 1}`] = landmarks[i] ?? ''
  }
  return slots
}

/** Scalar protocol fields not already in the fixed column list. */
function extraScalarFields(
  protocol: Record<string, unknown>,
  fixedKeys: readonly string[],
): Record<string, string> {
  const skip = new Set([...fixedKeys, ...PROTOCOL_META_KEYS])
  const extras: Record<string, string> = {}
  for (const [key, value] of Object.entries(protocol)) {
    if (skip.has(key) || value == null || value === '') continue
    if (Array.isArray(value) || typeof value === 'object') continue
    extras[key] = cell(value)
  }
  return extras
}

export const REGION_FLAT_COLUMNS: FlatColumn[] = [
  { key: 'id', label: 'Protocol ID' },
  { key: 'abbreviation', label: 'Abbreviation' },
  { key: 'displayName', label: 'Display name' },
  { key: 'schemaRegionKey', label: 'Schema region key' },
  { key: 'name', label: 'Name' },
  { key: 'regionType', label: 'Region type' },
  { key: 'hemisphere', label: 'Hemisphere' },
  { key: 'sliceThickness_um', label: 'Thickness (µm)' },
  { key: 'sliceOrientation', label: 'Slice orientation' },
  { key: 'landmark_1', label: 'Landmark 1' },
  { key: 'landmark_2', label: 'Landmark 2' },
  { key: 'landmark_3', label: 'Landmark 3' },
  { key: 'landmarks_count', label: 'Landmarks count' },
  { key: 'landmarks_overflow', label: 'Landmarks 4+' },
  { key: 'description', label: 'Description' },
]

export const STAIN_FLAT_COLUMNS: FlatColumn[] = [
  { key: 'id', label: 'Protocol ID' },
  { key: 'abbreviation', label: 'Abbreviation' },
  { key: 'displayName', label: 'Display name' },
  { key: 'schemaStainKey', label: 'Schema stain key' },
  { key: 'name', label: 'Name' },
  { key: 'stainType', label: 'Stain type' },
  { key: 'antibody', label: 'Antibody' },
  { key: 'phosphoSpecific', label: 'Phospho-specific' },
  { key: 'chromogen', label: 'Chromogen' },
  { key: 'chemistry', label: 'Chemistry' },
  { key: 'vendor', label: 'Vendor' },
  { key: 'description', label: 'Description' },
]

export const LANDMARK_APPENDIX_COLUMNS: FlatColumn[] = [
  { key: 'regionType', label: 'Region type (schema key)' },
  { key: 'regionTitle', label: 'Region title' },
  { key: 'sortOrder', label: 'Order' },
  { key: 'landmark', label: 'Allowed landmark' },
]

const REGION_FIXED_KEYS = [
  ...REGION_FLAT_COLUMNS.map((c) => c.key),
  ...REGION_SUMMARY_KEYS.map((c) => c.key),
  'sliceThickness',
]

const STAIN_FIXED_KEYS = [
  ...STAIN_FLAT_COLUMNS.map((c) => c.key),
  ...STAIN_SUMMARY_KEYS.map((c) => c.key),
]

export function flattenRegionProtocol(protocol: Record<string, unknown>): Record<string, string> {
  const landmarks = Array.isArray(protocol.landmarks)
    ? protocol.landmarks.map((v) => String(v))
    : []
  const overflow =
    landmarks.length > LANDMARK_SLOT_COUNT
      ? landmarks.slice(LANDMARK_SLOT_COUNT).join('; ')
      : ''

  return {
    id: cell(protocol.id),
    abbreviation: cell(protocol.abbreviation),
    displayName: cell(protocol.displayName),
    schemaRegionKey: cell(protocol.schemaRegionKey),
    name: cell(protocol.name),
    regionType: cell(protocol.regionType),
    hemisphere: cell(protocol.hemisphere),
    sliceThickness_um: cell(protocol.sliceThickness),
    sliceOrientation: cell(protocol.sliceOrientation),
    ...landmarkSlots(landmarks),
    landmarks_count: landmarks.length ? String(landmarks.length) : '',
    landmarks_overflow: overflow,
    description: cell(protocol.description),
    ...extraScalarFields(protocol, REGION_FIXED_KEYS),
  }
}

export function flattenStainProtocol(protocol: Record<string, unknown>): Record<string, string> {
  return {
    id: cell(protocol.id),
    abbreviation: cell(protocol.abbreviation),
    displayName: cell(protocol.displayName),
    schemaStainKey: cell(protocol.schemaStainKey),
    name: cell(protocol.name),
    stainType: cell(protocol.stainType),
    antibody: cell(protocol.antibody),
    phosphoSpecific: cell(protocol.phosphoSpecific),
    chromogen: cell(protocol.chromogen),
    chemistry: cell(protocol.chemistry),
    vendor: cell(protocol.vendor),
    description: cell(protocol.description),
    ...extraScalarFields(protocol, STAIN_FIXED_KEYS),
  }
}

/** Pitt/BDSA region schema: allowed landmarks per region type (QC reference appendix). */
export function extractLandmarkAppendix(
  regionMetadata: Record<string, unknown> | null | undefined,
): LandmarkAppendixRow[] {
  const rows: LandmarkAppendixRow[] = []
  if (!regionMetadata) return rows

  const regions = (
    regionMetadata as {
      properties?: {
        bdsa_region_ids?: {
          properties?: {
            regions?: {
              properties?: Record<
                string,
                { title?: string; items?: { enum?: string[] } }
              >
            }
          }
        }
      }
    }
  )?.properties?.bdsa_region_ids?.properties?.regions?.properties

  if (!regions) return rows

  for (const [regionType, def] of Object.entries(regions)) {
    const enumVals = def?.items?.enum ?? []
    enumVals.forEach((landmark, index) => {
      rows.push({
        regionType,
        regionTitle: def.title ?? regionType,
        landmark,
        sortOrder: index + 1,
      })
    })
  }

  return rows.sort(
    (a, b) =>
      a.regionType.localeCompare(b.regionType) || a.sortOrder - b.sortOrder,
  )
}

export function mergeColumns(
  base: FlatColumn[],
  rows: Record<string, string>[],
): FlatColumn[] {
  const known = new Set(base.map((c) => c.key))
  const extraKeys = new Set<string>()
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!known.has(key)) extraKeys.add(key)
    }
  }
  const extras = [...extraKeys].sort().map((key) => ({ key, label: key }))
  return [...base, ...extras]
}

function escapeCsvCell(value: string): string {
  return `"${value.replace(/"/g, '""')}"`
}

export function rowsToCsv(columns: FlatColumn[], rows: Record<string, string>[]): string {
  const header = columns.map((c) => escapeCsvCell(c.label)).join(',')
  const body = rows.map((row) =>
    columns.map((c) => escapeCsvCell(row[c.key] ?? '')).join(','),
  )
  return [header, ...body].join('\n')
}

export function downloadTextFile(
  contents: string,
  filename: string,
  mimeType = 'text/csv;charset=utf-8;',
): void {
  const blob = new Blob([contents], { type: mimeType })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.href = url
  link.download = filename
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function htmlEscape(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export function exportProtocolsWorkbook(
  collectionLabel: string,
  regionRows: Record<string, string>[],
  stainRows: Record<string, string>[],
  landmarkRows: LandmarkAppendixRow[],
  regionColumns: FlatColumn[],
  stainColumns: FlatColumn[],
): void {
  const safeLabel = collectionLabel.replace(/[^\w.-]+/g, '_').slice(0, 40)

  const section = (title: string, columns: FlatColumn[], rows: Record<string, string>[]) => {
    let html = `<h2>${htmlEscape(title)}</h2><table><tr>`
    html += columns.map((c) => `<th>${htmlEscape(c.label)}</th>`).join('')
    html += '</tr>'
    for (const row of rows) {
      html += '<tr>'
      html += columns.map((c) => `<td>${htmlEscape(row[c.key] ?? '')}</td>`).join('')
      html += '</tr>'
    }
    html += '</table><br/>'
    return html
  }

  const landmarkFlat = landmarkRows.map((r) => ({
    regionType: r.regionType,
    regionTitle: r.regionTitle,
    sortOrder: String(r.sortOrder),
    landmark: r.landmark,
  }))

  let html =
    '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">'
  html += '<head><meta charset="utf-8"><style>table{border-collapse:collapse}th,td{border:1px solid #ccc;padding:6px}th{background:#f2f2f2}</style></head><body>'
  html += `<p><strong>Collection:</strong> ${htmlEscape(collectionLabel)}</p>`
  html += section('Region protocols', regionColumns, regionRows)
  html += section('Stain protocols', stainColumns, stainRows)
  html += section('Landmark reference (appendix)', LANDMARK_APPENDIX_COLUMNS, landmarkFlat)
  html += '</body></html>'

  downloadTextFile(
    html,
    `protocols-qc-${safeLabel || 'export'}.xls`,
    'application/vnd.ms-excel',
  )
}
