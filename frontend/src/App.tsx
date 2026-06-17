import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api/client'
import { AnswersPanel } from './components/AnswersPanel'
import { ContentTabs } from './components/ContentTabs'
import { FormSelector } from './components/FormSelector'
import { Header } from './components/Header'
import { PdfPreview } from './components/PdfPreview'
import { VoiceAssistant, type VoiceAssistantHandle } from './components/VoiceAssistant'
import type { GeminiLiveStatus } from './lib/gemini-live-session'
import type { FormSchema, FormSession, FormSummary, Language } from './types'
import './App.css'

function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [forms, setForms] = useState<FormSummary[]>([])
  const [selectedFormId, setSelectedFormId] = useState('')
  const [schema, setSchema] = useState<FormSchema | null>(null)
  const [session, setSession] = useState<FormSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [voiceActive, setVoiceActive] = useState(false)
  const voiceRef = useRef<VoiceAssistantHandle>(null)

  useEffect(() => {
    api
      .listForms()
      .then((list) => {
        setForms(list)
        const defaultForm = list.find((f) => f.default) ?? list[0]
        if (defaultForm) setSelectedFormId(defaultForm.id)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selectedFormId) return
    api.getSchema(selectedFormId).then(setSchema).catch((err: Error) => setError(err.message))
  }, [selectedFormId])

  const startSession = useCallback(async () => {
    if (!selectedFormId) return
    setError('')
    const created = await api.createSession(selectedFormId, language)
    setSession(created)
    setMessage(language === 'vi' ? 'Đã tạo phiên mới.' : 'New session created.')
  }, [selectedFormId, language])

  useEffect(() => {
    if (selectedFormId) startSession()
  }, [selectedFormId, startSession])

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

  if (loading) {
    return <div className="app-shell loading">{language === 'vi' ? 'Đang tải...' : 'Loading...'}</div>
  }

  return (
    <div className="app-shell">
      <Header language={language} onLanguageChange={setLanguage} />

      {error && <div className="alert error">{error}</div>}
      {message && <div className="alert success">{message}</div>}

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
            disabled={!session}
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
            disabled={!session}
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
            disabled={!session}
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
            disabled={!session}
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

      <VoiceAssistant
        ref={voiceRef}
        sessionId={session?.id ?? null}
        language={language}
        onAnswersUpdate={(answers) => setSession((s) => (s ? { ...s, answers } : s))}
        onStatusChange={handleVoiceStatusChange}
      />

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
