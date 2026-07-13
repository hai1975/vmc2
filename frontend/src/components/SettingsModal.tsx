import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Language } from '../types'

interface SettingsModalProps {
  language: Language
  open: boolean
  onClose: () => void
}

interface PharmacyEntry {
  name: string
  address: string
  phone?: string
}

const DEFAULT_PHARMACY_LINES = [
  'Lavina Pharmacy | 8251 Westminster Blvd, Ste 100, Westminster, CA 92683 | +1 714-379-1179',
  'Professional Pharmacy | 7631 Westminster Blvd, Ste D, Westminster, CA 92683 | +1 714-893-2464',
  'Q Pharmacy | 8401 Westminster Blvd, Westminster, CA 92683 | +1 714-373-3023',
  'Walgreens Pharmacy | 8052 Westminster Blvd, Westminster, CA 92683 | +1 714-896-9589',
  'Hong Pharmacy | 8883 Westminster Blvd, Garden Grove, CA 92844 | +1 714-890-0331',
].join('\n')

function formatPharmacyLine(entry: PharmacyEntry): string {
  const phone = entry.phone?.trim()
  return phone ? `${entry.name} | ${entry.address} | ${phone}` : `${entry.name} | ${entry.address}`
}

function pharmaciesToText(raw: string): string {
  const text = raw.trim()
  if (!text) return DEFAULT_PHARMACY_LINES
  try {
    const parsed = JSON.parse(text) as PharmacyEntry[]
    if (!Array.isArray(parsed) || parsed.length === 0) return DEFAULT_PHARMACY_LINES
    return parsed
      .filter((item) => item?.name && item?.address)
      .map((item) => formatPharmacyLine(item))
      .join('\n')
  } catch {
    return text
  }
}

function textToPharmacyJson(text: string): string {
  const entries: PharmacyEntry[] = []
  for (const line of text.split('\n')) {
    const cleaned = line.replace(/^\s*\d+\s*[/.)-]\s*/, '').trim()
    if (!cleaned) continue
    if (cleaned.includes('|')) {
      const parts = cleaned.split('|').map((part) => part.trim())
      if (parts.length >= 2 && parts[0] && parts[1]) {
        const entry: PharmacyEntry = { name: parts[0], address: parts[1] }
        if (parts[2]) entry.phone = parts[2]
        entries.push(entry)
      }
      continue
    }
    if (cleaned.includes(':')) {
      const [name, address] = cleaned.split(':').map((part) => part.trim())
      if (name && address) entries.push({ name, address })
    }
  }
  return JSON.stringify(entries)
}

export function SettingsModal({ language, open, onClose }: SettingsModalProps) {
  const [emailTo, setEmailTo] = useState('')
  const [pediatricAgeThreshold, setPediatricAgeThreshold] = useState('18')
  const [pharmacyListText, setPharmacyListText] = useState(DEFAULT_PHARMACY_LINES)
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
        setPharmacyListText(pharmaciesToText(settings.pharmacy_list || ''))
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
        pharmacy_list: textToPharmacyJson(pharmacyListText),
      })
      setEmailTo(updated.email_to)
      setPediatricAgeThreshold(updated.pediatric_age_threshold || '18')
      setPharmacyListText(pharmaciesToText(updated.pharmacy_list || ''))
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

          <label>
            {t('Danh sách nhà thuốc gợi ý', 'Suggested pharmacy list')}
            <textarea
              rows={7}
              value={pharmacyListText}
              onChange={(e) => setPharmacyListText(e.target.value)}
              placeholder={DEFAULT_PHARMACY_LINES}
            />
          </label>
          <p className="settings-hint">
            {t(
              'Mỗi dòng: Tên | Địa chỉ | SĐT (SĐT tùy chọn). Bot tự điền SĐT khi gợi ý nhà thuốc; không có SĐT thì để trống trên PDF.',
              'One per line: Name | Address | Phone (phone optional). Bot auto-fills phone when suggesting; leaves PDF blank if no phone.',
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
