import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'
import {
  displayBoundText,
  fromDateInputValue,
  toDateInputValue,
  useFormBind,
} from './form-context'

/** Copied from https://github.com/hai1975/form-builder-pro — form-ui.tsx (+ bind via `name`) */
export function FormPage({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="w-full bg-muted/30 py-6 px-3 sm:px-4">
      <div className="w-full bg-card text-card-foreground shadow-md rounded-md p-6 sm:p-8 border border-border">
        <header className="text-center mb-6">
          <h1 className="text-2xl font-bold tracking-tight">VM CLINIC</h1>
          <p className="text-sm text-muted-foreground italic">Pediatric & Adult Medicine</p>
          <h2 className="mt-3 text-lg font-semibold underline">{title}</h2>
          {subtitle ? <p className="text-xs text-muted-foreground mt-1">{subtitle}</p> : null}
        </header>
        <form className="space-y-4 text-sm" onSubmit={(e) => e.preventDefault()}>
          {children}
        </form>
      </div>
    </div>
  )
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="pt-4 mt-4 border-t border-border">
      <h3 className="font-semibold underline mb-3">{title}</h3>
      <div className="space-y-3">{children}</div>
    </section>
  )
}

/** Show children only when FormBind currentPage matches (or when no page filter). */
export function PageGate({ page, children }: { page: number; children: ReactNode }) {
  const bind = useFormBind()
  if (bind?.currentPage != null && bind.currentPage !== page) return null
  return <>{children}</>
}

export function Row({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap items-end gap-4">{children}</div>
}

export function Field({
  label,
  name,
  className = 'flex-1 min-w-[200px]',
  type = 'text',
  ...rest
}: {
  label: string
  name?: string
  className?: string
} & InputHTMLAttributes<HTMLInputElement>) {
  const bind = useFormBind()
  const active = Boolean(name && bind?.activeFieldId === name)
  const raw = name && bind ? bind.answers[name] : undefined
  const value =
    name && bind
      ? type === 'date'
        ? toDateInputValue(raw)
        : displayBoundText(raw, bind.language)
      : rest.value

  return (
    <label
      className={`flex flex-col gap-1 ${className} ${active ? 'ring-2 ring-primary/40 rounded-sm bg-primary/5 px-1' : ''}`.trim()}
    >
      <span className="font-medium">{label}</span>
      <input
        {...rest}
        name={name}
        type={type}
        className="border-0 border-b border-foreground/60 bg-transparent px-1 py-1 focus:outline-none focus:border-primary"
        value={value ?? ''}
        onChange={(e) => {
          rest.onChange?.(e)
          if (name && bind?.onFieldChange) {
            const next = type === 'date' ? fromDateInputValue(e.target.value) : e.target.value
            void bind.onFieldChange(name, next)
          }
        }}
      />
    </label>
  )
}

export function TextArea({
  label,
  name,
  rows = 2,
  ...rest
}: {
  label: string
  name?: string
  rows?: number
} & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const bind = useFormBind()
  const active = Boolean(name && bind?.activeFieldId === name)
  const value =
    name && bind ? displayBoundText(bind.answers[name], bind.language) : rest.value

  return (
    <label
      className={`flex flex-col gap-1 w-full ${active ? 'ring-2 ring-primary/40 rounded-sm bg-primary/5 px-1' : ''}`.trim()}
    >
      <span className="font-medium">{label}</span>
      <textarea
        {...rest}
        name={name}
        rows={rows}
        className="border border-border rounded-sm bg-transparent px-2 py-1 focus:outline-none focus:border-primary"
        value={value ?? ''}
        onChange={(e) => {
          rest.onChange?.(e)
          if (name && bind?.onFieldChange) void bind.onFieldChange(name, e.target.value)
        }}
      />
    </label>
  )
}

export function Check({
  label,
  name,
  value: optionValue,
  multi = false,
  ...rest
}: {
  label: string
  name?: string
  /** Option value for select/multiselect groups; omit for boolean fields. */
  value?: string
  multi?: boolean
} & Omit<InputHTMLAttributes<HTMLInputElement>, 'value'>) {
  const bind = useFormBind()
  const active = Boolean(name && bind?.activeFieldId === name)
  let checked = rest.checked

  if (name && bind) {
    const current = bind.answers[name]
    if (optionValue !== undefined) {
      if (multi || Array.isArray(current)) checked = (Array.isArray(current) ? current : []).map(String).includes(optionValue)
      else checked = String(current ?? '') === optionValue
    } else {
      checked = current === true
    }
  }

  return (
    <label
      className={`inline-flex items-start gap-2 mr-4 ${active ? 'ring-2 ring-primary/40 rounded-sm bg-primary/5 px-1' : ''}`.trim()}
    >
      <input
        {...rest}
        type="checkbox"
        className="mt-0.5 h-4 w-4 accent-primary"
        checked={Boolean(checked)}
        onChange={(e) => {
          rest.onChange?.(e)
          if (!name || !bind?.onFieldChange) return
          if (optionValue !== undefined) {
            const current = bind.answers[name]
            if (multi || Array.isArray(current)) {
              const list = Array.isArray(current) ? current.map(String) : []
              const next = e.target.checked
                ? [...list, optionValue]
                : list.filter((v) => v !== optionValue)
              void bind.onFieldChange(name, next)
            } else {
              void bind.onFieldChange(name, e.target.checked ? optionValue : '')
            }
          } else {
            void bind.onFieldChange(name, e.target.checked)
          }
        }}
      />
      <span>{label}</span>
    </label>
  )
}

export type CheckItem = string | { label: string; value: string }

export function CheckGroup({
  title,
  items,
  name,
  multi = false,
}: {
  title: string
  items: CheckItem[]
  name?: string
  multi?: boolean
}) {
  const bind = useFormBind()
  const active = Boolean(name && bind?.activeFieldId === name)

  return (
    <div className={active ? 'ring-2 ring-primary/40 rounded-sm bg-primary/5 p-1' : undefined}>
      <p className="font-medium mb-1">{title}</p>
      <div className="flex flex-wrap gap-y-2">
        {items.map((item) => {
          const label = typeof item === 'string' ? item : item.label
          const value = typeof item === 'string' ? item : item.value
          return (
            <Check
              key={value}
              label={label}
              name={name}
              value={name ? value : undefined}
              multi={multi}
            />
          )
        })}
      </div>
    </div>
  )
}

export function Paragraph({ children }: { children: ReactNode }) {
  return <p className="text-xs leading-relaxed text-foreground/80">{children}</p>
}

/** Yes/No pair bound to a select field with values yes|no. */
export function YesNoCheck({
  title,
  name,
  yesLabel = 'Yes',
  noLabel = 'No',
}: {
  title: string
  name: string
  yesLabel?: string
  noLabel?: string
}) {
  return (
    <div>
      <p className="font-medium mb-1">{title}</p>
      <div className="flex flex-wrap gap-y-2">
        <Check label={yesLabel} name={name} value="yes" />
        <Check label={noLabel} name={name} value="no" />
      </div>
    </div>
  )
}
