import { useRef } from 'react'
import SignatureCanvas from 'react-signature-canvas'
import type { Language } from '../types'

interface SignaturePanelProps {
  language: Language
  onChange: (dataUrl: string | null) => void
}

export function SignaturePanel({ language, onChange }: SignaturePanelProps) {
  const padRef = useRef<SignatureCanvas>(null)

  const handleEnd = () => {
    if (!padRef.current || padRef.current.isEmpty()) {
      onChange(null)
      return
    }
    onChange(padRef.current.getCanvas().toDataURL('image/png'))
  }

  const clear = () => {
    padRef.current?.clear()
    onChange(null)
  }

  return (
    <div className="signature-panel">
      <p className="signature-hint">
        {language === 'vi' ? 'Ký tên trong khung bên dưới' : 'Sign in the box below'}
      </p>
      <div className="signature-canvas-wrap">
        <SignatureCanvas
          ref={padRef}
          penColor="#0f172a"
          minWidth={1.2}
          maxWidth={2.8}
          canvasProps={{
            className: 'signature-canvas',
            'aria-label': language === 'vi' ? 'Ký tên' : 'Signature',
          }}
          onEnd={handleEnd}
        />
      </div>
      <button type="button" className="btn-secondary" onClick={clear}>
        {language === 'vi' ? 'Xóa chữ ký' : 'Clear'}
      </button>
    </div>
  )
}
