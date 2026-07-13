import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { api, BOOT_TIMEOUT_MS } from './api/client'
import { AnswersPanel } from './components/AnswersPanel'
import { ContentTabs } from './components/ContentTabs'
import { DocumentScanModal } from './components/DocumentScanModal'
import { Header } from './components/Header'
import { LoadingSplash } from './components/LoadingSplash'
import { PdfPreview } from './components/PdfPreview'
import { SettingsModal } from './components/SettingsModal'
import { SubmitModal } from './components/SubmitModal'
import type { VoiceAssistantHandle } from './components/VoiceAssistant'
import type { GeminiLiveStatus } from './lib/gemini-live-session'
import type { FormSchema, FormSession, FormSummary, Language, SelectFormResult } from './types'
import './App.css'

const VoiceAssistant = lazy(() =>
  import('./components/VoiceAssistant').then((module) => ({ default: module.VoiceAssistant })),
)

const TRIAGE_FORM_ID = 'triage'

function formStatusLabel(
  formId: string | undefined,
  forms: FormSummary[],
  language: Language,
): string {
  if (!formId || formId === TRIAGE_FORM_ID) {
    return language === 'vi'
      ? 'Chưa chọn form — bấm Nói và cho biết ngày sinh'
      : 'Form pending — press Speak and tell us your date of birth'
  }
  const found = forms.find((f) => f.id === formId)
  return found?.title[language] ?? found?.title.en ?? formId
}

