from pydantic import BaseModel, Field


class FieldOption(BaseModel):
    value: str
    label: dict[str, str]


class FormField(BaseModel):
    id: str
    type: str  # text | date | email | phone | ssn | select | multiselect | boolean | textarea
    label: dict[str, str]
    voice_prompt: dict[str, str]
    required: bool = False
    options: list[FieldOption] | None = None
    validation: dict | None = None
    page: int = 1
    section: str = "general"
    depends_on: dict | None = None


class FormSection(BaseModel):
    id: str
    title: dict[str, str]
    order: int


class FormSchema(BaseModel):
    id: str
    filename: str
    title: dict[str, str]
    version: str = "1.0.0"
    default: bool = False
    sections: list[FormSection]
    fields: list[FormField]


class FormSummary(BaseModel):
    id: str
    filename: str
    title: dict[str, str]
    default: bool


class SessionCreate(BaseModel):
    form_id: str = "triage"
    language: str = "en"


class SessionUpdateAnswers(BaseModel):
    answers: dict[str, object]
    merge: bool = True


class SessionResponse(BaseModel):
    id: str
    form_id: str
    status: str
    language: str
    answers: dict[str, object]
    filled_pdf_url: str | None = None
    created_at: str
    updated_at: str
    submitted_at: str | None = None
    email_sent: bool | None = None
    email_error: str | None = None


class VoiceConfigResponse(BaseModel):
    form_id: str
    system_instruction: str
    fields: list[FormField]
    gemini_model: str = "gemini-2.5-flash-native-audio-preview-12-2025"


class LiveTokenResponse(BaseModel):
    token: str
    model: str
    expires_at: str


class FormProgressResponse(BaseModel):
    filled_fields: dict[str, object]
    missing_required: list[str]
    missing_optional: list[str]
    next_field_id: str | None = None
    ready_to_submit: bool = False
    all_fields_collected: bool = False
    filled_count: int = 0
    remaining_count: int = 0
    total_fields: int = 0
    next_field_required: bool | None = None
    next_field_ask_en: str | None = None
    next_field_ask_vi: str | None = None
    next_field_allowed_values: list[str] | None = None
    voice_instruction: str | None = None
    say_next: str | None = None
    say_next_en: str | None = None
    say_next_vi: str | None = None


class AppSettingsResponse(BaseModel):
    email_enabled: str = "false"
    email_to: str = ""
    smtp_host: str = ""
    smtp_port: str = "587"
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    pediatric_age_threshold: str = "18"
    pharmacy_list: str = ""
    voice_gender: str = "female"


class AppSettingsUpdate(BaseModel):
    email_enabled: str | None = None
    email_to: str | None = None
    smtp_host: str | None = None
    smtp_port: str | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    pediatric_age_threshold: str | None = None
    pharmacy_list: str | None = None
    voice_gender: str | None = None


class SelectFormRequest(BaseModel):
    dob: str
    voice_language: str = Field(default="en", description="vi if patient speaks Vietnamese, else en")


class SelectFormResponse(BaseModel):
    form_id: str
    patient_age: int
    is_pediatric: bool
    session: SessionResponse


class DocumentScanRequest(BaseModel):
    image: str = Field(description="Base64 data URL or raw base64 JPEG/PNG")
    doc_type: str = Field(default="auto", description="auto|id|passport|license|insurance")
    merge: bool = True


class DocumentScanResponse(BaseModel):
    detected_document: str
    extracted_fields: dict[str, object]
    applied_fields: dict[str, object]
    filled_count: int
    session: SessionResponse | None = None


class ProviderLookupRequest(BaseModel):
    query: str = Field(min_length=2, description="Partial doctor/clinic name or address")


class ProviderLookupResponse(BaseModel):
    query: str
    candidates: list[dict[str, str]]
    message: str


class EmailSendResponse(BaseModel):
    ok: bool = True
    to: str
    subject: str
    message: str
