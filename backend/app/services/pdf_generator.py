import base64
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.config import settings
from app.models import FormSchema
from app.services.form_registry import normalize_field_value, SKIPPED_VALUE, skipped_pdf_label

FONT_REGULAR = "VMC-Regular"
FONT_BOLD = "VMC-Bold"
TEXT_SIZE = 10
CHECK_SIZE = 11
BACKEND_ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = BACKEND_ROOT / "assets" / "fonts"
_FONTS_READY = False

# Page 1 top-right selfie; page 5 patient signature (PDF coords, origin bottom-left)
SELFIE_BOX = {"page": 1, "x": 468, "y": 668, "w": 118, "h": 108}
SIGNATURE_BOX = {"page": 5, "x": 88, "y": 120, "w": 240, "h": 72}


def _font_candidates(name: str) -> list[Path]:
    return [
        FONT_DIR / name,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        if name.startswith("arial")
        else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
        if name.startswith("arial")
        else Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("C:/Windows/Fonts/arial.ttf")
        if name.startswith("arial")
        else Path("C:/Windows/Fonts/arialbd.ttf"),
    ]


def _resolve_font(name: str) -> Path:
    import reportlab

    for candidate in _font_candidates(name):
        if candidate.exists():
            return candidate
    return Path(reportlab.__file__).parent / "fonts" / ("VeraBd.ttf" if "bd" in name else "Vera.ttf")


def _ensure_fonts() -> None:
    global _FONTS_READY
    if _FONTS_READY:
        return
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(_resolve_font("arial.ttf"))))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(_resolve_font("arialbd.ttf"))))
    _FONTS_READY = True


def _decode_data_url(data_url: str) -> bytes | None:
    if not data_url or not isinstance(data_url, str):
        return None
    try:
        payload = data_url.split(",", 1)[1] if "," in data_url else data_url
        return base64.b64decode(payload)
    except (ValueError, TypeError):
        return None


ImageOverlay = tuple[bytes, float, float, float, float]


def _draw_overlay_page(
    marks: list[tuple[str, float, float, str]],
    images: list[ImageOverlay] | None = None,
    page_width: float = 612,
    page_height: float = 792,
) -> bytes:
    _ensure_fonts()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    for img_bytes, x, y, w, h in images or []:
        try:
            c.drawImage(
                ImageReader(BytesIO(img_bytes)),
                x,
                y,
                width=w,
                height=h,
                preserveAspectRatio=True,
                anchor="sw",
                mask="auto",
            )
        except Exception:
            continue

    for text, x, y, kind in marks:
        if not text:
            continue
        if kind == "check":
            c.setFont(FONT_BOLD, CHECK_SIZE)
            c.drawString(x + 2, y, "X")
        else:
            c.setFont(FONT_REGULAR, TEXT_SIZE)
            c.drawString(x, y, str(text)[:120])

    c.save()
    buffer.seek(0)
    return buffer.read()


def _resolve_overlay_marks(field, value, language: str = "en") -> list[tuple[str, float, float, str]]:
    meta = field.validation or {}
    marks: list[tuple[str, float, float, str]] = []
    value = normalize_field_value(field, value)
    if value is None or value == "" or value == []:
        return marks

    if value == SKIPPED_VALUE:
        display = skipped_pdf_label(language)
        x = float(meta.get("x", 150))
        y = float(meta.get("y", 700))
        marks.append((display, x, y, "text"))
        return marks

    if field.type in ("select", "multiselect") and meta.get("checkbox_positions"):
        selected = value if isinstance(value, list) else [value]
        positions = meta["checkbox_positions"]
        for item in selected:
            pos = positions.get(str(item))
            if pos:
                marks.append(("X", float(pos["x"]), float(pos["y"]), "check"))
        return marks

    if isinstance(value, list):
        display = ", ".join(str(v) for v in value)
    elif isinstance(value, bool):
        if not value:
            return marks
        display = "X" if meta.get("render_as_check") else "Yes"
        kind = "check" if meta.get("render_as_check") else "text"
        x = float(meta.get("x", 150))
        y = float(meta.get("y", 700))
        marks.append((display, x, y, kind))
        return marks
    else:
        display = str(value)

    x = float(meta.get("x", 150))
    y = float(meta.get("y", 700))
    marks.append((display, x, y, "text"))
    return marks


def _attachment_overlays(answers: dict) -> dict[int, list[ImageOverlay]]:
    overlays: dict[int, list[ImageOverlay]] = {}

    selfie = _decode_data_url(str(answers.get("_selfie", "")))
    if selfie:
        box = SELFIE_BOX
        overlays.setdefault(box["page"], []).append(
            (selfie, box["x"], box["y"], box["w"], box["h"])
        )

    signature = _decode_data_url(str(answers.get("_signature", "")))
    if signature:
        box = SIGNATURE_BOX
        overlays.setdefault(box["page"], []).append(
            (signature, box["x"], box["y"], box["w"], box["h"])
        )

    return overlays


def generate_filled_pdf(
    form_id: str,
    schema: FormSchema,
    answers: dict,
    session_id: str,
    language: str = "en",
) -> Path:
    source_pdf = settings.form_dir / schema.filename
    if not source_pdf.exists():
        raise FileNotFoundError(f"PDF template not found: {schema.filename}")

    reader = PdfReader(str(source_pdf))
    writer = PdfWriter()

    text_overlays: dict[int, list[tuple[str, float, float, str]]] = {}
    for field in schema.fields:
        value = answers.get(field.id)
        if value is None or value == "" or value == []:
            continue
        for mark in _resolve_overlay_marks(field, value, language):
            text_overlays.setdefault(field.page, []).append(mark)

    image_overlays = _attachment_overlays(answers)
    all_pages = set(text_overlays) | set(image_overlays)

    for page_index, page in enumerate(reader.pages):
        page_num = page_index + 1
        if page_num in all_pages:
            page_w = float(page.mediabox.width)
            page_h = float(page.mediabox.height)
            overlay_bytes = _draw_overlay_page(
                text_overlays.get(page_num, []),
                image_overlays.get(page_num),
                page_w,
                page_h,
            )
            overlay_reader = PdfReader(BytesIO(overlay_bytes))
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    output_path = settings.output_pdf_dir / f"{session_id}_{form_id}.pdf"
    with output_path.open("wb") as f:
        writer.write(f)
    return output_path
