import type { FormSummary, Language } from '../types'

interface FormSelectorProps {
  forms: FormSummary[]
  selectedId: string
  language: Language
  onChange: (formId: string) => void
}

export function FormSelector({ forms, selectedId, language, onChange }: FormSelectorProps) {
  return (
    <label className="form-select-wrap">
      <span className="form-select-label">{language === 'vi' ? 'Biểu mẫu' : 'Form'}</span>
      <select
        className="form-select"
        value={selectedId}
        onChange={(e) => onChange(e.target.value)}
      >
        {forms.map((form) => (
          <option key={form.id} value={form.id}>
            {form.title[language] ?? form.title.en}
          </option>
        ))}
      </select>
    </label>
  )
}
