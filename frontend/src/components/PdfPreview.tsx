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
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const blobUrlRef = useRef<string | null>(null)
  const answersKey = JSON.stringify(answers)

  useEffect(() => {
    if (!sessionId) {
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current)
        blobUrlRef.current = null
      }
      setPdfUrl(null)
      setError('')
      setLoading(false)
      return
    }

    let cancelled = false
    const timer = window.setTimeout(async () => {
      setLoading(true)
      setError('')
      try {
        const blob = await api.fetchPdfBlob(sessionId)
        if (cancelled) return
        const url = URL.createObjectURL(blob)
        if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current)
        blobUrlRef.current = url
        setPdfUrl(url)
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Preview failed')
        setPdfUrl(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 600)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [sessionId, answersKey])

  useEffect(() => {
    return () => {
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current)
    }
  }, [])

  const body = (
    <>
      {error && <div className="alert error pdf-preview-error">{error}</div>}

      {!sessionId && (
        <div className="pdf-preview-empty">
          {language === 'vi' ? 'Chọn biểu mẫu để xem PDF.' : 'Select a form to preview the PDF.'}
        </div>
      )}

      {sessionId && loading && !pdfUrl && (
        <div className="pdf-preview-empty">
          {language === 'vi' ? 'Đang tải PDF...' : 'Loading PDF...'}
        </div>
      )}

      {sessionId && pdfUrl && (
        <iframe
          className="pdf-preview-frame"
          src={pdfUrl}
          title={language === 'vi' ? 'Xem trước PDF' : 'PDF Preview'}
        />
      )}
    </>
  )

  if (embedded) {
    return (
      <div className="pdf-preview-card embedded">
        {loading && pdfUrl && (
          <span className="pdf-preview-status">
            {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
          </span>
        )}
        {body}
      </div>
    )
  }

  return (
    <section className="card pdf-preview-card">
      <div className="pdf-preview-header">
        <h2>{language === 'vi' ? 'Xem trước PDF' : 'PDF Preview'}</h2>
        {loading && pdfUrl && (
          <span className="pdf-preview-status">
            {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
          </span>
        )}
      </div>
      {body}
    </section>
  )
}
