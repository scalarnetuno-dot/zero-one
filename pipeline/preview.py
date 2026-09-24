"""Gera o conteúdo de uma prévia a partir do volume completo.

A prévia tem a mesma estrutura do volume: todos os capítulos, com as
seções no sumário. Os liberados são copiados inteiros; os demais viram só
o front matter com `previa: true` e os títulos de seção — na página, o
capítulo abre e mostra o aviso da edição completa.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

from .loader import (
    BOOKS,
    book_dir,
    load_config,
    preview_allowed,
    preview_chapter_list,
)
from .model import Art, Figure
from .parser import parse_chapter

# Imagens da prévia: JPEG, largura máxima em pixels. A edição completa
# continua com os PNG originais.
PREVIEW_IMAGE_WIDTH = 1400
PREVIEW_COVER_HEIGHT = 1600
PREVIEW_JPEG_QUALITY = 82


def generate_preview(slug: str) -> list[Path]:
    """Materializa os capítulos da prévia ``slug``: inteiros ou fechados."""
    target = book_dir(slug)
    config = load_config(slug)
    source_slug = str(config.get("preview_source", "") or "")
    if not source_slug:
        paired = BOOKS / f"{slug}-previa"
        if (paired / "book.yaml").exists():
            return generate_preview(paired.name)
        raise ValueError(f"{slug}: book.yaml precisa de preview_source")

    source = book_dir(source_slug) / "content"
    allowed = preview_allowed(config)
    if not allowed:
        raise ValueError(f"{slug}: preview_chapters não libera nenhum capítulo")

    content = target / "content"
    content.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    opened: list[Path] = []
    for name in preview_chapter_list(config):
        source_file = source / name
        if not source_file.exists():
            raise FileNotFoundError(f"capítulo ausente no volume fonte: {source_file}")
        destination = content / name
        if name in allowed:
            shutil.copy2(source_file, destination)
            opened.append(destination)
        else:
            destination.write_text(_locked(source_file), encoding="utf-8")
        generated.append(destination)

    _light_assets(config, book_dir(source_slug), target, opened)

    # Arquivos de gerações anteriores (o antigo sumário avulso) saem.
    keep = set(preview_chapter_list(config))
    for stale in content.glob("*.md"):
        if stale.name not in keep:
            stale.unlink()

    return generated


def _light_assets(config: dict[str, Any], source_book: Path, target: Path,
                  chapters: list[Path]) -> None:
    """Copia, em JPEG reduzido, só as imagens que os capítulos liberados usam.

    As referências dos capítulos copiados passam a apontar para o `.jpg`.
    A capa entra também, com a mesma regra.
    """
    source_assets = source_book / "assets"
    dest = target / "assets"
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)

    used: set[str] = set()
    for path in chapters:
        for b in parse_chapter(path).walk():
            if isinstance(b, (Figure, Art)) and getattr(b, "src", ""):
                used.add(Path(b.src).name)

    renamed: dict[str, str] = {}
    for name in sorted(used):
        src = source_assets / name
        if src.exists():
            renamed[name] = _to_jpeg(src, dest, width=PREVIEW_IMAGE_WIDTH)

    cover = str(config.get("cover_image", "") or "capa.png")
    if (source_assets / cover).exists():
        _to_jpeg(source_assets / cover, dest, height=PREVIEW_COVER_HEIGHT)

    for path in chapters:
        text = path.read_text(encoding="utf-8")
        for old, new in renamed.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def _to_jpeg(src: Path, dest: Path, width: int = 0, height: int = 0) -> str:
    img = Image.open(src)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        fundo = Image.new("RGB", img.size, "white")
        fundo.paste(img, mask=img.split()[-1])
        img = fundo
    else:
        img = img.convert("RGB")
    limite = (width or img.width, height or img.height)
    img.thumbnail(limite, Image.LANCZOS)
    name = src.with_suffix(".jpg").name
    img.save(dest / name, "JPEG", quality=PREVIEW_JPEG_QUALITY, optimize=True)
    return name


def _locked(source_file: Path) -> str:
    """Capítulo fechado: o front matter com `previa: true` e as seções."""
    text = source_file.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"capítulo sem front matter: {source_file}")
    _, front, body = text.split("---", 2)
    lines = ["---", front.strip(), "previa: true", "---", ""]
    fenced = False
    for line in body.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"^#{2,3}\s+\S", line):
            lines += [line, ""]
    return "\n".join(lines)
