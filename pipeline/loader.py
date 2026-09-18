"""
loader.py — books/<slug>/book.yaml + content/*.md → Book.

Um livro é só isto: metadados, uma cor e uma lista de arquivos.
Todo o resto vem da coleção.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import Art, Book, BookMeta, Chapter, Figure, Part
from .parser import parse_chapter
from .theme import COLLECTION, ROOT

BOOKS = ROOT / "books"


class BookError(Exception):
    pass


def book_dir(slug: str) -> Path:
    d = BOOKS / slug
    if not (d / "book.yaml").exists():
        raise BookError(f"livro '{slug}' não encontrado em {BOOKS}")
    return d


def list_books() -> list[str]:
    return sorted(p.parent.name for p in BOOKS.glob("*/book.yaml")
                  if not p.parent.name.startswith("_"))


def load_book(slug: str) -> Book:
    d = book_dir(slug)
    cfg: dict[str, Any] = yaml.safe_load((d / "book.yaml").read_text(encoding="utf-8")) or {}
    coll = yaml.safe_load((COLLECTION / "collection.yaml").read_text(encoding="utf-8"))
    c = coll.get("collection", {})

    meta = BookMeta(
        title=str(cfg.get("title", slug)),
        subtitle=str(cfg.get("subtitle", "")),
        author=str(cfg.get("author", c.get("author_default", ""))),
        slug=slug,
        volume=int(cfg.get("volume", 0) or 0),
        accent=str(cfg.get("accent", "red")),
        language=str(cfg.get("language", c.get("language_default", "pt-BR"))),
        isbn=str(cfg.get("isbn", "") or ""),
        publisher=str(cfg.get("publisher", c.get("publisher", ""))),
        year=int(cfg.get("year", 0) or 0),
        edition=str(cfg.get("edition", "1ª edição")),
        description=str(cfg.get("description", "")),
        keywords=list(cfg.get("keywords", []) or []),
        course_slug=str(cfg.get("course_slug", "") or ""),
        extra={k: v for k, v in cfg.items() if k not in _KNOWN},
    )

    content = d / "content"
    listed = cfg.get("chapters")
    if listed:
        files = [content / f for f in listed]
    else:
        files = sorted(content.glob("*.md"))
    # Um livro de 40 capítulos nasce aos poucos: arquivo listado e ainda não
    # escrito vira aviso do validador, não erro de carga.
    missing = [f.name for f in files if not f.exists()]
    files = [f for f in files if f.exists()]
    if not files:
        raise BookError(f"nenhum capítulo encontrado em {content}")

    chapters: list[Chapter] = []
    n = 0
    for f in files:
        ch = parse_chapter(f)
        if ch.matter == "body" and ch.numbered:
            n += 1
            if not ch.number:
                ch.number = n
            else:
                n = ch.number
        chapters.append(ch)

    for ch in chapters:
        _resolve_assets(ch, d)

    parts = [
        Part(number=int(p.get("number", i + 1)), title=str(p.get("title", "")),
             blurb=str(p.get("blurb", "")), id=str(p.get("id", f"p{i + 1}")))
        for i, p in enumerate(cfg.get("parts", []) or [])
    ]
    known = {p.id for p in parts}
    for ch in chapters:
        if ch.part and ch.part not in known:
            raise BookError(
                f"{ch.source.name if ch.source else ch.slug}: parte "
                f"'{ch.part}' não existe em book.yaml (partes: {', '.join(sorted(known)) or '—'})")

    book = Book(meta=meta, chapters=chapters, parts=parts, root=d)
    book.missing = missing
    return book


_KNOWN = {
    "title", "subtitle", "author", "volume", "accent", "language", "isbn",
    "publisher", "year", "edition", "description", "keywords", "course_slug",
    "chapters", "parts", "theme",
}


def theme_overrides(slug: str) -> dict[str, Any]:
    cfg = yaml.safe_load((book_dir(slug) / "book.yaml").read_text(encoding="utf-8")) or {}
    return cfg.get("theme", {}) or {}


def _resolve_assets(ch: Chapter, d: Path) -> None:
    """Normaliza caminhos de imagem para `assets/<arquivo>`.

    Vale para figura e para ilustração: quem troca o marcador pela arte
    escreve só o nome do arquivo, e a pipeline resolve onde ele mora.
    """
    for b in ch.walk():
        if isinstance(b, Figure):
            b.src = f"assets/{Path(b.src).name}"
        elif isinstance(b, Art) and b.src:
            b.src = f"assets/{Path(b.src).name}"
