import type { Language } from '../types'

interface LoadingSplashProps {
  language: Language
  /** Full-screen overlay vs inline block */
  overlay?: boolean
  message?: string
}

export function LoadingSplash({ language, overlay = true, message }: LoadingSplashProps) {
  const label =
    message ??
    (language === 'vi' ? 'Đang kết nối VM Clinic...' : 'Connecting to VM Clinic...')

  return (
    <div className={`loading-splash${overlay ? ' loading-splash--overlay' : ''}`} role="status" aria-live="polite">
      <div className="loading-splash-card">
        <div className="loading-splash-logo-wrap">
          <img
            src={`${import.meta.env.BASE_URL}favicon.svg`}
            alt=""
            className="loading-splash-logo"
            aria-hidden
          />
        </div>
        <p className="loading-splash-text">{label}</p>
      </div>
    </div>
  )
}
