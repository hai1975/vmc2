import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Language } from '../types'

interface PdfPreviewProps {
  sessionId: string | null
  answers: Record<string, unknown>
  language: Language
  embedded?: boolean
}

export function PdfPreview({ sessionId, answers, language, embedded = false }: PdfPreviewProps) {
  const [displayUrl, setDisplayUrl] = useState<string | null>(null)
  const [pendingUrl, setPendingUrl] = useState<string | null>(null)
  const [initialLoading, setInitialLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const displayUrlRef = useRef<string | null>(null)
  const pendingUrlRef = useRef<string | null>(null)
  const requestIdRef = useRef(0)
  const answersKey = JSON.stringify(answers)

  const revokeUrl = (url: string | null) => {
    if (url) URL.revokeObjectURL(url)
  }

  const clearAllUrls = () => {
    revokeUrl(displayUrlRef.current)
    revokeUrl(pendingUrlRef.current)
    displayUrlRef.current = null
    pendingUrlRef.current = null
    setDisplayUrl(null)
    setPendingUrl(null)
  }

  useEffect(() => {
    if (!sessionId) {
      clearAllUrls()
      setError('')
      setInitialLoading(false)
      setRefreshing(false)
      return
    }

    let cancelled = false
    const reqId = ++requestIdRef.current
    const hasPdf = Boolean(displayUrlRef.current)
    const debounceMs = hasPdf ? 500 : 0

    const timer = window.setTimeout(async () => {
      if (!hasPdf) setInitialLoading(true)
      else setRefreshing(true)
      setError('')

      try {
        const blob = await api.fetchPdfBlob(sessionId)
        if (cancelled || reqId !== requestIdRef.current) return

        const url = URL.createObjectURL(blob)

        if (!displayUrlRef.current) {
          displayUrlRef.current = url
          setDisplayUrl(url)
          setInitialLoading(false)
          setRefreshing(false)
          return
        }

        if (pendingUrlRef.current) {
          revokeUrl(pendingUrlRef.current)
        }
        pendingUrlRef.current = url
        setPendingUrl(url)
      } catch (err) {
        if (cancelled || reqId !== requestIdRef.current) return
        setError(err instanceof Error ? err.message : 'Preview failed')
        setInitialLoading(false)
        setRefreshing(false)
        if (!displayUrlRef.current) clearAllUrls()
      }
    }, debounceMs)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [sessionId, answersKey])

  useEffect(() => {
    return () => {
      revokeUrl(displayUrlRef.current)
      revokeUrl(pendingUrlRef.current)
    }
  }, [])

  const handlePendingLoad = () => {
    const next = pendingUrlRef.current
    if (!next) return

    revokeUrl(displayUrlRef.current)
    displayUrlRef.current = next
    pendingUrlRef.current = null
    setDisplayUrl(next)
    setPendingUrl(null)
    setRefreshing(false)
  }

  const body = (
    <>
      {error && <div className="alert error pdf-preview-error">{error}</div>}

      {!sessionId && (
        <div className="pdf-preview-empty">
          {language === 'vi' ? 'Chọn biểu mẫu để xem PDF.' : 'Select a form to preview the PDF.'}
        </div>
      )}

      {sessionId && initialLoading && !displayUrl && (
        <div className="pdf-preview-empty">
          {language === 'vi' ? 'Đang tải PDF...' : 'Loading PDF...'}
        </div>
      )}

      {sessionId && displayUrl && (
        <div className="pdf-preview-viewport">
          {refreshing && (
            <span className="pdf-preview-live-badge">
              {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
            </span>
          )}
          <iframe
            className="pdf-preview-frame"
            src={displayUrl}
            title={language === 'vi' ? 'Xem trước PDF' : 'PDF Preview'}
          />
          {pendingUrl && (
            <iframe
              className="pdf-preview-frame pdf-preview-frame--preload"
              src={pendingUrl}
              title=""
              tabIndex={-1}
              aria-hidden
              onLoad={handlePendingLoad}
            />
          )}
        </div>
      )}
    </>
  )

  if (embedded) {
    return <div className="pdf-preview-card embedded">{body}</div>
  }

  return (
    <section className="card pdf-preview-card">
      <div className="pdf-preview-header">
        <h2>{language === 'vi' ? 'Xem trước PDF' : 'PDF Preview'}</h2>
        {refreshing && (
          <span className="pdf-preview-status">
            {language === 'vi' ? 'Live — đang cập nhật' : 'Live — updating'}
          </span>
        )}
      </div>
      {body}
    </section>
  )
}