function App() {
  const [language, setLanguage] = useState<Language>('en')
  const [forms, setForms] = useState<FormSummary[]>([])
  const [schema, setSchema] = useState<FormSchema | null>(null)
  const [session, setSession] = useState<FormSession | null>(null)
  const [booting, setBooting] = useState(true)
  const [bootMessage, setBootMessage] = useState<string | undefined>()
  const [bootAttempt, setBootAttempt] = useState(0)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [voiceActive, setVoiceActive] = useState(false)
  const [submitOpen, setSubmitOpen] = useState(false)
  const [scanOpen, setScanOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [emailing, setEmailing] = useState(false)
  const voiceRef = useRef<VoiceAssistantHandle>(null)

  const activeFormId = session?.form_id
  const formReady = Boolean(activeFormId && activeFormId !== TRIAGE_FORM_ID)

  useEffect(() => {
    let cancelled = false
    const slowTimer = window.setTimeout(() => {
      if (!cancelled) {
        setBootMessage(
          language === 'vi'
            ? 'Đang đánh thức server (có thể mất 30–90 giây)...'
            : 'Waking server (may take 30–90 seconds)...',
        )
      }
    }, 12_000)

    async function boot() {
      setBooting(true)
      setBootMessage(undefined)
      setError('')

      const [listResult, schemaResult, sessionResult] = await Promise.allSettled([
        api.listForms(BOOT_TIMEOUT_MS),
        api.getSchema(TRIAGE_FORM_ID, BOOT_TIMEOUT_MS),
        api.createSession(TRIAGE_FORM_ID, language, BOOT_TIMEOUT_MS),
      ])

      if (cancelled) return

      if (listResult.status === 'fulfilled') {
        setForms(listResult.value)
      } else if (listResult.status === 'rejected') {
        setError(listResult.reason instanceof Error ? listResult.reason.message : 'Failed to load forms')
      }

      if (schemaResult.status === 'fulfilled') {
        setSchema(schemaResult.value)
      }

      if (sessionResult.status === 'fulfilled') {
        setSession(sessionResult.value)
        setMessage(
          language === 'vi'
            ? 'Sẵn sàng. Bấm Nói — bot sẽ hỏi ngày sinh để chọn form.'
            : 'Ready. Press Speak — the bot will ask your date of birth to pick the form.',
        )
      } else if (sessionResult.status === 'rejected') {
        const reason =
          sessionResult.reason instanceof Error ? sessionResult.reason.message : 'Failed to start session'
        setError((prev) => prev || reason)
      }

      setBooting(false)
      setBootMessage(undefined)
    }

    void boot()
    return () => {
      cancelled = true
      window.clearTimeout(slowTimer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- boot on mount / retry
  }, [bootAttempt])

  const handleFormSelected = async (result: SelectFormResult) => {
    setSession(result.session)
    const nextSchema = await api.getSchema(result.form_id)
    setSchema(nextSchema)
    const label = forms.find((f) => f.id === result.form_id)?.title[language]
    setMessage(
      language === 'vi'
        ? `Đã chọn form ${label ?? result.form_id} (tuổi ${result.patient_age}).`
        : `Selected ${label ?? result.form_id} (age ${result.patient_age}).`,
    )
  }

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

  const handleSubmitClick = () => {
    if (!session) return
    setSubmitOpen(true)
  }

  const handleSubmitConfirm = async (payload: { signature: string; selfie: string }) => {
    if (!session) return
    setSubmitting(true)
    setError('')
    try {
      const withAttachments = await api.updateAnswers(session.id, {
        _signature: payload.signature,
        _selfie: payload.selfie,
      })
      setSession(withAttachments)
      const submitted = await api.submitSession(session.id)
      setSession(submitted)
      setSubmitOpen(false)
      let msg =
        language === 'vi' ? 'Đã submit form thành công!' : 'Form submitted successfully!'
      if (submitted.email_sent) {
        msg += language === 'vi' ? ' PDF đã gửi email.' : ' PDF emailed.'
      } else if (submitted.email_error) {
        msg +=
          language === 'vi'
            ? ` (Gửi email lỗi: ${submitted.email_error})`
            : ` (Email failed: ${submitted.email_error})`
      }
      setMessage(msg)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submit failed')
    } finally {
      setSubmitting(false)
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

  const handleEmail = async () => {
    if (!session) return
    setError('')
    setEmailing(true)
    try {
      const result = await api.sendSessionEmail(session.id)
      setMessage(
        language === 'vi'
          ? `Đã gửi email đến ${result.to}.`
          : `Email sent to ${result.to}.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : language === 'vi' ? 'Gửi email thất bại' : 'Email failed')
    } finally {
      setEmailing(false)
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

  const waitingSession = !booting && !session && !error

  return (
    <div className="app-shell">
      <Header
        language={language}
        onLanguageChange={setLanguage}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {(booting || waitingSession) && (
        <LoadingSplash
          language={language}
          message={
            booting
              ? bootMessage
              : language === 'vi'
                ? 'Đang tạo phiên làm việc...'
                : 'Starting your session...'
          }
        />
      )}

      {error && (
        <div className="alert error">
          <span>{error}</span>
          <button type="button" className="alert-retry" onClick={() => setBootAttempt((n) => n + 1)}>
            {language === 'vi' ? 'Thử lại' : 'Retry'}
          </button>
        </div>
      )}
      {message && !booting && session && <div className="alert success">{message}</div>}

      <div className="toolbar-row card">
        <div className="form-status-wrap">
          <span className="form-select-label">{language === 'vi' ? 'Biểu mẫu' : 'Form'}</span>
          <span className="form-status-label">{formStatusLabel(activeFormId, forms, language)}</span>
        </div>

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
            disabled={!session || booting || !formReady}
            onClick={() => setScanOpen(true)}
            title={language === 'vi' ? 'Quét giấy tờ (webcam)' : 'Scan ID / insurance (webcam)'}
            aria-label={language === 'vi' ? 'Quét giấy tờ' : 'Scan document'}
          >
            <span className="icon-btn-symbol" aria-hidden="true">
              📷
            </span>
            <span className="icon-btn-label">{language === 'vi' ? 'Quét' : 'Scan'}</span>
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
            disabled={!session || booting || !formReady}
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
            className="icon-btn"
            disabled={!session || booting || emailing || !formReady}
            onClick={() => void handleEmail()}
            title={language === 'vi' ? 'Gửi PDF qua email' : 'Email PDF'}
            aria-label={language === 'vi' ? 'Gửi email' : 'Email'}
          >
            <span className="icon-btn-symbol" aria-hidden="true">
              ✉
            </span>
            <span className="icon-btn-label">{language === 'vi' ? 'Email' : 'Email'}</span>
          </button>

          <button
            type="button"
            className="icon-btn primary"
            disabled={!session || booting || !formReady}
            onClick={() => handleSubmitClick()}
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
            formId={session.form_id}
            language={language}
            onAnswersUpdate={(answers) => setSession((s) => (s ? { ...s, answers } : s))}
            onFormSelected={(result) => void handleFormSelected(result)}
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
            formId={activeFormId}
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
      <SubmitModal
        language={language}
        open={submitOpen}
        busy={submitting}
        onClose={() => setSubmitOpen(false)}
        onConfirm={(payload) => void handleSubmitConfirm(payload)}
      />
      <DocumentScanModal
        language={language}
        open={scanOpen}
        sessionId={session?.id ?? null}
        onClose={() => setScanOpen(false)}
        onSessionUpdate={(updated) => {
          setSession(updated)
          setMessage(
            language === 'vi'
              ? 'Đã cập nhật form từ giấy tờ quét.'
              : 'Form updated from scanned document.',
          )
        }}
      />
      <SettingsModal language={language} open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}

export default App
