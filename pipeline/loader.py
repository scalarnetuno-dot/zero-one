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
    if (d / "book.yaml").exists():
        return d
    base, lang = split_translation(slug)
    if lang:
        return BOOKS / base / I18N / lang
    raise BookError(f"livro '{slug}' não encontrado em {BOOKS}")


def list_books(translations: bool = True) -> list[str]:
    """Os volumes em português e, logo depois de cada um, as traduções."""
    out: list[str] = []
    for p in sorted(BOOKS.glob("*/book.yaml")):
        slug = p.parent.name
        if slug.startswith("_"):
            continue
        out.append(slug)
        if translations:
            out += [f"{slug}-{lang}" for lang in book_languages(slug)]
    return out


# ─── traduções ──────────────────────────────────────────────────────────
# O português é a língua oficial da coleção: `books/<slug>/` é a fonte.
# Uma tradução mora dentro do volume, em `books/<slug>/i18n/<idioma>/`, e
# só traz o que muda: um book.yaml com os campos traduzidos e os capítulos
# traduzidos, com os MESMOS nomes de arquivo. Assets, estrutura, número,
# slug e parte de cada capítulo vêm do original — nada é duplicado.
#
# O slug de uma tradução é `<slug>-<idioma>`: php-one-v1-en, php-one-v1-es.
# Capítulo ainda não traduzido cai no original em português, com aviso.

I18N = "i18n"

# Campos estruturais do capítulo: vêm sempre do original.
STRUCTURAL = ("number", "slug", "part", "matter", "numbered")


def book_languages(slug: str) -> list[str]:
    """Idiomas para os quais o volume em português tem tradução."""
    d = BOOKS / slug / I18N
    return sorted(p.parent.name for p in d.glob("*/book.yaml")) if d.exists() else []


def split_translation(slug: str) -> tuple[str, str]:
    """`php-one-v1-en` → (`php-one-v1`, `en`). Original → (slug, "")."""
    if (BOOKS / slug / "book.yaml").exists():
        return slug, ""
    if "-" in slug:
        base, lang = slug.rsplit("-", 1)
        if (BOOKS / base / I18N / lang / "book.yaml").exists():
            return base, lang
    return slug, ""


def translated_slug(slug: str, lang: str) -> str:
    """O mesmo volume no idioma pedido, se a tradução existir."""
    if lang and (BOOKS / slug / I18N / lang / "book.yaml").exists():
        return f"{slug}-{lang}"
    return slug


def source_hash(path: Path) -> str:
    """Impressão digital do capítulo original, gravada na tradução.

    `source_hash` no front matter da tradução diz de qual versão do
    português ela partiu. Mudou o original, a tradução vira pendência.
    """
    import hashlib

    # Só o texto conta: BOM, CRLF do Windows (git autocrlf) e espaço no fim
    # da linha não fazem a tradução "envelhecer".
    text = path.read_bytes().decode("utf-8-sig", errors="replace")
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    norm = "\n".join(lines).strip("\n") + "\n"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]


