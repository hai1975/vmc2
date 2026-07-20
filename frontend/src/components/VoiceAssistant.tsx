import { forwardRef, useEffect, useImperativeHandle, useRef, useState, startTransition } from 'react'
import { api } from '../api/client'
import { ConnectionRingtone } from '../lib/connection-ring'
import { GeminiLiveSession, type GeminiLiveStatus } from '../lib/gemini-live-session'
import { VideoFrameStreamer } from '../lib/video-frame-streamer'
import type { Language, SelectFormResult } from '../types'

export interface VoiceAssistantHandle {
  start: () => Promise<void>
  stop: () => Promise<void>
  isActive: () => boolean
}

interface VoiceAssistantProps {
  sessionId: string | null
  formId: string | null
  language: Language
  currentPage?: number
  onAnswersUpdate: (answers: Record<string, unknown>) => void
  onFormSelected?: (result: SelectFormResult) => void | Promise<void>
  onNavigatePage?: (
    action: 'next' | 'back' | 'goto',
    page?: number,
  ) => { ok: boolean; page: number; total_pages: number }
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
  function VoiceAssistant(
    {
      sessionId,
      formId,
      language,
      currentPage = 1,
      onAnswersUpdate,
      onFormSelected,
      onNavigatePage,
      onStatusChange,
    },
    ref,
  ) {
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
    const refusalRetryRef = useRef(0)
    const pageRef = useRef(currentPage)
    const reconnectingRef = useRef(false)
    const voiceActiveRef = useRef(false)
    const onNavigatePageRef = useRef(onNavigatePage)
    onNavigatePageRef.current = onNavigatePage

    /** Keep on-screen form on the same section the voicebot is collecting. */
    const syncFormToProgressPage = (progress: {
      global_next_field_page?: number | null
      suggest_next_page?: number | null
      next_field_page?: number | null
      section_complete?: boolean
      all_fields_collected?: boolean
    }) => {
      if (progress.all_fields_collected) return
      const target =
        (typeof progress.global_next_field_page === 'number' && progress.global_next_field_page) ||
        (progress.section_complete &&
          typeof progress.suggest_next_page === 'number' &&
          progress.suggest_next_page) ||
        (typeof progress.next_field_page === 'number' && progress.next_field_page) ||
        null
      if (target == null || target < 1) return
      if (target === pageRef.current) return
      onNavigatePageRef.current?.('goto', target)
    }

    const updateStatus = (next: GeminiLiveStatus) => {
      setStatus(next)
      const active =
        next === 'connecting' ||
        next === 'connected' ||
        next === 'listening' ||
        next === 'speaking'
      voiceActiveRef.current = active
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
      voiceActiveRef.current = false
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

    const sectionPageForApi = () => {
      if (!formId || formId === 'triage') return undefined
      return pageRef.current
    }

    const startVoice = async (opts?: { quiet?: boolean }) => {
      if (!sessionId) return
      setError('')
      setBotMessage('')
      setCameraError('')
      if (!opts?.quiet) refusalRetryRef.current = 0

      await liveRef.current?.disconnect()
      await stopCamera()
      liveRef.current = null

      try {
        updateStatus('connecting')
        if (!opts?.quiet) void ringRef.current?.start()

        const page = sectionPageForApi()
        const liveToken = await api.createLiveToken(sessionId, page)
        const voiceConfig = await api.getVoiceConfig(sessionId, page)
        const session = new GeminiLiveSession()
        liveRef.current = session

        await session.connect(
          liveToken.token,
          liveToken.model,
          {
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
              if (message.startsWith('MODEL_REFUSAL:') && refusalRetryRef.current < 1) {
                refusalRetryRef.current += 1
                setError(
                  language === 'vi'
                    ? 'Bot bị chặn tạm — đang kết nối lại...'
                    : 'Bot was blocked — reconnecting...',
                )
                window.setTimeout(() => {
                  void startVoice({ quiet: true })
                }, 600)
                return
              }
              setError(
                message.startsWith('MODEL_REFUSAL:')
                  ? language === 'vi'
                    ? 'Bot từ chối phiên — bấm Nói lại giúp.'
                    : 'Bot refused the session — tap Speak again.'
                  : message,
              )
            },
            onFieldUpdate: async (fieldId, value) => {
              const updated = await api.updateAnswers(sessionId, { [fieldId]: value })
              startTransition(() => {
                onAnswersUpdate(updated.answers)
              })
              const progress = await api.getFormProgress(
                sessionId,
                fieldId,
                sectionPageForApi(),
              )
              syncFormToProgressPage(progress)
              return { ...progress }
            },
            onBatchFieldUpdate: async (fields) => {
              if (Object.keys(fields).length === 0) {
                const progress = await api.getFormProgress(sessionId, undefined, sectionPageForApi())
                syncFormToProgressPage(progress)
                return { ...progress, saved_count: 0 }
              }
              const updated = await api.updateAnswers(sessionId, fields)
              startTransition(() => {
                onAnswersUpdate(updated.answers)
              })
              const progress = await api.getFormProgress(sessionId, undefined, sectionPageForApi())
              syncFormToProgressPage(progress)
              return { ...progress, saved_count: Object.keys(fields).length }
            },
            onProviderLookup: async (query) => api.lookupProvider(sessionId, query),
            onNavigatePage: async (action, page) => {
              const nav = onNavigatePageRef.current
              if (!nav) {
                return { ok: false, page: pageRef.current, total_pages: 0 }
              }
              return nav(action, page)
            },
          onFormSelect: async (dob, voiceLanguage) => {
            const result = await api.selectForm(sessionId, dob, voiceLanguage)
            startTransition(() => {
              onAnswersUpdate(result.session.answers)
            })
            setBotMessage('')
            await onFormSelected?.(result)
            pageRef.current = 1
            // Reconnect into the registration form session (page 1 tools + instructions).
            // Staying on the triage Live token leaves navigate_form_page broken (0 pages).
            window.setTimeout(() => {
              if (!voiceActiveRef.current) return
              if (reconnectingRef.current) return
              reconnectingRef.current = true
              void startVoice({ quiet: true })
            }, 400)
            const [progress, nextVoiceConfig] = await Promise.all([
              api.getFormProgress(sessionId, 'birthday', 1),
              api.getVoiceConfig(sessionId, 1),
            ])
            return {
              ...progress,
              registration_context: nextVoiceConfig.system_instruction,
              reconnect_soon: true,
            }
          },
          },
          { triage: voiceConfig.form_id === 'triage' },
        )
      } catch (err) {
        stopRingtone()
        await stopCamera()
        await liveRef.current?.disconnect()
        liveRef.current = null
        updateStatus('error')
        const message = err instanceof Error ? err.message : 'Failed to start Gemini Live'
        setError(message)
      } finally {
        reconnectingRef.current = false
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

    // Reconnect live session when user/bot switches section (avoids GoAway on long forms).
    useEffect(() => {
      if (pageRef.current === currentPage) return
      pageRef.current = currentPage
      if (!sessionId || !formId || formId === 'triage') return
      if (!voiceActiveRef.current) return
      if (reconnectingRef.current) return
      reconnectingRef.current = true
      void startVoice({ quiet: true })
      // eslint-disable-next-line react-hooks/exhaustive-deps -- reconnect only on page change
    }, [currentPage])

    const isActive =
      status === 'connecting' ||
      status === 'connected' ||
      status === 'listening' ||
      status === 'speaking'

    useImperativeHandle(ref, () => ({
      start: () => startVoice(),
      stop: stopVoice,
      isActive: () => isActive,
    }))

    if (!sessionId) return null

    return (
      <div className="voice-panel">
        <div className="voice-strip">
          <span className={`status-pill status-${status}`}>{statusLabel(status, language)}</span>
          {isActive && formId && formId !== 'triage' && (
            <span className="voice-camera-badge">
              {language === 'vi'
                ? `Phần ${currentPage}`
                : `Section ${currentPage}`}
            </span>
          )}
          {isActive && cameraLive && (
            <span className="voice-camera-badge">
              {language === 'vi' ? '📷 Bot đang xem webcam' : '📷 Bot viewing webcam'}
            </span>
          )}
          {error && <span className="voice-strip-error">{error}</span>}
          {!error && botMessage && <span className="voice-strip-bot">{botMessage}</span>}
          {!error && transcript && <span className="voice-strip-user">{transcript}</span>}
        </div>

        {isActive && formId && formId !== 'triage' && (
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
