import { useEffect, useRef, useState } from 'react'
import type { Language } from '../types'

interface SelfieCaptureProps {
  language: Language
  value: string | null
  onChange: (dataUrl: string | null) => void
}

export function SelfieCapture({ language, value, onChange }: SelfieCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [error, setError] = useState('')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        })
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
      } catch {
        setError(
          language === 'vi'
            ? 'Không mở được camera. Hãy cho phép quyền camera.'
            : 'Could not open camera. Please allow camera permission.',
        )
      }
    }

    if (!value) void startCamera()

    return () => {
      cancelled = true
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [language, value])

  const capture = () => {
    const video = videoRef.current
    if (!video) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.88)
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    onChange(dataUrl)
  }

  const retake = () => {
    onChange(null)
  }

  if (value) {
    return (
      <div className="selfie-capture">
        <img src={value} alt="" className="selfie-preview" />
        <button type="button" className="btn-secondary" onClick={retake}>
          {language === 'vi' ? 'Chụp lại' : 'Retake'}
        </button>
      </div>
    )
  }

  return (
    <div className="selfie-capture">
      <p className="selfie-hint">
        {language === 'vi'
          ? 'Ảnh sẽ được dán góc trên bên phải của form PDF.'
          : 'Photo will appear in the top-right corner of the PDF form.'}
      </p>
      {error && <div className="alert error">{error}</div>}
      <video ref={videoRef} className="selfie-video" playsInline muted />
      <button type="button" className="btn-primary" disabled={!ready} onClick={capture}>
        {language === 'vi' ? 'Chụp ảnh' : 'Take photo'}
      </button>
    </div>
  )
}
