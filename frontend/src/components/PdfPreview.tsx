import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { isMobilePdfViewer } from '../lib/mobile-detect'
import type { Language } from '../types'

const PdfCanvasView = lazy(() =>
  import('./PdfCanvasView').then((module) => ({ default: module.PdfCanvasView })),
)

interface PdfPreviewProps {
  sessionId: string | null
  formId?: string | null
  answers: Record<string, unknown>
  language: Language
  embedded?: boolean
}

export function PdfPreview({ sessionId, formId, answers, language, embedded = false }: PdfPreviewProps) {
  const [displayUrl, setDisplayUrl] = useState<string | null>(null)
  const [pendingUrl, setPendingUrl] = useState<string | null>(null)
  const [pdfBlob, setPdfBlob] = useState<Blob | null>(null)
  const [initialLoading, setInitialLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [mobileView] = useState(isMobilePdfViewer)
  const displayUrlRef = useRef<string | null>(null)
  const pendingUrlRef = useRef<string | null>(null)
  const pdfBlobRef = useRef<Blob | null>(null)
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
    pdfBlobRef.current = null
    setDisplayUrl(null)
    setPendingUrl(null)
    setPdfBlob(null)
  }

  useEffect(() => {
    clearAllUrls()
    setError('')
    setInitialLoading(false)
    setRefreshing(false)
    requestIdRef.current += 1
  }, [sessionId])

  useEffect(() => {
    if (!sessionId || formId === 'triage') {
      clearAllUrls()
      setError('')
      setInitialLoading(false)
      setRefreshing(false)
      return
    }

    let cancelled = false
    const reqId = ++requestIdRef.current
    const hasPdf = mobileView ? Boolean(pdfBlobRef.current) : Boolean(displayUrlRef.current)
    const debounceMs = hasPdf ? 500 : 0

    const timer = window.setTimeout(async () => {
      if (!hasPdf) setInitialLoading(true)
      else setRefreshing(true)
      setError('')

      try {
        const blob = await api.fetchPdfBlob(sessionId)
        if (cancelled || reqId !== requestIdRef.current) return

        if (mobileView) {
          pdfBlobRef.current = blob
          setPdfBlob(blob)
          setInitialLoading(false)
          setRefreshing(false)
          return
        }

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
        if (!displayUrlRef.current && !pdfBlobRef.current) clearAllUrls()
      }
    }, debounceMs)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [sessionId, formId, answersKey, mobileView])

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

  const openUrl = sessionId ? api.pdfUrl(sessionId) : null

  const body = (
    <>
      {error && <div className="alert error pdf-preview-error">{error}</div>}

      {!sessionId && (
        <div className="pdf-preview-empty">
          {language === 'vi' ? 'Chọn biểu mẫu để xem PDF.' : 'Select a form to preview the PDF.'}
        </div>
      )}

      {sessionId && formId === 'triage' && (
        <div className="pdf-preview-empty">
          {language === 'vi'
            ? 'Bấm Nói và cho biết ngày sinh — PDF sẽ hiện sau khi chọn form.'
            : 'Press Speak and give your date of birth — PDF preview appears after form selection.'}
        </div>
      )}

      {sessionId && formId !== 'triage' && initialLoading && !displayUrl && !pdfBlob && (
        <div className="pdf-preview-empty">
          {language === 'vi'
            ? 'Đang tạo PDF... (có thể mất vài giây trên server Render)'
            : 'Generating PDF... (may take a few seconds on Render)'}
        </div>
      )}

      {sessionId && formId !== 'triage' && mobileView && pdfBlob && (
        <div className="pdf-preview-viewport">
          <Suspense
            fallback={
              <div className="pdf-preview-empty">
                {language === 'vi' ? 'Đang tải PDF...' : 'Loading PDF...'}
              </div>
            }
          >
            <PdfCanvasView
              blob={pdfBlob}
              language={language}
              refreshing={refreshing}
              openUrl={openUrl}
            />
          </Suspense>
        </div>
      )}

      {sessionId && formId !== 'triage' && !mobileView && displayUrl && (
        <div className="pdf-preview-viewport">
          {refreshing && (
            <span className="pdf-preview-live-badge">
              {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
            </span>
          )}
          <iframe
            key={displayUrl}
            className="pdf-preview-frame"
            src={displayUrl}
            title={language === 'vi' ? 'Xem trước PDF' : 'PDF Preview'}
          />
          {pendingUrl && (
            <iframe
              className="pdf-preview-frame pdf-preview-frame--preload"
              src={pendingUrl}
              title={language === 'vi' ? 'PDF đang tải' : 'PDF loading'}
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
