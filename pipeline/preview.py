"""Assets leves de uma prévia.

A prévia tem a mesma estrutura do volume: todos os capítulos, com as
seções no sumário. Os liberados saem inteiros; os demais abrem e mostram
o aviso da edição completa. Isso é resolvido pelo loader, na leitura —
aqui só se gera a versão reduzida, em JPEG, das imagens que a prévia usa.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from PIL import Image

from .loader import (
    BOOKS,
    book_dir,
    content_path,
    load_config,
    preview_allowed,
    split_translation,
)
from .model import Art, Figure
from .parser import parse_chapter

# Imagens da prévia: JPEG, largura máxima em pixels. A edição completa
# continua com os PNG originais.
PREVIEW_IMAGE_WIDTH = 1400
PREVIEW_COVER_HEIGHT = 1600
PREVIEW_JPEG_QUALITY = 82


def generate_preview(slug: str) -> list[Path]:
    """Gera os assets leves da prévia ``slug`` e devolve as imagens criadas.

    O texto da prévia não é copiado: o loader lê os capítulos do volume
    fonte e fecha, na hora, os que não estão em `preview_chapters`. Uma
    prévia é só um book.yaml — em qualquer idioma — mais estes JPEG.
    Traduções da prévia (`i18n/<idioma>/`) usam os mesmos JPEG.
    """
    base, _ = split_translation(slug)
    target = BOOKS / base
    config = load_config(base)
    source_slug = str(config.get("preview_source", "") or "")
    if not source_slug:
        paired = BOOKS / f"{base}-previa"
        if (paired / "book.yaml").exists():
            return generate_preview(paired.name)
        raise ValueError(f"{slug}: book.yaml precisa de preview_source")

    allowed = preview_allowed(config)
    if not allowed:
        raise ValueError(f"{slug}: preview_chapters não libera nenhum capítulo")

    opened = [content_path(source_slug, name)[0] for name in allowed]
    missing = [p for p in opened if not p.exists()]
    if missing:
        raise FileNotFoundError(f"capítulo ausente no volume fonte: {missing[0]}")

    # Conteúdo materializado por versões antigas da pipeline sai.
    shutil.rmtree(target / "content", ignore_errors=True)
    return _light_assets(config, book_dir(source_slug), target, opened)


def _light_assets(config: dict[str, Any], source_book: Path, target: Path,
                  chapters: list[Path]) -> list[Path]:
    """Copia, em JPEG reduzido, só as imagens que os capítulos liberados usam.

    Os capítulos continuam citando o `.png`: o loader troca pelo `.jpg`
    quando só ele existe. A capa entra também, com a mesma regra.
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

    made: list[Path] = []
    for name in sorted(used):
        src = source_assets / name
        if src.exists():
            made.append(dest / _to_jpeg(src, dest, width=PREVIEW_IMAGE_WIDTH))

    cover = str(config.get("cover_image", "") or "capa.png")
    if (source_assets / cover).exists():
        made.append(dest / _to_jpeg(source_assets / cover, dest,
                                    height=PREVIEW_COVER_HEIGHT))
    return made


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
