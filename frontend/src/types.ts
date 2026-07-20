export type Language = 'vi' | 'en'

export interface FormSummary {
  id: string
  filename: string
  title: Record<Language, string>
  default: boolean
}

export interface FieldOption {
  value: string
  label: Record<Language, string>
}

export interface FieldValidation {
  x?: number
  y?: number
  maxLength?: number
  render_as_check?: boolean
  checkbox_positions?: Record<string, { x: number; y: number }>
}

export interface FormField {
  id: string
  type: string
  label: Record<Language, string>
  voice_prompt: Record<Language, string>
  required: boolean
  options?: FieldOption[]
  page: number
  section: string
  validation?: FieldValidation | null
}

export interface FormSchema {
  id: string
  filename: string
  title: Record<Language, string>
  sections: { id: string; title: Record<Language, string>; order: number }[]
  fields: FormField[]
}

export interface FormSession {
  id: string
  form_id: string
  status: 'draft' | 'submitted'
  language: Language
  answers: Record<string, unknown>
  filled_pdf_url: string | null
  created_at: string
  updated_at: string
  submitted_at: string | null
  email_sent?: boolean | null
  email_error?: string | null
}

export interface AppSettings {
  email_enabled: string
  email_to: string
  smtp_host: string
  smtp_port: string
  smtp_user: string
  smtp_password: string
  smtp_from: string
  pediatric_age_threshold: string
  pharmacy_list: string
  voice_gender: string
}

export interface LiveToken {
  token: string
  model: string
  expires_at: string
}

export interface VoiceConfig {
  form_id: string
  system_instruction: string
  fields: FormField[]
  gemini_model: string
  section_page?: number | null
}

export interface FormProgress {
  filled_fields: Record<string, unknown>
  missing_required: string[]
  missing_optional: string[]
  next_field_id: string | null
  next_field_page?: number | null
  total_pages?: number
  ready_to_submit: boolean
  all_fields_collected?: boolean
  filled_count?: number
  remaining_count?: number
  total_fields?: number
  section_page?: number | null
  section_complete?: boolean
  suggest_next_page?: number | null
  section_title_en?: string | null
  section_title_vi?: string | null
  global_remaining_count?: number | null
  global_next_field_id?: string | null
  global_next_field_page?: number | null
  next_field_ask_en?: string
  next_field_ask_vi?: string
  voice_instruction?: string
  say_next?: string | null
  say_next_en?: string | null
  say_next_vi?: string | null
}

export interface SelectFormResult {
  form_id: string
  patient_age: number
  is_pediatric: boolean
  session: FormSession
}

export interface EmailSendResult {
  ok: boolean
  to: string
  subject: string
  message: string
}

export interface ProviderLookupResult {
  query: string
  candidates: Array<{
    name: string
    address: string
    phone: string
    fax: string
    confidence: string
  }>
  message: string
}

export interface DocumentScanResult {
  detected_document: string
  extracted_fields: Record<string, unknown>
  applied_fields: Record<string, unknown>
  filled_count: number
  session: FormSession | null
}
