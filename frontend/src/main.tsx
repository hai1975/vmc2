import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { wakeApi } from './api/client'
import './index.css'
import './form-builder-theme.css'
import App from './App.tsx'

wakeApi()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

const bootSplash = document.getElementById('boot-splash')
if (bootSplash) {
  requestAnimationFrame(() => {
    bootSplash.classList.add('boot-splash--hide')
    window.setTimeout(() => bootSplash.remove(), 280)
  })
}
