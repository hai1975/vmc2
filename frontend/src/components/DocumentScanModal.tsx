import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { DocumentScanResult, FormSession, Language } from '../types'

type DocType = 'auto' | 'id' | 'passport' | 'license' | 'insurance'

interface DocumentScanModalProps {
  language: Language
  open: boolean
  sessionId: string | null
  onClose: () => void
  onSessionUpdate: (session: FormSession) => void
}

const AUTO_SCAN_MS = 4500

export function DocumentScanModal({
  language,
  open,
  sessionId,
  onClose,
  onSessionUpdate,
}: DocumentScanModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const scanningRef = useRef(false)

  const [cameraError, setCameraError] = useState('')
  const [ready, setReady] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [autoScan, setAutoScan] = useState(false)
  const [docType, setDocType] = useState<DocType>('auto')
  const [status, setStatus] = useState('')
  const [lastResult, setLastResult] = useState<DocumentScanResult | null>(null)
  const [totalFilled, setTotalFilled] = useState(0)

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setReady(false)
  }, [])

  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current
    if (!video || !video.videoWidth) return null
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    return canvas.toDataURL('image/jpeg', 0.85)
  }, [])

  const runScan = useCallback(async () => {
    if (!sessionId || scanningRef.current) return
    const frame = captureFrame()
    if (!frame) return

    scanningRef.current = true
    setScanning(true)
    setStatus(language === 'vi' ? 'Đang đọc giấy tờ...' : 'Reading document...')

    try {
      const result = await api.scanDocument(sessionId, frame, docType, true)
      setLastResult(result)
      if (result.session) {
        onSessionUpdate(result.session)
      }
      if (result.filled_count > 0) {
        setTotalFilled((n) => n + result.filled_count)
        setStatus(
          language === 'vi'
            ? `Đã điền ${result.filled_count} trường (${result.detected_document}).`
            : `Filled ${result.filled_count} field(s) (${result.detected_document}).`,
        )
      } else {
        setStatus(
          language === 'vi'
            ? 'Không đọc được thông tin — hãy căn giấy tờ vào khung.'
            : 'No fields detected — align document in frame.',
        )
      }
    } catch (err) {
      setStatus(err instanceof Error ? err.message : language === 'vi' ? 'Quét thất bại' : 'Scan failed')
    } finally {
      scanningRef.current = false
      setScanning(false)
    }
  }, [captureFrame, docType, language, onSessionUpdate, sessionId])

  useEffect(() => {
    if (!open) {
      stopCamera()
      return
    }

    let cancelled = false

    async function startCamera() {
      setCameraError('')
      setStatus('')
      setLastResult(null)
      setTotalFilled(0)

      const constraints: MediaStreamConstraints[] = [
        { video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
        { video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
        { video: true, audio: false },
      ]

      for (const constraint of constraints) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia(constraint)
          if (cancelled) {
            stream.getTracks().forEach((t) => t.stop())
            return
          }
          streamRef.current = stream
          if (videoRef.current) {
            videoRef.current.srcObject = stream
            await videoRef.current.play()
            setReady(true)
          }
          return
        } catch {
          continue
        }
      }

      setCameraError(
        language === 'vi'
          ? 'Không mở được webcam. Hãy cho phép quyền camera.'
          : 'Could not open webcam. Please allow camera access.',
      )
    }

    void startCamera()

    return () => {
      cancelled = true
      stopCamera()
    }
  }, [language, open, stopCamera])

  useEffect(() => {
    if (!open || !autoScan || !ready || !sessionId) return
    const timer = window.setInterval(() => {
      void runScan()
    }, AUTO_SCAN_MS)
    return () => window.clearInterval(timer)
  }, [autoScan, open, ready, runScan, sessionId])

  if (!open) return null

  const handleClose = () => {
    if (scanning) return
    stopCamera()
    onClose()
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-card document-scan-modal">
        <header className="modal-header">
          <h2>{language === 'vi' ? 'Quét giấy tờ (webcam)' : 'Scan document (webcam)'}</h2>
          <button type="button" className="modal-close" onClick={handleClose} aria-label="Close">
            ×
          </button>
        </header>

        <p className="document-scan-hint">
          {language === 'vi'
            ? 'Đưa CMND/CCCD, hộ chiếu, bằng lái hoặc thẻ bảo hiểm vào khung camera. Hệ thống đọc và tự điền form.'
            : 'Hold ID, passport, driver license, or insurance card in the camera frame. We read and auto-fill the form.'}
        </p>

        {cameraError && <div className="alert error">{cameraError}</div>}

        <div className="document-scan-video-wrap">
          <video ref={videoRef} className="document-scan-video" playsInline muted />
          <div className="document-scan-frame" aria-hidden="true" />
        </div>

        <div className="document-scan-controls">
          <label className="document-scan-select">
            <span>{language === 'vi' ? 'Loại giấy tờ' : 'Document type'}</span>
            <select value={docType} onChange={(e) => setDocType(e.target.value as DocType)} disabled={scanning}>
              <option value="auto">{language === 'vi' ? 'Tự động' : 'Auto detect'}</option>
              <option value="id">{language === 'vi' ? 'CMND / CCCD' : 'ID card'}</option>
              <option value="passport">{language === 'vi' ? 'Hộ chiếu' : 'Passport'}</option>
              <option value="license">{language === 'vi' ? 'Bằng lái' : 'Driver license'}</option>
              <option value="insurance">{language === 'vi' ? 'Thẻ bảo hiểm' : 'Insurance card'}</option>
            </select>
          </label>

          <label className="document-scan-toggle">
            <input
              type="checkbox"
              checked={autoScan}
              onChange={(e) => setAutoScan(e.target.checked)}
              disabled={!ready || scanning}
            />
            <span>{language === 'vi' ? 'Quét liên tục (live)' : 'Continuous scan (live)'}</span>
          </label>
        </div>

        {status && <p className="document-scan-status">{status}</p>}

        {lastResult && lastResult.filled_count > 0 && (
          <details className="document-scan-details">
            <summary>
              {language === 'vi'
                ? `Trường vừa điền (${lastResult.filled_count})`
                : `Fields just filled (${lastResult.filled_count})`}
            </summary>
            <ul>
              {Object.keys(lastResult.extracted_fields).map((key) => (
                <li key={key}>{key}</li>
              ))}
            </ul>
          </details>
        )}

        {totalFilled > 0 && (
          <p className="document-scan-total">
            {language === 'vi' ? `Tổng đã điền trong phiên quét: ${totalFilled}` : `Total filled this scan: ${totalFilled}`}
          </p>
        )}

        <footer className="modal-footer">
          <button type="button" className="btn-secondary" onClick={handleClose} disabled={scanning}>
            {language === 'vi' ? 'Đóng' : 'Close'}
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={!ready || scanning || !sessionId}
            onClick={() => void runScan()}
          >
            {scanning
              ? language === 'vi'
                ? 'Đang quét...'
                : 'Scanning...'
              : language === 'vi'
                ? 'Quét ngay'
                : 'Scan now'}
          </button>
        </footer>
      </div>
    </div>
  )
}
