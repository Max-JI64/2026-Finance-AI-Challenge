"""Extract and render the downloaded RE Stage 2 policy documents."""

from __future__ import annotations

import csv
import hashlib
import io
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fitz
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
from pypdf import PdfReader

from src.guards.re_stage2_guard import assert_stage2_action_allowed


RAW_ROOT = ROOT / "data" / "raw_re" / "policy" / "selected" / "2026-08-15"
PROCESSED_ROOT = ROOT / "data" / "processed_re" / "policy" / "re_stage2" / "extracted_text"
REPORT_ROOT = ROOT / "reports" / "re_stage2"
RENDER_ROOT = ROOT / "tmp" / "pdfs" / "re_stage2"
INVENTORY = REPORT_ROOT / "document_inventory.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_pdf(path: Path, output: Path, render_dir: Path) -> tuple[int, int]:
    reader = PdfReader(path)
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        pages.append(f"\n===== PAGE {index} =====\n{page.extract_text() or ''}")
    text = "\n".join(pages).strip() + "\n"
    output.write_text(text, encoding="utf-8")

    render_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(path)
    rendered: list[Path] = []
    for index, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
        rendered_path = render_dir / f"page_{index:03d}.png"
        pixmap.save(rendered_path)
        rendered.append(rendered_path)
    document.close()
    build_contact_sheet(rendered, render_dir / "contact_sheet.png")
    return len(reader.pages), len(text)


def build_contact_sheet(images: list[Path], output: Path) -> None:
    if not images:
        return
    thumb_width, thumb_height = 280, 380
    margin, label_height, columns = 16, 24, 3
    rows = (len(images) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (
            margin + columns * (thumb_width + margin),
            margin + rows * (thumb_height + label_height + margin),
        ),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    for index, path in enumerate(images):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height))
        column = index % columns
        row = index // columns
        x = margin + column * (thumb_width + margin)
        y = margin + row * (thumb_height + label_height + margin)
        canvas.paste(image, (x, y + label_height))
        draw.text((x, y), f"page {index + 1}", fill="black")
    canvas.save(output)


def extract_hwpx(path: Path, output: Path) -> tuple[int, int]:
    sections: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name for name in archive.namelist()
            if name.startswith("Contents/section") and name.endswith(".xml")
        )
        for name in names:
            root = ElementTree.fromstring(archive.read(name))
            texts = [
                element.text.strip()
                for element in root.iter()
                if element.tag.endswith("}t") and element.text and element.text.strip()
            ]
            sections.append(f"===== {name} =====\n" + "\n".join(texts))
    text = "\n\n".join(sections).strip() + "\n"
    output.write_text(text, encoding="utf-8")
    return len(sections), len(text)


def extract_html(path: Path, output: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    soup = BeautifulSoup(raw, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    text = "\n".join(lines) + "\n"
    output.write_text(text, encoding="utf-8")
    return 1, len(text)


def main() -> None:
    assert_stage2_action_allowed("extract_selected_policy_documents")
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    RENDER_ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(item for item in RAW_ROOT.rglob("*") if item.is_file()):
        policy_id = path.relative_to(RAW_ROOT).parts[0]
        suffix = path.suffix.lower()
        output_dir = PROCESSED_ROOT / policy_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"{path.name}.txt"
        if suffix == ".pdf":
            page_count, char_count = extract_pdf(
                path, output, RENDER_ROOT / policy_id / path.stem
            )
            signature_valid = path.read_bytes().startswith(b"%PDF-")
        elif suffix == ".hwpx":
            page_count, char_count = extract_hwpx(path, output)
            signature_valid = zipfile.is_zipfile(path)
        elif suffix == ".html":
            page_count, char_count = extract_html(path, output)
            signature_valid = b"<html" in path.read_bytes()[:4096].lower()
        else:
            continue
        rows.append(
            {
                "policy_id": policy_id,
                "source_path": path.relative_to(ROOT).as_posix(),
                "format": suffix.lstrip("."),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "page_or_section_count": page_count,
                "extracted_char_count": char_count,
                "signature_valid": "yes" if signature_valid else "no",
                "extracted_path": output.relative_to(ROOT).as_posix(),
            }
        )

    if not rows:
        raise RuntimeError("No selected policy documents were found")
    with INVENTORY.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"DOCUMENTS={len(rows)}")
    print(f"PDF_DOCUMENTS={sum(row['format'] == 'pdf' for row in rows)}")
    print(f"INVALID_SIGNATURES={sum(row['signature_valid'] == 'no' for row in rows)}")


if __name__ == "__main__":
    main()

