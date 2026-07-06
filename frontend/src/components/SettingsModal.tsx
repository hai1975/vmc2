import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { AppSettings, Language } from '../types'

interface SettingsModalProps {
  language: Language
  open: boolean
  onClose: () => void
}

export function SettingsModal({ language, open, onClose }: SettingsModalProps) {
  const [form, setForm] = useState<AppSettings | null>(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setError('')
    setMessage('')
    void api.getSettings().then(setForm).catch((err: Error) => setError(err.message))
  }, [open])

  if (!open) return null

  const save = async () => {
    if (!form) return
    setSaving(true)
    setError('')
    try {
      const updated = await api.updateSettings(form)
      setForm(updated)
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

        {form && (
          <div className="settings-form">
            <label className="settings-row checkbox-row">
              <input
                type="checkbox"
                checked={form.email_enabled === 'true'}
                onChange={(e) =>
                  setForm({ ...form, email_enabled: e.target.checked ? 'true' : 'false' })
                }
              />
              <span>{t('Gửi PDF qua email khi Submit', 'Email PDF on Submit')}</span>
            </label>

            <label>
              {t('Email người nhận (nút Email)', 'Recipient email (Email button)')}
              <input
                type="email"
                value={form.email_to}
                onChange={(e) => setForm({ ...form, email_to: e.target.value })}
                placeholder="clinic@example.com"
              />
            </label>
            <p className="settings-hint">
              {t(
                'Nhập email phòng khám, sau đó bấm nút Email trên thanh công cụ để gửi PDF đính kèm.',
                'Enter the clinic email, then use the Email button on the toolbar to send the PDF attachment.',
              )}
            </p>

            <label>
              SMTP Host
              <input
                type="text"
                value={form.smtp_host}
                onChange={(e) => setForm({ ...form, smtp_host: e.target.value })}
                placeholder="smtp.gmail.com"
              />
            </label>

            <label>
              SMTP Port
              <input
                type="text"
                value={form.smtp_port}
                onChange={(e) => setForm({ ...form, smtp_port: e.target.value })}
              />
            </label>

            <label>
              SMTP User
              <input
                type="text"
                value={form.smtp_user}
                onChange={(e) => setForm({ ...form, smtp_user: e.target.value })}
              />
            </label>

            <label>
              SMTP Password
              <input
                type="password"
                value={form.smtp_password === '***' ? '' : form.smtp_password}
                onChange={(e) => setForm({ ...form, smtp_password: e.target.value })}
                placeholder={form.smtp_password === '***' ? '••••••••' : ''}
              />
            </label>

            <label>
              From address
              <input
                type="email"
                value={form.smtp_from}
                onChange={(e) => setForm({ ...form, smtp_from: e.target.value })}
              />
            </label>
          </div>
        )}

        <footer className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            {t('Đóng', 'Close')}
          </button>
          <button type="button" className="btn-primary" disabled={!form || saving} onClick={() => void save()}>
            {saving ? t('Đang lưu...', 'Saving...') : t('Lưu', 'Save')}
          </button>
        </footer>
      </div>
    </div>
  )
}
