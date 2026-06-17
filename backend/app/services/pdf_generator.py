from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.config import settings
from app.models import FormSchema
from app.services.form_registry import normalize_field_value

FONT_REGULAR = "VMC-Regular"
FONT_BOLD = "VMC-Bold"
TEXT_SIZE = 10
CHECK_SIZE = 11
BACKEND_ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = BACKEND_ROOT / "assets" / "fonts"
_FONTS_READY = False


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


def _draw_overlay_page(
    marks: list[tuple[str, float, float, str]],
    page_width: float = 612,
    page_height: float = 792,
) -> bytes:
    _ensure_fonts()
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
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


def _resolve_overlay_marks(field, value) -> list[tuple[str, float, float, str]]:
    meta = field.validation or {}
    marks: list[tuple[str, float, float, str]] = []
    value = normalize_field_value(field, value)
    if value is None or value == "" or value == []:
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


def generate_filled_pdf(
    form_id: str,
    schema: FormSchema,
    answers: dict,
    session_id: str,
) -> Path:
    source_pdf = settings.form_dir / schema.filename
    if not source_pdf.exists():
        raise FileNotFoundError(f"PDF template not found: {schema.filename}")

    reader = PdfReader(str(source_pdf))
    writer = PdfWriter()

    overlays: dict[int, list[tuple[str, float, float, str]]] = {}
    for field in schema.fields:
        value = answers.get(field.id)
        if value is None or value == "" or value == []:
            continue
        for mark in _resolve_overlay_marks(field, value):
            overlays.setdefault(field.page, []).append(mark)

    for page_index, page in enumerate(reader.pages):
        page_num = page_index + 1
        if page_num in overlays:
            page_w = float(page.mediabox.width)
            page_h = float(page.mediabox.height)
            overlay_bytes = _draw_overlay_page(overlays[page_num], page_w, page_h)
            overlay_reader = PdfReader(BytesIO(overlay_bytes))
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    output_path = settings.output_pdf_dir / f"{session_id}_{form_id}.pdf"
    with output_path.open("wb") as f:
        writer.write(f)
    return output_path
