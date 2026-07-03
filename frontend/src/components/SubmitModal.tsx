import { useState } from 'react'
import type { Language } from '../types'
import { SelfieCapture } from './SelfieCapture'
import { SignaturePanel } from './SignaturePanel'

interface SubmitModalProps {
  language: Language
  open: boolean
  busy: boolean
  onClose: () => void
  onConfirm: (payload: { signature: string; selfie: string }) => void
}

export function SubmitModal({ language, open, busy, onClose, onConfirm }: SubmitModalProps) {
  const [selfie, setSelfie] = useState<string | null>(null)
  const [signature, setSignature] = useState<string | null>(null)

  if (!open) return null

  const canSubmit = Boolean(signature && selfie)

  const handleClose = () => {
    if (busy) return
    setSelfie(null)
    setSignature(null)
    onClose()
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-card submit-modal">
        <header className="modal-header">
          <h2>{language === 'vi' ? 'Hoàn tất đăng ký' : 'Complete registration'}</h2>
          <button type="button" className="modal-close" onClick={handleClose} aria-label="Close">
            ×
          </button>
        </header>

        <section className="submit-section">
          <h3>{language === 'vi' ? '1. Ảnh chân dung' : '1. Selfie photo'}</h3>
          <SelfieCapture language={language} value={selfie} onChange={setSelfie} />
        </section>

        <section className="submit-section">
          <h3>{language === 'vi' ? '2. Chữ ký' : '2. Signature'}</h3>
          <SignaturePanel language={language} onChange={setSignature} />
        </section>

        <footer className="modal-footer">
          <button type="button" className="btn-secondary" disabled={busy} onClick={handleClose}>
            {language === 'vi' ? 'Hủy' : 'Cancel'}
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={!canSubmit || busy}
            onClick={() => {
              if (signature && selfie) onConfirm({ signature, selfie })
            }}
          >
            {busy
              ? language === 'vi'
                ? 'Đang gửi...'
                : 'Submitting...'
              : language === 'vi'
                ? 'Submit'
                : 'Submit'}
          </button>
        </footer>
      </div>
    </div>
  )
}
