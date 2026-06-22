import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api/client'
import { AnswersPanel } from './components/AnswersPanel'
import { ContentTabs } from './components/ContentTabs'
import { FormSelector } from './components/FormSelector'
import { Header } from './components/Header'
import { LoadingSplash } from './components/LoadingSplash'
import { PdfPreview } from './components/PdfPreview'
import type { VoiceAssistantHandle } from './components/VoiceAssistant'
import type { GeminiLiveStatus } from './lib/gemini-live-session'
import type { FormSchema, FormSession, FormSummary, Language } from './types'
import './App.css'

const VoiceAssistant = lazy(() =>
  import('./components/VoiceAssistant').then((module) => ({ default: module.VoiceAssistant })),
)

const DEFAULT_FORM_ID = 'f-patient'

function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [forms, setForms] = useState<FormSummary[]>([])
  const [selectedFormId, setSelectedFormId] = useState(DEFAULT_FORM_ID)
  const [schema, setSchema] = useState<FormSchema | null>(null)
  const [session, setSession] = useState<FormSession | null>(null)
  const [booting, setBooting] = useState(true)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [voiceActive, setVoiceActive] = useState(false)
  const voiceRef = useRef<VoiceAssistantHandle>(null)
  const initialBootRef = useRef(true)

  useEffect(() => {
    if (initialBootRef.current) return
    if (!selectedFormId) return

    let cancelled = false
    setBooting(true)
    setError('')
    setSession(null)
    setSchema(null)

    void Promise.all([api.getSchema(selectedFormId), api.createSession(selectedFormId, language)])
      .then(([nextSchema, created]) => {
        if (cancelled) return
        setSchema(nextSchema)
        setSession(created)
        setMessage(language === 'vi' ? 'Đã tạo phiên mới.' : 'New session created.')
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setBooting(false)
      })

    return () => {
      cancelled = true
    }
  }, [selectedFormId, language])

  useEffect(() => {
    let cancelled = false

    async function boot() {
      setBooting(true)
      setError('')

      const [listResult, schemaResult, sessionResult] = await Promise.allSettled([
        api.listForms(),
        api.getSchema(DEFAULT_FORM_ID),
        api.createSession(DEFAULT_FORM_ID, language),
      ])

      if (cancelled) return

      if (listResult.status === 'fulfilled' && listResult.value.length > 0) {
        setForms(listResult.value)
        const defaultForm = listResult.value.find((f) => f.default) ?? listResult.value[0]
        if (defaultForm && defaultForm.id !== DEFAULT_FORM_ID) {
          initialBootRef.current = false
          setSelectedFormId(defaultForm.id)
          return
        }
      } else if (listResult.status === 'rejected') {
        setError(listResult.reason instanceof Error ? listResult.reason.message : 'Failed to load forms')
      }

      if (schemaResult.status === 'fulfilled') {
        setSchema(schemaResult.value)
      }

      if (sessionResult.status === 'fulfilled') {
        setSession(sessionResult.value)
        setMessage(language === 'vi' ? 'Đã tạo phiên mới.' : 'New session created.')
      } else if (sessionResult.status === 'rejected') {
        const reason =
          sessionResult.reason instanceof Error ? sessionResult.reason.message : 'Failed to start session'
        setError((prev) => prev || reason)
      }

      setBooting(false)
      initialBootRef.current = false
    }

    void boot()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- boot once on mount
  }, [])

  const handleFieldChange = async (fieldId: string, value: unknown) => {
    if (!session) return
    const updated = await api.updateAnswers(session.id, { [fieldId]: value })
    setSession(updated)
  }

  const handleSave = async () => {
    if (!session) return
    const saved = await api.saveSession(session.id)
    setSession(saved)
    setMessage(language === 'vi' ? 'Đã lưu bản nháp.' : 'Draft saved.')
  }

  const handleSubmit = async () => {
    if (!session) return
    try {
      const submitted = await api.submitSession(session.id)
      setSession(submitted)
      setMessage(language === 'vi' ? 'Đã submit form thành công!' : 'Form submitted successfully!')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Submit failed'
      setError(message)
    }
  }

  const handleDownload = async () => {
    if (!session) return
    setError('')
    try {
      const filename = `${session.form_id}_${session.id.slice(0, 8)}.pdf`
      await api.downloadPdf(session.id, filename)
      setMessage(language === 'vi' ? 'Đã tải PDF thành công!' : 'PDF downloaded successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed')
    }
  }

  const handleVoiceStatusChange = useCallback((status: GeminiLiveStatus) => {
    const active =
      status === 'connecting' ||
      status === 'connected' ||
      status === 'listening' ||
      status === 'speaking'
    setVoiceActive(active)
  }, [])

  const toggleVoice = async () => {
    if (!voiceRef.current) return
    if (voiceActive) {
      await voiceRef.current.stop()
    } else {
      await voiceRef.current.start()
    }
  }

  const waitingSession = !booting && selectedFormId && !session && !error

  return (
    <div className="app-shell">
      <Header language={language} onLanguageChange={setLanguage} />

      {(booting || waitingSession) && (
        <LoadingSplash
          language={language}
          message={
            booting
              ? undefined
              : language === 'vi'
                ? 'Đang tạo phiên làm việc...'
                : 'Starting your session...'
          }
        />
      )}

      {error && <div className="alert error">{error}</div>}
      {message && !booting && session && <div className="alert success">{message}</div>}

      <div className="toolbar-row card">
        <FormSelector
          forms={forms}
          selectedId={selectedFormId}
          language={language}
          onChange={setSelectedFormId}
        />

        <div className="toolbar-actions">
          <button
            type="button"
            className={`icon-btn speak-btn ${voiceActive ? 'active' : ''}`}
            disabled={!session || booting}
            onClick={() => void toggleVoice()}
            title={language === 'vi' ? 'Bắt đầu nói' : 'Start Speak'}
            aria-label={language === 'vi' ? 'Bắt đầu nói' : 'Start Speak'}
          >
            <span className="icon-btn-symbol" aria-hidden="true">
              {voiceActive ? '⏹' : '🎤'}
            </span>
            <span className="icon-btn-label">{language === 'vi' ? 'Nói' : 'Speak'}</span>
          </button>

          <button
            type="button"
            className="icon-btn"
            disabled={!session || booting}
            onClick={() => void handleSave()}
            title={language === 'vi' ? 'Lưu nháp' : 'Save'}
            aria-label={language === 'vi' ? 'Lưu nháp' : 'Save'}
          >
            <span className="icon-btn-symbol" aria-hidden="true">
              💾
            </span>
            <span className="icon-btn-label">{language === 'vi' ? 'Lưu' : 'Save'}</span>
          </button>

          <button
            type="button"
            className="icon-btn"
            disabled={!session || booting}
            onClick={() => void handleDownload()}
            title={language === 'vi' ? 'Tải PDF' : 'Download'}
            aria-label={language === 'vi' ? 'Tải PDF' : 'Download'}
          >
            <span className="icon-btn-symbol" aria-hidden="true">
              ⬇
            </span>
            <span className="icon-btn-label">{language === 'vi' ? 'Tải' : 'Download'}</span>
          </button>

          <button
            type="button"
            className="icon-btn primary"
            disabled={!session || booting}
            onClick={() => void handleSubmit()}
            title="Submit"
            aria-label="Submit"
          >
            <span className="icon-btn-symbol" aria-hidden="true">
              ✓
            </span>
            <span className="icon-btn-label">Submit</span>
          </button>
        </div>
      </div>

      {session && (
        <Suspense fallback={null}>
          <VoiceAssistant
            ref={voiceRef}
            sessionId={session.id}
            language={language}
            onAnswersUpdate={(answers) => setSession((s) => (s ? { ...s, answers } : s))}
            onStatusChange={handleVoiceStatusChange}
          />
        </Suspense>
      )}

      <ContentTabs
        language={language}
        pdfPanel={
          <PdfPreview
            embedded
            sessionId={session?.id ?? null}
            answers={session?.answers ?? {}}
            language={language}
          />
        }
        answersPanel={
          <AnswersPanel
            embedded
            schema={schema}
            answers={session?.answers ?? {}}
            language={language}
            onFieldChange={handleFieldChange}
          />
        }
      />
    </div>
  )
}

export default App
