"""
cover.py — capa em dois formatos, um só desenho.

  front  → uma página no tamanho do miolo. Vira a página 1 do PDF de leitura
           e a capa do EPUB (PNG em 300 DPI).
  wrap   → contracapa + lombada + capa, com sangria, para a KDP impressa.

A largura da lombada é função do número de páginas, então o modo `wrap` só
pode ser gerado depois do miolo.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import typst

from .loader import asset_dir, book_dir, load_book, theme_overrides
from .model import Book
from .theme import FONTS, Theme, _mm, load_theme

# Espessura do papel na KDP, por página impressa.
PAPER_MM_PER_PAGE = {"white": 0.0572, "cream": 0.0635, "color": 0.0596}
BLEED_MM = 3.175
SPINE_TEXT_MIN_PAGES = 100   # abaixo disso a KDP não aceita texto na lombada
COVER_ART_NAMES = ("capa.png", "capa.jpg", "capa.jpeg", "cover.png", "cover.jpg")


def spine_width(pages: int, paper: str = "white") -> float:
    return pages * PAPER_MM_PER_PAGE.get(paper, PAPER_MM_PER_PAGE["white"])


def find_cover_art(slug: str, book: Book | None = None) -> Path | None:
    """A arte da capa do volume: `cover_image:` no book.yaml ou assets/capa.png."""
    book = book or load_book(slug)
    d = book.root
    named = book.meta.extra.get("cover_image")
    if named:
        p = asset_dir(book) / Path(str(named)).name
        return p if p.exists() else None
    for name in COVER_ART_NAMES:
        p = asset_dir(book) / name
        if p.exists():
            return p
    return None


def _sources(slug: str, mode: str, pages: int, out: Path,
             paper: str = "white") -> tuple[Path, Path]:
    book = load_book(slug)
    theme = load_theme(accent=book.meta.accent, language=book.meta.language,
                       overrides=theme_overrides(slug))
    m = book.meta
    coll = theme.collection.get("collection", {})

    src_dir = out / "typst"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Paleta do embrulho: o livro declara as cores da arte; sem isso,
    # a contracapa usa o neutro da coleção.
    padrao = {
        "bg": theme.t("color.paper"),
        "panel": theme.accent_hex,
        "accent": theme.accent_hex,
        "ink": theme.t("color.ink"),
        "ink_soft": theme.t("color.ink_soft"),
    }
    palette = {**padrao, **(m.extra.get("cover_palette") or {})}

    art = find_cover_art(slug, book)
    if art:
        dest = src_dir / "assets" / art.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.stat().st_mtime < art.stat().st_mtime:
            shutil.copy2(art, dest)

    typ = theme.render(
        "cover.typ.j2",
        mode=mode,
        trim_w=_mm(theme.t("page.trim.width")),
        trim_h=_mm(theme.t("page.trim.height")),
        spine=round(spine_width(pages, paper), 2),
        bleed=BLEED_MM,
        spine_text=pages >= SPINE_TEXT_MIN_PAGES,
        cover_image=f"assets/{art.name}" if art else "",
        cover_full=bool(m.extra.get("cover_full", False)),
        palette=palette,
        title=m.title,
        subtitle=m.subtitle,
        author=m.author,
        volume=m.volume or 0,
        description=m.description,
        bullets=[str(b) for b in (m.extra.get("cover_bullets") or [])][:5],
        publisher=m.publisher or coll.get("publisher", ""),
        collection_name=coll.get("name", ""),
        isbn=m.isbn,
        lang=m.language.split("-")[0],
    )
    suffix = "capa-kdp" if mode == "wrap" else "capa"
    src = src_dir / f"{slug}-{suffix}.typ"
    src.write_text(typ, encoding="utf-8")
    return src, src_dir


def build_front(slug: str, out: Path, png: bool = True) -> tuple[Path, Path | None]:
    """Capa sozinha: PDF de uma página (+ PNG para o EPUB)."""
    src, root = _sources(slug, "front", 0, out)
    pdf = out / f"{slug}-capa.pdf"
    compiler = typst.Compiler(input=src, root=root, font_paths=[FONTS],
                              ignore_system_fonts=True)
    compiler.compile(output=pdf)
    img = None
    if png:
        data = compiler.compile(format="png", ppi=300)
        img = out / f"{slug}-capa.png"
        img.write_bytes(data[0] if isinstance(data, list) else data)
    return pdf, img


def build_wrap(slug: str, pages: int, out: Path, paper: str = "white") -> Path:
    """Capa completa para impressão: contracapa + lombada + capa, com sangria."""
    src, root = _sources(slug, "wrap", pages, out, paper)
    pdf = out / f"{slug}-capa-kdp.pdf"
    typst.Compiler(input=src, root=root, font_paths=[FONTS],
                   ignore_system_fonts=True).compile(output=pdf)
    return pdf


def merge_with_cover(cover_pdf: Path, interior: Path, dest: Path) -> Path:
    """PDF de leitura: capa como página 1, miolo em seguida."""
    import logging

    from pypdf import PdfWriter

    # juntar capa + miolo acusa "annotation sizes differ" (links do sumário):
    # é ruído do pypdf, não defeito do PDF.
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    w = PdfWriter()
    w.append(str(cover_pdf))
    w.append(str(interior))
    with dest.open("wb") as fh:
        w.write(fh)
    return dest
