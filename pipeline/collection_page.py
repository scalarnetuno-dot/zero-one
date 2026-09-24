"""
collection_page.py — a última página: os demais volumes da coleção.

As capas entram em miniatura, JPEG, para não pesar o PDF nem o EPUB.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from .model import Book, OtherBook

COLLECTION_DIR = "colecao"
THUMB_HEIGHT = 900
THUMB_QUALITY = 82


def other_cover_name(b: OtherBook) -> str:
    return f"{b.slug}.jpg"


def write_thumbnails(book: Book, dest: Path) -> list[Path]:
    """Grava em ``dest`` a miniatura da capa de cada volume indicado."""
    dest.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for b in book.others:
        img = Image.open(b.cover)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            fundo = Image.new("RGB", img.size, "white")
            fundo.paste(img, mask=img.split()[-1])
            img = fundo
        else:
            img = img.convert("RGB")
        img.thumbnail((img.width, THUMB_HEIGHT), Image.LANCZOS)
        path = dest / other_cover_name(b)
        img.save(path, "JPEG", quality=THUMB_QUALITY, optimize=True)
        out.append(path)
    return out