def content_path(slug: str, name: str) -> tuple[Path, Path]:
    """(arquivo que será lido, original em português) de um capítulo."""
    base, lang = split_translation(slug)
    original = BOOKS / base / "content" / name
    if lang:
        translated = BOOKS / base / I18N / lang / "content" / name
        if translated.exists():
            return translated, original
    return original, original


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

    # De onde vêm os capítulos: do próprio volume ou, numa prévia, do volume
    # fonte — a prévia não guarda cópia de texto nenhum.
    source_slug = str(cfg.get("preview_source", "") or "") or slug
    names = [str(n) for n in cfg.get("chapters", []) or []]
    if not names:
        own = BOOKS / split_translation(source_slug)[0] / "content"
        names = sorted(p.name for p in own.glob("*.md"))
    allowed = set(preview_allowed(cfg)) if cfg.get("preview_source") else None

    chapters: list[Chapter] = []
    missing: list[str] = []
    untranslated: list[str] = []
    outdated: list[str] = []
    n = 0
    for name in names:
        path, original = content_path(source_slug, name)
        # Um livro de 40 capítulos nasce aos poucos: arquivo listado e ainda
        # não escrito vira aviso do validador, não erro de carga.
        if not path.exists():
            missing.append(name)
            continue
        overrides: dict[str, Any] = {}
        if path != original:
            front = chapter_front_matter(original)
            overrides = {k: front[k] for k in STRUCTURAL if k in front}
            done = str(chapter_front_matter(path).get("source_hash", "") or "")
            if done != source_hash(original):
                outdated.append(name)
        elif meta.language != _source_language(source_slug):
            untranslated.append(name)
        if allowed is not None and name not in allowed:
            overrides["previa"] = True
        ch = parse_chapter(path, overrides=overrides)
        if ch.matter == "body" and ch.numbered:
            n += 1
            if not ch.number:
                ch.number = n
            else:
                n = ch.number
        chapters.append(ch)
    if not chapters:
        raise BookError(f"nenhum capítulo encontrado para {slug}")


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
    book.untranslated = untranslated
    book.outdated = outdated
    book.ref_format = str(_strings(meta.language).get(
        "chapter_in_volume", "{number} do {label}"))
    for ch in chapters:
        _resolve_assets(ch, book)
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
    lang = split_translation(slug)[1]
    skip = {slug, str(cfg.get("preview_source", "") or "")}
    found: list[tuple[int, OtherBook]] = []
    for other in list_books(translations=False):
        other = translated_slug(other, lang)
        if other in skip or split_translation(other)[0].endswith("-previa"):
            continue
        ocfg = load_config(other)
        if ocfg.get("preview_source"):
            continue
        # Só volume no mesmo idioma, e com arte de capa própria desse idioma.
        if split_translation(other)[1] != lang:
            continue
        cover = cover_art_path(other, ocfg)
        if cover is None or not _is_cover(cover):
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

    source = str(cfg["preview_source"])
    outline: dict[str, int] = {}
    for name in cfg.get("chapters", []) or []:
        meta = chapter_front_matter(content_path(source, str(name))[1])
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
    """Lê a configuração do livro, herdando a configuração de uma fonte.

    Numa tradução, a ordem é: volume fonte já traduzido (se for prévia) →
    book.yaml original em português → book.yaml da tradução. As partes
    casam pelo `id`: a tradução só troca título e texto de abertura.
    """
    base_slug, lang = split_translation(slug)
    cfg = _read_yaml(BOOKS / base_slug / "book.yaml")
    if lang:
        tr = _read_yaml(BOOKS / base_slug / I18N / lang / "book.yaml")
        parts = _merge_parts(cfg.get("parts") or [], tr.pop("parts", None) or [])
        cfg.update(tr)
        if parts:
            cfg["parts"] = parts
        cfg["translation_of"] = base_slug
        cfg["companions"] = [translated_slug(str(c), lang)
                             for c in cfg.get("companions", []) or []]
        if cfg.get("preview_source"):
            cfg["preview_source"] = translated_slug(str(cfg["preview_source"]), lang)
    source_slug = str(cfg.get("preview_source", "") or "")
    if source_slug and source_slug != slug:
        base = load_config(source_slug)
        base.update(cfg)
        cfg = base
    # O book.yaml original declara pt-BR; a prévia traduzida às vezes não
    # declara nada. O idioma do slug decide.
    if lang and not str(cfg.get("language", "")).startswith(lang):
        cfg["language"] = lang
    return cfg


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _merge_parts(original: list[dict], translated: list[dict]) -> list[dict]:
    by_id = {str(p.get("id")): p for p in translated}
    return [{**p, **{k: v for k, v in by_id.get(str(p.get("id")), {}).items()
                     if k in ("title", "blurb")}}
            for p in original]


