"""Batch the installed pdf-to-markdown skill, preserve page facsimiles too.

Run from repository root with the course Python environment. Full reference
conversions are local and ignored by git; the coverage manifest is publishable.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def convert_one(item: tuple[int, Path], skill: Path, legacy: bool) -> dict:
    import pymupdf

    index, source = item
    destination = Path("Literature/converted") / f"book_{index:02d}"
    destination.mkdir(parents=True, exist_ok=True)
    markdown = destination / "book.md"
    log_path = destination / "conversion.log"
    if not markdown.exists():
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        with log_path.open("w", encoding="utf-8") as log:
            if legacy:
                # Use the bundled conversion logic, selecting the documented
                # legacy text-layout engine before invoking its entry point.
                wrapper = Path(__file__).with_name("run_pdf_skill.py")
                command = [sys.executable, str(wrapper), str(skill), str(source.resolve()),
                           "--output", str(markdown.resolve())]
            else:
                command = [sys.executable, str(skill), str(source.resolve()),
                           "--output", str(markdown.resolve())]
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        if result.returncode:
            raise RuntimeError(f"Conversion failed: {source.name}; see {log_path}")
    # Per-page facsimiles retain vectors, formulas and graphics even when the
    # converter cannot identify them as individual figure objects.
    facsimiles = destination / "pages"
    facsimiles.mkdir(exist_ok=True)
    manifest = []
    with pymupdf.open(source) as document:
        toc = document.get_toc()
        for page in document:
            image = facsimiles / f"page-{page.number+1:04}.jpg"
            if not image.exists():
                page.get_pixmap(dpi=110, alpha=False).save(str(image), jpg_quality=82)
            text = page.get_text()
            manifest.append({"page": page.number+1, "text_chars": len(text),
                             "raster_images": len(page.get_images()),
                             "vector_paths": len(page.get_drawings()),
                             "facsimile": f"pages/{image.name}"})
    text = markdown.read_text(encoding="utf-8")
    # Normalize long filenames with nested parentheses for portable MD parsers.
    images = destination / "book_images"
    for number, image in enumerate(sorted(images.glob("*.png")), 1):
        if image.name.startswith("figure-"):
            continue
        renamed = image.with_name(f"figure-{number:04d}.png")
        text = text.replace(f"book_images/{image.name}", f"book_images/{renamed.name}")
        image.rename(renamed)
    if "<!-- FACSIMILE -->" not in text:
        chunks = re.split(r"(<!-- Page (\d+) -->)", text)
        combined = [chunks[0]]
        for j in range(1, len(chunks), 3):
            marker, number, content = chunks[j:j+3]
            combined += [marker, content,
                         f"\n\n<!-- FACSIMILE -->\n[Визуальный оригинал PDF-страницы {number}](pages/page-{int(number):04d}.jpg)\n\n"]
        text = "".join(combined)
    markdown.write_text(text, encoding="utf-8")
    links = []
    for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
        if not target.startswith(("http", "data:")):
            links.append(target)
    missing = [target for target in links if not (markdown.parent / target).exists()]
    index_text = ["# Постраничный визуальный индекс", "",
                  "Факсимиле сохраняют весь видимый состав страницы; это не OCR-исправление.", ""]
    for row in manifest:
        index_text += [f"## PDF-страница {row['page']}",
                       f"![Страница {row['page']}]({row['facsimile']})", ""]
    (destination / "visual-index.md").write_text("\n".join(index_text), encoding="utf-8")
    info = {"id": f"B{index:02d}", "source": source.name,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "pages": len(manifest), "markdown_page_markers": len(re.findall(r"<!-- Page \d+ -->", text)),
            "figure_links": len(links), "missing_figure_links": missing,
            "facsimiles": len(manifest), "toc": toc, "page_inventory": manifest,
            "engine": "pdf-to-markdown skill / PyMuPDF4LLM", "legacy_layout": legacy}
    (destination / "manifest.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return {key:value for key,value in info.items() if key not in {"page_inventory", "toc"}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--legacy-layout", action="store_true")
    parser.add_argument("--only", type=int)
    args = parser.parse_args()
    skill = Path.home() / ".codex/skills/pdf-to-markdown/scripts/convert_pdf.py"
    books = list(enumerate(sorted(Path("Books").glob("*.pdf")), 1))
    if args.only:
        books = [item for item in books if item[0] == args.only]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(convert_one, item, skill, args.legacy_layout) for item in books]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps(result, ensure_ascii=True), flush=True)
    Path("Literature/conversion-summary.json").write_text(json.dumps(sorted(results,key=lambda x:x["id"]),
                                                               ensure_ascii=False,indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
