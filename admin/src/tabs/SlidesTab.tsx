import { useEffect, useState } from 'react'
import { fetchSlides } from '../api'
import { DataView } from '../DataView'

interface Props {
  collectionId: string | null
}

export function SlidesTab({ collectionId }: Props) {
  const [data, setData] = useState<unknown>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!collectionId) {
      setData(null)
      setError(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchSlides(collectionId)
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [collectionId])

  if (!collectionId) {
    return (
      <div className="tab-placeholder">
        <p>Select a collection above to view slides.</p>
      </div>
    )
  }

  return (
    <DataView
      title="Slides (BDSA metadata)"
      data={data}
      loading={loading}
      error={error ?? undefined}
    />
  )
}
