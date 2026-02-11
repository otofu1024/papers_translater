from __future__ import annotations

from pathlib import Path

import fitz


def render_pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int) -> list[Path]:
    if dpi <= 0:
        raise ValueError("dpi must be a positive integer.")
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            out_path = output_dir / f"{index:03d}.png"
            pix.save(out_path)
            rendered.append(out_path)

    return rendered

