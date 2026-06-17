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

export interface FormField {
  id: string
  type: string
  label: Record<Language, string>
  voice_prompt: Record<Language, string>
  required: boolean
  options?: FieldOption[]
  page: number
  section: string
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
}

export interface FormProgress {
  filled_fields: Record<string, unknown>
  missing_required: string[]
  missing_optional: string[]
  next_field_id: string | null
  ready_to_submit: boolean
  all_fields_collected?: boolean
  next_field_ask_en?: string
  next_field_ask_vi?: string
}
