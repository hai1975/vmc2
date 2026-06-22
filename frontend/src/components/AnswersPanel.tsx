import type { FormField, FormSchema, Language } from '../types'

interface AnswersPanelProps {
  schema: FormSchema | null
  answers: Record<string, unknown>
  language: Language
  onFieldChange: (fieldId: string, value: unknown) => void
  embedded?: boolean
}

function formatValue(field: FormField, value: unknown, language: Language): string {
  if (value === '__skipped__') {
    return language === 'vi' ? 'Không có' : 'None'
  }
  if (value === undefined || value === null || value === '') return '—'
  if (typeof value === 'boolean') return value ? '✓' : '✗'
  if (Array.isArray(value)) {
    return value
      .map((v) => field.options?.find((o) => o.value === v)?.label[language] ?? String(v))
      .join(', ')
  }
  if (field.options) {
    return field.options.find((o) => o.value === value)?.label[language] ?? String(value)
  }
  return String(value)
}

function renderInput(
  field: FormField,
  value: unknown,
  language: Language,
  onFieldChange: (fieldId: string, value: unknown) => void,
) {
  if (field.type === 'boolean') {
    return (
      <input
        type="checkbox"
        checked={Boolean(value)}
        onChange={(e) => onFieldChange(field.id, e.target.checked)}
      />
    )
  }
  if (field.type === 'select' && field.options) {
    return (
      <select
        value={String(value ?? '')}
        onChange={(e) => onFieldChange(field.id, e.target.value || null)}
      >
        <option value="">—</option>
        {field.options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label[language]}
          </option>
        ))}
      </select>
    )
  }
  if (field.type === 'multiselect' && field.options) {
    const selected = Array.isArray(value) ? (value as string[]) : []
    return (
      <div className="multiselect">
        {field.options.map((opt) => (
          <label key={opt.value}>
            <input
              type="checkbox"
              checked={selected.includes(opt.value)}
              onChange={(e) => {
                const next = e.target.checked
                  ? [...selected, opt.value]
                  : selected.filter((v) => v !== opt.value)
                onFieldChange(field.id, next)
              }}
            />
            {opt.label[language]}
          </label>
        ))}
      </div>
    )
  }
  return (
    <input
      type={field.type === 'date' ? 'date' : 'text'}
      value={String(value ?? '')}
      onChange={(e) => onFieldChange(field.id, e.target.value)}
    />
  )
}

export function AnswersPanel({ schema, answers, language, onFieldChange, embedded = false }: AnswersPanelProps) {
  if (!schema) return null

  const grouped = schema.sections
    .sort((a, b) => a.order - b.order)
    .map((section) => ({
      section,
      fields: schema.fields.filter((f) => f.section === section.id),
    }))

  const content = (
    <>
      {grouped.map(({ section, fields }) => (
        <div key={section.id} className="answer-section">
          <h3>{section.title[language]}</h3>
          {fields.map((field) => (
            <div key={field.id} className="answer-row">
              <label>
                {field.label[language]}
                {field.required ? ' *' : ''}
              </label>
              <div className="answer-input">{renderInput(field, answers[field.id], language, onFieldChange)}</div>
              <small className="answer-preview">{formatValue(field, answers[field.id], language)}</small>
            </div>
          ))}
        </div>
      ))}
    </>
  )

  if (embedded) {
    return <div className="answers-panel embedded">{content}</div>
  }

  return (
    <section className="card answers-panel">
      <h2>{language === 'vi' ? 'Thông tin đã điền' : 'Filled Information'}</h2>
      {content}
    </section>
  )
}
