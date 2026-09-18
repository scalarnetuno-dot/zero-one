"""
placeholder.py — arte provisória, gerada localmente.

Enquanto as ilustrações definitivas não chegam, a pipeline precisa de
imagens de verdade para exercitar o caminho todo: resolução, DPI, sangria,
posição na página, peso do EPUB. Estas servem de dublê.

São desenhadas com Pillow a partir de uma semente (o nome do arquivo), em
300 DPI, na paleta da coleção: neutros + a cor do volume. Nada baixado,
nada com licença de terceiros — se uma escapar para a gráfica, o estrago
é estético, não jurídico.

    python -m pipeline art java-one            # capa + 2 figuras
    python -m pipeline art java-one --figures 4
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

from PIL import Image, ImageDraw

DPI = 300


def _rng(seed: str) -> random.Random:
    return random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:12], 16))


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def figure(path: Path, accent: str, seed: str | None = None,
           size: tuple[int, int] = (2100, 1400)) -> Path:
    """Composição geométrica abstrata — dublê de diagrama ou foto."""
    rng = _rng(seed or path.stem)
    w, h = size
    ink = _hex("#16181A")
    soft = _hex("#B6BCC4")
    acc = _hex(accent)

    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    cols, rows = rng.choice([(7, 5), (9, 6), (5, 4)])
    cw, ch = w / cols, h / rows
    pad = min(cw, ch) * 0.12

    for r in range(rows):
        for c in range(cols):
            x0, y0 = c * cw + pad, r * ch + pad
            x1, y1 = (c + 1) * cw - pad, (r + 1) * ch - pad
            roll = rng.random()
            weight = rng.choice([0.0, 0.0, 0.12, 0.25, 1.0])
            color = acc if weight == 1.0 else _mix((255, 255, 255), ink, weight)
            if roll < 0.30:
                continue
            if roll < 0.55:
                d.rectangle([x0, y0, x1, y1], outline=soft, width=max(2, int(w / 700)))
            elif roll < 0.75:
                d.rectangle([x0, y0, x1, y1], fill=color)
            elif roll < 0.90:
                d.ellipse([x0, y0, x1, y1], fill=color)
            else:
                d.line([x0, y1, x1, y0], fill=color, width=max(3, int(w / 380)))

    d.rectangle([0, 0, w - 1, h - 1], outline=soft, width=max(2, int(w / 900)))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, dpi=(DPI, DPI))
    return path


def cover_art(path: Path, accent: str, seed: str | None = None,
              size: tuple[int, int] = (1800, 1800)) -> Path:
    """Marca da capa — dublê da ilustração do volume."""
    rng = _rng(seed or path.stem)
    w, h = size
    ink = _hex("#16181A")
    acc = _hex(accent)

    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    cx, cy = w / 2, h / 2
    rings = rng.randint(5, 8)

    for i in range(rings, 0, -1):
        r = (min(w, h) / 2) * (i / rings) * 0.92
        t = i / rings
        if i % 2 == 0:
            d.ellipse([cx - r, cy - r, cx + r, cy + r],
                      outline=_mix(acc, ink, 1 - t), width=max(4, int(w * 0.012)))
        else:
            start = rng.choice([0, 45, 90, 180, 270])
            d.arc([cx - r, cy - r, cx + r, cy + r], start, start + rng.choice([90, 180, 270]),
                  fill=acc if t > 0.55 else ink, width=max(6, int(w * 0.02)))

    bar = w * 0.16
    d.rectangle([cx - bar / 2, cy - bar / 2, cx + bar / 2, cy + bar / 2], fill=acc)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, dpi=(DPI, DPI))
    return path
