/** PDF Letter page size in points (matches ReportLab / schema coords). */
export const PDF_PAGE_WIDTH = 612
export const PDF_PAGE_HEIGHT = 792
export const PDF_TEXT_SIZE = 10
export const PDF_CHECK_SIZE = 11

export function pageCountForForm(formId: string | null | undefined): number {
  if (!formId || formId === 'triage') return 0
  if (formId.startsWith('child')) return 5
  if (formId.startsWith('adult')) return 4
  return 1
}

/** ReportLab / PDF origin is bottom-left; CSS is top-left. */
export function pdfYToCssTop(y: number, fontSize = PDF_TEXT_SIZE): number {
  return PDF_PAGE_HEIGHT - y - fontSize
}

export function isAnswerEmpty(value: unknown): boolean {
  return value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0)
}

export function displayAnswerText(value: unknown, language: 'en' | 'vi'): string {
  if (value === '__blank__') return ''
  if (value === '__skipped__') return language === 'vi' ? 'Không có' : 'None'
  if (Array.isArray(value)) return value.map(String).join(', ')
  if (typeof value === 'boolean') return value ? 'Yes' : ''
  return String(value ?? '')
}
