import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { api } from '../api/client'
import { ConnectionRingtone } from '../lib/connection-ring'
import { GeminiLiveSession, type GeminiLiveStatus } from '../lib/gemini-live-session'
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
    const liveRef = useRef<GeminiLiveSession | null>(null)
    const ringRef = useRef<ConnectionRingtone | null>(null)

    const updateStatus = (next: GeminiLiveStatus) => {
      setStatus(next)
      onStatusChange?.(next)
    }

    useEffect(() => {
      ringRef.current = new ConnectionRingtone()
      return () => {
        void liveRef.current?.disconnect()
        void ringRef.current?.stop()
        liveRef.current = null
        ringRef.current = null
      }
    }, [])

    useEffect(() => {
      void liveRef.current?.disconnect()
      void ringRef.current?.stop()
      liveRef.current = null
      setStatus('idle')
      onStatusChange?.('idle')
      setTranscript('')
      setBotMessage('')
      setError('')
      // eslint-disable-next-line react-hooks/exhaustive-deps -- only reset when session changes
    }, [sessionId])

    const stopRingtone = () => {
      void ringRef.current?.stop()
    }

    const startVoice = async () => {
      if (!sessionId) return
      setError('')
      setBotMessage('')

      await liveRef.current?.disconnect()
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
            if (next === 'connected') stopRingtone()
            else if (next === 'error' || next === 'idle') stopRingtone()
          },
          onBotText: (text) => setBotMessage((prev) => (prev ? `${prev}${text}` : text)),
          onUserText: setTranscript,
          onError: (message) => {
            stopRingtone()
            setError(message)
          },
          onFieldUpdate: async (fieldId, value) => {
            const updated = await api.updateAnswers(sessionId, { [fieldId]: value })
            onAnswersUpdate(updated.answers)
            const progress = await api.getFormProgress(sessionId)
            return { ...progress }
          },
        })
      } catch (err) {
        stopRingtone()
        await liveRef.current?.disconnect()
        liveRef.current = null
        updateStatus('error')
        const message = err instanceof Error ? err.message : 'Failed to start Gemini Live'
        setError(message)
      }
    }

    const stopVoice = async () => {
      stopRingtone()
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
      <div className="voice-strip">
        <span className={`status-pill status-${status}`}>{statusLabel(status, language)}</span>
        {error && <span className="voice-strip-error">{error}</span>}
        {!error && botMessage && <span className="voice-strip-bot">{botMessage}</span>}
        {!error && transcript && <span className="voice-strip-user">{transcript}</span>}
      </div>
    )
  },
)
