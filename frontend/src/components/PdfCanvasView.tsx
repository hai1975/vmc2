import { useEffect, useRef, useState } from 'react'
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist/legacy/build/pdf.mjs'
import pdfWorker from 'pdfjs-dist/legacy/build/pdf.worker.min.mjs?url'
import type { Language } from '../types'

GlobalWorkerOptions.workerSrc = pdfWorker

interface PdfCanvasViewProps {
  blob: Blob | null
  language: Language
  refreshing?: boolean
  openUrl?: string | null
}

export function PdfCanvasView({ blob, language, refreshing = false, openUrl }: PdfCanvasViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const renderIdRef = useRef(0)

  useEffect(() => {
    const container = containerRef.current
    if (!blob || !container) {
      if (container) container.replaceChildren()
      return
    }

    let cancelled = false
    const renderId = ++renderIdRef.current

    async function renderPdf() {
      setLoading(true)
      setError('')
      container!.replaceChildren()

      try {
        const data = await blob!.arrayBuffer()
        const pdf = await getDocument({ data }).promise
        if (cancelled || renderId !== renderIdRef.current) return

        const containerWidth = container!.clientWidth || 320

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
          const page = await pdf.getPage(pageNum)
          if (cancelled || renderId !== renderIdRef.current) return

          const baseViewport = page.getViewport({ scale: 1 })
          const scale = containerWidth / baseViewport.width
          const viewport = page.getViewport({ scale })

          const canvas = document.createElement('canvas')
          canvas.className = 'pdf-canvas-page'
          canvas.width = Math.floor(viewport.width)
          canvas.height = Math.floor(viewport.height)

          const context = canvas.getContext('2d')
          if (!context) continue

          await page.render({ canvas, canvasContext: context, viewport }).promise
          if (cancelled || renderId !== renderIdRef.current) return

          container!.appendChild(canvas)
        }
      } catch (err) {
        if (cancelled || renderId !== renderIdRef.current) return
        setError(err instanceof Error ? err.message : 'Failed to render PDF')
      } finally {
        if (!cancelled && renderId === renderIdRef.current) setLoading(false)
      }
    }

    void renderPdf()
    return () => {
      cancelled = true
    }
  }, [blob])

  return (
    <div className="pdf-canvas-view">
      {(loading || refreshing) && (
        <span className="pdf-preview-live-badge">
          {language === 'vi' ? 'Đang cập nhật...' : 'Updating...'}
        </span>
      )}
      {error && (
        <div className="alert error pdf-preview-error">{error}</div>
      )}
      {error && openUrl && (
        <>
          <embed className="pdf-embed-fallback" src={openUrl} type="application/pdf" />
          <p className="pdf-open-fallback">
            <a href={openUrl} target="_blank" rel="noopener noreferrer">
              {language === 'vi' ? 'Mở PDF trong tab mới' : 'Open PDF in new tab'}
            </a>
          </p>
        </>
      )}
      {!error && openUrl && (
        <a className="pdf-open-link" href={openUrl} target="_blank" rel="noopener noreferrer">
          {language === 'vi' ? 'Mở toàn màn hình' : 'Open full screen'}
        </a>
      )}
      <div ref={containerRef} className="pdf-canvas-scroll" />
      {loading && !error && <div className="pdf-preview-empty pdf-canvas-loading">…</div>}
    </div>
  )
}
