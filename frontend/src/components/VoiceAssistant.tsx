import { forwardRef, useEffect, useImperativeHandle, useRef, useState, startTransition } from 'react'
import { api } from '../api/client'
import { ConnectionRingtone } from '../lib/connection-ring'
import { GeminiLiveSession, type GeminiLiveStatus } from '../lib/gemini-live-session'
import { VideoFrameStreamer } from '../lib/video-frame-streamer'
import type { Language } from '../types'

export interface VoiceAssistantHandle {
  start: () => Promise<void>
  stop: () => Promise<void>
  isActive: () => boolean
}

interface VoiceAssistantProps {
  sessionId: string | null
  language: Language
  onAnswersUpdate: (answers: Record<string, unknown>) => void
  onStatusChange?: (status: GeminiLiveStatus) => void
}

function statusLabel(status: GeminiLiveStatus, language: Language): string {
  const labels: Record<GeminiLiveStatus, Record<Language, string>> = {
    idle: { vi: 'Sẵn sàng', en: 'Ready' },
    connecting: { vi: 'Đang kết nối...', en: 'Connecting...' },
    connected: { vi: 'Đã kết nối', en: 'Connected' },
    listening: { vi: 'Đang lắng nghe', en: 'Listening' },
    speaking: { vi: 'Bot đang nói', en: 'Speaking' },
    error: { vi: 'Lỗi', en: 'Error' },
  }
  return labels[status][language]
}

