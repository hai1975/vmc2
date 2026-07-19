import { createContext, useContext, type ReactNode } from 'react'

export type FormBindContextValue = {
  answers: Record<string, unknown>
  activeFieldId?: string | null
  language: 'en' | 'vi'
  currentPage?: number
  onFieldChange?: (fieldId: string, value: unknown) => void | Promise<void>
}

const FormBindContext = createContext<FormBindContextValue | null>(null)

export function FormBindProvider({
  value,
  children,
}: {
  value: FormBindContextValue
  children: ReactNode
}) {
  return <FormBindContext.Provider value={value}>{children}</FormBindContext.Provider>
}

export function useFormBind() {
  return useContext(FormBindContext)
}

export function displayBoundText(value: unknown, language: 'en' | 'vi'): string {
  if (value === undefined || value === null || value === '__blank__') return ''
  if (value === '__skipped__') return language === 'vi' ? 'Không có' : 'None'
  if (typeof value === 'boolean') return value ? 'true' : ''
  if (Array.isArray(value)) return value.map(String).join(', ')
  return String(value)
}

/** Convert stored MM/DD/YYYY or other formats to yyyy-MM-dd for input[type=date]. */
export function toDateInputValue(value: unknown): string {
  const raw = String(value ?? '').trim()
  if (!raw || raw === '__skipped__' || raw === '__blank__') return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw
  const mdy = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/)
  if (mdy) {
    const [, m, d, y] = mdy
    return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`
  }
  return raw
}

export function fromDateInputValue(value: string): string {
  if (!value) return ''
  const ymd = value.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (ymd) {
    const [, y, m, d] = ymd
    return `${m}/${d}/${y}`
  }
  return value
}