def _source_language(slug: str) -> str:
    base = split_translation(slug)[0]
    return str(_read_yaml(BOOKS / base / "book.yaml").get("language", "pt-BR"))


def _strings(language: str) -> dict[str, str]:
    coll = _read_yaml(COLLECTION / "collection.yaml").get("strings", {})
    return (coll.get(language) or coll.get(language.split("-")[0])
            or coll.get("pt-BR", {}))


def asset_dirs(book: Book) -> list[Path]:
    """Pastas de imagem do livro, da mais específica para a mais geral.

    Tradução: primeiro a pasta do idioma (arte com texto localizado), depois
    a do volume em português. Prévia: os assets leves dela; sem eles, os do
    volume fonte. Nada é copiado para dentro do repositório.
    """
    return _asset_chain(book.meta.slug)


def _asset_chain(slug: str) -> list[Path]:
    base, lang = split_translation(slug)
    chain: list[Path] = []
    if lang:
        chain.append(BOOKS / base / I18N / lang / "assets")
    own = BOOKS / base / "assets"
    cfg = load_config(slug)
    source = str(cfg.get("preview_source", "") or "")
    if source and not (own.exists() and any(own.iterdir())):
        chain += _asset_chain(source)
    else:
        chain.append(own)
    return [d for i, d in enumerate(chain) if d not in chain[:i]]


def asset_dir(book: Book) -> Path:
    """A pasta principal (a primeira que existe) — compatibilidade."""
    for d in asset_dirs(book):
        if d.exists() and any(d.iterdir()):
            return d
    return book.root / "assets"


def asset_path(book: Book, name: str) -> Path:
    """Onde mora `name`, seguindo a cadeia de pastas do livro."""
    name = Path(name).name
    dirs = asset_dirs(book)
    for d in dirs:
        if (d / name).exists():
            return d / name
    return dirs[-1] / name


def cover_art_path(slug: str, cfg: dict[str, Any] | None = None) -> Path | None:
    """A arte da capa: `cover_image:` ou capa.png.

    Tradução só usa arte da pasta do próprio idioma: a capa original traz
    título e frases em português desenhados na imagem. Sem arte traduzida,
    a capa sai só tipográfica, com o título no idioma do livro.
    """
    cfg = cfg if cfg is not None else load_config(slug)
    names = [Path(str(cfg["cover_image"])).name] if cfg.get("cover_image") else []
    names += ["capa.png", "capa.jpg", "capa.jpeg", "cover.png", "cover.jpg"]
    names += [Path(n).with_suffix(".jpg").name for n in names]
    base, lang = split_translation(slug)
    dirs = _asset_chain(slug)
    if lang:
        dirs = [BOOKS / base / I18N / lang / "assets"]
        source = str(cfg.get("preview_source", "") or "")
        if source:
            found = cover_art_path(source)
            if found is not None:
                return found
    for d in dirs:
        for name in names:
            if (d / name).exists():
                return d / name
    return None


_KNOWN = {
    "title", "subtitle", "author", "volume", "accent", "language", "isbn",
    "publisher", "year", "edition", "description", "keywords", "course_slug",
    "chapters", "parts", "theme",
}



def theme_overrides(slug: str) -> dict[str, Any]:
    cfg = load_config(slug)
    return cfg.get("theme", {}) or {}


def _resolve_assets(ch: Chapter, book: Book) -> None:
    """Normaliza caminhos de imagem para `assets/<arquivo>`.

    Vale para figura e para ilustração: quem troca o marcador pela arte
    escreve só o nome do arquivo, e a pipeline resolve onde ele mora. Numa
    prévia leve, `x.png` que só existe como `x.jpg` passa a apontar para ele.
    """
    for b in ch.walk():
        if isinstance(b, (Figure, Art)) and b.src:
            name = Path(b.src).name
            if not asset_path(book, name).exists():
                jpg = Path(name).with_suffix(".jpg").name
                if asset_path(book, jpg).exists():
                    name = jpg
            b.src = f"assets/{name}"
