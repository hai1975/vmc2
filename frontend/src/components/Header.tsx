import type { Language } from '../types'
import { LOGO_URL } from '../lib/brand'

interface HeaderProps {
  language: Language
  onLanguageChange: (lang: Language) => void
}

export function Header({ language, onLanguageChange }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <img src={LOGO_URL} alt="VM Clinic" className="brand-logo" />
        <div>
          <h1>VM Clinic</h1>
          <p>AI Voice Form Assistant</p>
        </div>
      </div>
      <div className="lang-switch">
        <button
          type="button"
          className={language === 'vi' ? 'active' : ''}
          onClick={() => onLanguageChange('vi')}
        >
          VI
        </button>
        <button
          type="button"
          className={language === 'en' ? 'active' : ''}
          onClick={() => onLanguageChange('en')}
        >
          EN
        </button>
      </div>
    </header>
  )
}
