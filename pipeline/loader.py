"""
loader.py — books/<slug>/book.yaml + content/*.md → Book.

Um livro é só isto: metadados, uma cor e uma lista de arquivos.
Todo o resto vem da coleção.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import Art, Book, BookMeta, Chapter, Figure, OtherBook, Part
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
    cfg = load_config(slug)
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
    listed = preview_chapter_list(cfg) if cfg.get("preview_source") else None
    listed = listed or cfg.get("chapters")
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
    if cfg.get("preview_source"):
        book.outline = source_outline(cfg)
    book.others = other_books(slug)
    # Volumes irmãos: `@cap:` para um capítulo do outro volume vale, e vira
    # o número dele. A numeração dos volumes é contínua.
    for other in cfg.get("companions", []) or []:
        label = str(load_config(str(other)).get("volume_label", "") or "")
        for slug, number in book_outline(str(other)).items():
            if slug not in book.outline:
                book.outline[slug] = number
                if label:
                    book.outline_labels[slug] = label
    return book


def book_outline(slug: str) -> dict[str, int]:
    """slug → número de cada capítulo numerado de outro livro da coleção."""
    return source_outline({**load_config(slug), "preview_source": slug})


def other_books(slug: str) -> list[OtherBook]:
    """Os demais volumes da coleção que já têm capa, para a última página.

    Ficam de fora o próprio livro, o volume de que ele é prévia, as
    prévias e o modelo.
    """
    cfg = load_config(slug)
    skip = {slug, str(cfg.get("preview_source", "") or "")}
    found: list[tuple[int, OtherBook]] = []
    for other in list_books():
        if other in skip or other.endswith("-previa"):
            continue
        ocfg = load_config(other)
        if ocfg.get("preview_source"):
            continue
        cover = book_dir(other) / "assets" / Path(
            str(ocfg.get("cover_image", "") or "capa.png")).name
        if not cover.exists() or not _is_cover(cover):
            continue
        found.append((int(ocfg.get("volume", 0) or 0), OtherBook(
            slug=other, title=str(ocfg.get("title", other)),
            subtitle=str(ocfg.get("subtitle", "") or ""), cover=cover)))
    return [b for _, b in sorted(found, key=lambda x: (x[0], x[1].slug))]


def _is_cover(path: Path) -> bool:
    """Capa de verdade é retrato; a arte provisória da pipeline é quadrada."""
    from PIL import Image

    with Image.open(path) as img:
        return img.height > img.width


# ─── prévia ─────────────────────────────────────────────────────────────
# Uma prévia tem a mesma estrutura do volume completo: todos os capítulos,
# com as seções no sumário. Os que não estão liberados chegam com
# `previa: true` e imprimem só o aviso da edição completa.


def preview_allowed(cfg: dict[str, Any]) -> list[str]:
    """Capítulos do volume fonte liberados na prévia, na ordem do sumário."""
    names = [str(n) for n in cfg.get("chapters", []) or []]
    wanted = [str(v) for v in cfg.get("preview_chapters", []) or []]
    allowed: list[str] = []
    for name in names:
        for value in wanted:
            prefix = f"{int(value):02d}-" if value.isdigit() else None
            if name == value or (prefix and name.startswith(prefix)):
                allowed.append(name)
                break
    return allowed


def preview_chapter_list(cfg: dict[str, Any]) -> list[str]:
    """Arquivos da prévia: todos os capítulos do volume, na mesma ordem."""
    return [str(n) for n in cfg.get("chapters", []) or []]


def source_outline(cfg: dict[str, Any]) -> dict[str, int]:
    """slug → número de cada capítulo numerado do volume fonte."""
    from .parser import slugify

    source = book_dir(str(cfg["preview_source"])) / "content"
    outline: dict[str, int] = {}
    for name in cfg.get("chapters", []) or []:
        meta = chapter_front_matter(source / str(name))
        if meta.get("number") is None:
            continue
        slug = str(meta.get("slug", slugify(str(meta.get("title", name)))))
        outline[slug] = int(meta["number"])
    return outline


def chapter_front_matter(path: Path) -> dict[str, Any]:
    """Só o front matter de um capítulo, sem ler o corpo."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    _, front, _ = text.split("---", 2)
    return yaml.safe_load(front) or {}


def load_config(slug: str) -> dict[str, Any]:
    """Lê a configuração do livro, herdando a configuração de uma fonte."""
    d = book_dir(slug)
    cfg: dict[str, Any] = yaml.safe_load(
        (d / "book.yaml").read_text(encoding="utf-8")) or {}
    source_slug = str(cfg.get("preview_source", "") or "")
    if source_slug and source_slug != slug:
        base = load_config(source_slug)
        base.update(cfg)
        cfg = base
    return cfg


def asset_dir(book: Book) -> Path:
    """Retorna a pasta de assets própria ou herdada do volume fonte.

    Uma prévia gerada tem assets próprios — só as imagens dos capítulos
    liberados, em versão leve. Sem eles, herda os do volume fonte.
    """
    own = book.root / "assets"
    source_slug = str(book.meta.extra.get("preview_source", "") or "")
    if source_slug and own.exists() and any(own.iterdir()):
        return own
    if source_slug:
        source = book_dir(source_slug) / "assets"
        if source.exists():
            return source
    own = book.root / "assets"
    return own


_KNOWN = {
    "title", "subtitle", "author", "volume", "accent", "language", "isbn",
    "publisher", "year", "edition", "description", "keywords", "course_slug",
    "chapters", "parts", "theme",
}


def theme_overrides(slug: str) -> dict[str, Any]:
    cfg = load_config(slug)
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