export const VoiceAssistant = forwardRef<VoiceAssistantHandle, VoiceAssistantProps>(
  function VoiceAssistant({ sessionId, language, onAnswersUpdate, onStatusChange }, ref) {
    const [status, setStatus] = useState<GeminiLiveStatus>('idle')
    const [transcript, setTranscript] = useState('')
    const [botMessage, setBotMessage] = useState('')
    const [error, setError] = useState('')
    const [cameraOn, setCameraOn] = useState(false)
    const [cameraLive, setCameraLive] = useState(false)
    const [cameraError, setCameraError] = useState('')
    const liveRef = useRef<GeminiLiveSession | null>(null)
    const ringRef = useRef<ConnectionRingtone | null>(null)
    const videoRef = useRef<HTMLVideoElement>(null)
    const videoStreamerRef = useRef<VideoFrameStreamer | null>(null)

    const updateStatus = (next: GeminiLiveStatus) => {
      setStatus(next)
      onStatusChange?.(next)
    }

    const stopCamera = async () => {
      await videoStreamerRef.current?.stop()
      videoStreamerRef.current = null
      setCameraLive(false)
    }

    const startCamera = async (session: GeminiLiveSession) => {
      const videoEl = videoRef.current
      if (!videoEl || !cameraOn) return

      setCameraError('')
      try {
        if (!videoStreamerRef.current) {
          videoStreamerRef.current = new VideoFrameStreamer()
        }
        await videoStreamerRef.current.start(videoEl, (frame) => {
          session.sendVideoFrame(frame)
        })
        setCameraLive(true)
      } catch (err) {
        setCameraLive(false)
        setCameraError(
          err instanceof Error
            ? err.message
            : language === 'vi'
              ? 'Không mở được webcam'
              : 'Could not open webcam',
        )
      }
    }

    useEffect(() => {
      ringRef.current = new ConnectionRingtone()
      return () => {
        void liveRef.current?.disconnect()
        void stopCamera()
        void ringRef.current?.stop()
        liveRef.current = null
        ringRef.current = null
      }
    }, [])

    useEffect(() => {
      void liveRef.current?.disconnect()
      void stopCamera()
      void ringRef.current?.stop()
      liveRef.current = null
      setStatus('idle')
      onStatusChange?.('idle')
      setTranscript('')
      setBotMessage('')
      setError('')
      setCameraError('')
      setCameraLive(false)
      // eslint-disable-next-line react-hooks/exhaustive-deps -- only reset when session changes
    }, [sessionId])

    useEffect(() => {
      const session = liveRef.current
      if (!session || status === 'idle' || status === 'error') return

      if (cameraOn) {
        void startCamera(session)
      } else {
        void stopCamera()
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps -- toggle camera during live session
    }, [cameraOn, status])

    const stopRingtone = () => {
      void ringRef.current?.stop()
    }

    const startVoice = async () => {
      if (!sessionId) return
      setError('')
      setBotMessage('')
      setCameraError('')

      await liveRef.current?.disconnect()
      await stopCamera()
      liveRef.current = null

      try {
        updateStatus('connecting')
        void ringRef.current?.start()

        const liveToken = await api.createLiveToken(sessionId)
        const session = new GeminiLiveSession()
        liveRef.current = session

        await session.connect(liveToken.token, liveToken.model, {
          onStatus: (next) => {
            updateStatus(next)
            if (next === 'connected') {
              stopRingtone()
              if (cameraOn) void startCamera(session)
            } else if (next === 'error' || next === 'idle') stopRingtone()
          },
          onBotText: (text) => setBotMessage((prev) => (prev ? `${prev}${text}` : text)),
          onUserText: setTranscript,
          onError: (message) => {
            stopRingtone()
            setError(message)
          },
          onFieldUpdate: async (fieldId, value) => {
            const updated = await api.updateAnswers(sessionId, { [fieldId]: value })
            startTransition(() => {
              onAnswersUpdate(updated.answers)
            })
            const progress = await api.getFormProgress(sessionId, fieldId)
            return { ...progress }
          },
          onBatchFieldUpdate: async (fields) => {
            if (Object.keys(fields).length === 0) {
              const progress = await api.getFormProgress(sessionId)
              return { ...progress, saved_count: 0 }
            }
            const updated = await api.updateAnswers(sessionId, fields)
            startTransition(() => {
              onAnswersUpdate(updated.answers)
            })
            const progress = await api.getFormProgress(sessionId)
            return { ...progress, saved_count: Object.keys(fields).length }
          },
        })
      } catch (err) {
        stopRingtone()
        await stopCamera()
        await liveRef.current?.disconnect()
        liveRef.current = null
        updateStatus('error')
        const message = err instanceof Error ? err.message : 'Failed to start Gemini Live'
        setError(message)
      }
    }

    const stopVoice = async () => {
      stopRingtone()
      await stopCamera()
      await liveRef.current?.disconnect()
      liveRef.current = null
      updateStatus('idle')
      setError('')
    }

    const isActive =
      status === 'connecting' ||
      status === 'connected' ||
      status === 'listening' ||
      status === 'speaking'

    useImperativeHandle(ref, () => ({
      start: startVoice,
      stop: stopVoice,
      isActive: () => isActive,
    }))

    if (!sessionId) return null

    return (
      <div className="voice-panel">
        <div className="voice-strip">
          <span className={`status-pill status-${status}`}>{statusLabel(status, language)}</span>
          {isActive && cameraLive && (
            <span className="voice-camera-badge">
              {language === 'vi' ? '📷 Bot đang xem webcam' : '📷 Bot viewing webcam'}
            </span>
          )}
          {error && <span className="voice-strip-error">{error}</span>}
          {!error && botMessage && <span className="voice-strip-bot">{botMessage}</span>}
          {!error && transcript && <span className="voice-strip-user">{transcript}</span>}
        </div>

        {isActive && (
          <div className="voice-camera-panel">
            <div className="voice-camera-video-wrap">
              <video ref={videoRef} className="voice-camera-video" playsInline muted />
              <div className="voice-camera-frame" aria-hidden="true" />
            </div>
            <div className="voice-camera-meta">
              <label className="voice-camera-toggle">
                <input
                  type="checkbox"
                  checked={cameraOn}
                  onChange={(e) => setCameraOn(e.target.checked)}
                />
                <span>
                  {language === 'vi'
                    ? 'Cho bot xem webcam (giấy tờ, thẻ BH)'
                    : 'Let bot see webcam (ID, insurance)'}
                </span>
              </label>
              <p className="voice-camera-hint">
                {language === 'vi'
                  ? 'Đưa CMND/hộ chiếu/bằng lái/thẻ BH vào khung và nói: "Đây là giấy tờ của tôi, đọc giúp tôi nhé."'
                  : 'Hold your ID/passport/license/insurance in frame and say: "This is my document, please read it."'}
              </p>
              {cameraError && <p className="voice-camera-error">{cameraError}</p>}
            </div>
          </div>
        )}
      </div>
    )
  },
)
