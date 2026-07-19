import { AdultEnForm } from './form-builder/adult-en'
import { AdultVnForm } from './form-builder/adult-vn'
import { ChildEnForm } from './form-builder/child-en'
import { ChildVnForm } from './form-builder/child-vn'
import { FormBindProvider } from './form-builder/form-context'
import { pageCountForForm } from '../lib/form-layout'
import type { FormSchema, Language } from '../types'
import '../form-builder-theme.css'

const SECTION_TITLES: Record<number, { en: string; vi: string }> = {
  1: {
    en: 'Personal / Insurance / Consent',
    vi: 'Cá nhân / Bảo hiểm / Đồng ý điều trị',
  },
  2: { en: 'Medical History', vi: 'Tiền sử bệnh' },
  3: {
    en: 'Lifestyle / Privacy / Contacts',
    vi: 'Lối sống / Quyền riêng tư / Liên hệ',
  },
  4: {
    en: 'Authorization for Release',
    vi: 'Ủy quyền tiết lộ thông tin',
  },
  5: { en: 'Signature', vi: 'Chữ ký' },
}

interface FormPanelProps {
  schema: FormSchema | null
  formId?: string | null
  answers: Record<string, unknown>
  language: Language
  activeFieldId?: string | null
  currentPage: number
  onPageChange: (page: number) => void
  onFieldChange?: (fieldId: string, value: unknown) => void | Promise<void>
}

function pickForm(formId: string) {
  switch (formId) {
    case 'adult_en':
      return <AdultEnForm />
    case 'adult_vn':
      return <AdultVnForm />
    case 'child_en':
      return <ChildEnForm />
    case 'child_vn':
      return <ChildVnForm />
    default:
      return null
  }
}

export function FormPanel({
  formId,
  answers,
  language,
  activeFieldId = null,
  currentPage,
  onPageChange,
  onFieldChange,
}: FormPanelProps) {
  if (!formId || formId === 'triage') {
    return (
      <div className="pdf-preview-empty">
        {language === 'vi'
          ? 'Bấm Nói và cho biết ngày sinh — form sẽ hiện sau khi chọn biểu mẫu.'
          : 'Press Speak and give your date of birth — the form appears after selection.'}
      </div>
    )
  }

  const form = pickForm(formId)
  if (!form) {
    return (
      <div className="pdf-preview-empty">
        {language === 'vi' ? `Không có panel cho form ${formId}` : `No panel for form ${formId}`}
      </div>
    )
  }

  const formLanguage: Language = formId.endsWith('_vn')
    ? 'vi'
    : formId.endsWith('_en')
      ? 'en'
      : language
  const total = pageCountForForm(formId)
  const title = SECTION_TITLES[currentPage]
  const titleText = title ? (formLanguage === 'vi' ? title.vi : title.en) : `Page ${currentPage}`

  return (
    <FormBindProvider
      value={{
        answers,
        activeFieldId,
        language: formLanguage,
        currentPage,
        onFieldChange,
      }}
    >
      <div className="w-full">
        <div className="form-section-nav flex flex-wrap items-center justify-between gap-2 px-3 sm:px-4 py-2 border-b border-border bg-card sticky top-0 z-10">
          <button
            type="button"
            className="px-3 py-1.5 text-sm border border-border rounded disabled:opacity-40"
            disabled={currentPage <= 1}
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          >
            {formLanguage === 'vi' ? '← Phần trước' : '← Previous'}
          </button>
          <div className="text-center text-sm">
            <div className="font-semibold">
              {formLanguage === 'vi' ? 'Phần' : 'Section'} {currentPage}/{total}
            </div>
            <div className="text-muted-foreground text-xs">{titleText}</div>
          </div>
          <button
            type="button"
            className="px-3 py-1.5 text-sm border border-border rounded disabled:opacity-40"
            disabled={currentPage >= total}
            onClick={() => onPageChange(Math.min(total, currentPage + 1))}
          >
            {formLanguage === 'vi' ? 'Phần sau →' : 'Next →'}
          </button>
        </div>
        <div className="w-full">{form}</div>
      </div>
    </FormBindProvider>
  )
}
