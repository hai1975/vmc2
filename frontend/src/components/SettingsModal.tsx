import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Language } from '../types'

interface SettingsModalProps {
  language: Language
  open: boolean
  onClose: () => void
}

export function SettingsModal({ language, open, onClose }: SettingsModalProps) {
  const [emailTo, setEmailTo] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setError('')
    setMessage('')
    void api
      .getSettings()
      .then((settings) => setEmailTo(settings.email_to))
      .catch((err: Error) => setError(err.message))
  }, [open])

  if (!open) return null

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const updated = await api.updateSettings({ email_to: emailTo.trim() })
      setEmailTo(updated.email_to)
      setMessage(language === 'vi' ? 'Đã lưu cài đặt.' : 'Settings saved.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const t = (vi: string, en: string) => (language === 'vi' ? vi : en)

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-card settings-modal">
        <header className="modal-header">
          <h2>{t('Cài đặt', 'Settings')}</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        <div className="settings-form">
          <label>
            {t('Email người nhận', 'Email To')}
            <input
              type="email"
              value={emailTo}
              onChange={(e) => setEmailTo(e.target.value)}
              placeholder="clinic@example.com"
            />
          </label>
          <p className="settings-hint">
            {t(
              'Email gửi qua n8n. Bấm nút Email trên thanh công cụ để gửi PDF đính kèm.',
              'Email is sent via n8n. Use the Email button on the toolbar to send the PDF attachment.',
            )}
          </p>
        </div>

        <footer className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            {t('Đóng', 'Close')}
          </button>
          <button type="button" className="btn-primary" disabled={saving} onClick={() => void save()}>
            {saving ? t('Đang lưu...', 'Saving...') : t('Lưu', 'Save')}
          </button>
        </footer>
      </div>
    </div>
  )
}
