export interface CollectionSummary {
  collection_id: string
  display_name: string
  number: number
}

export function formatCollectionLabel(c: CollectionSummary): string {
  return `#${c.number} — ${c.display_name}`
}

/** Next unused `collection-{n}` id for a new collection. */
export function suggestNewCollectionId(existing: CollectionSummary[]): string {
  const used = new Set(existing.map((c) => c.collection_id))
  let n = existing.length + 1
  while (used.has(`collection-${n}`)) {
    n += 1
  }
  return `collection-${n}`
}

export function findCollection(
  collections: CollectionSummary[],
  collectionId: string,
): CollectionSummary | undefined {
  return collections.find((c) => c.collection_id === collectionId)
}
