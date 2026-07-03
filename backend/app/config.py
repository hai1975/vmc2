from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_project_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / "backend" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_live_model: str = "gemini-3.1-flash-live-preview"
    gemini_vision_model: str = "gemini-2.5-flash"
    # Optional: separate Live model for Dutch MC (native-audio multilingual tuning)
    gemini_live_model_nl: str = "gemini-2.5-flash-native-audio-preview-12-2025"
    form_dir: Path = PROJECT_ROOT / "Form"
    schema_dir: Path = PROJECT_ROOT / "schemas"
    data_dir: Path = PROJECT_ROOT / "data"
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'vmc.db').as_posix()}"
    cors_origins: str = "http://localhost:5173,capacitor://localhost,http://localhost,https://hai1975.com,https://www.hai1975.com"
    # Set to /vmc-api when cPanel Python app URL is hai1975.com/vmc-api
    api_mount_path: str = ""

    @field_validator("form_dir", "schema_dir", "data_dir", mode="before")
    @classmethod
    def resolve_relative_paths(cls, value: str | Path) -> Path:
        return _resolve_project_path(Path(value))

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def output_pdf_dir(self) -> Path:
        return self.data_dir / "filled-pdfs"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.output_pdf_dir.mkdir(parents=True, exist_ok=True)
