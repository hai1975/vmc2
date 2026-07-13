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
  const [pediatricAgeThreshold, setPediatricAgeThreshold] = useState('18')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setError('')
    setMessage('')
    void api
      .getSettings()
      .then((settings) => {
        setEmailTo(settings.email_to)
        setPediatricAgeThreshold(settings.pediatric_age_threshold || '18')
      })
      .catch((err: Error) => setError(err.message))
  }, [open])

  if (!open) return null

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const updated = await api.updateSettings({
        email_to: emailTo.trim(),
        pediatric_age_threshold: pediatricAgeThreshold.trim() || '18',
      })
      setEmailTo(updated.email_to)
      setPediatricAgeThreshold(updated.pediatric_age_threshold || '18')
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

          <label>
            {t('Tuổi trẻ em (dưới mức này = trẻ nhỏ)', 'Pediatric age (under = child form)')}
            <input
              type="number"
              min={1}
              max={25}
              value={pediatricAgeThreshold}
              onChange={(e) => setPediatricAgeThreshold(e.target.value)}
            />
          </label>
          <p className="settings-hint">
            {t(
              'Mặc định 18. Bot hỏi ngày sinh trước để chọn form người lớn hoặc trẻ em.',
              'Default 18. The bot asks date of birth first to pick adult or pediatric form.',
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
