"""
cover_i18n.py — a arte da capa no idioma da tradução.

A ilustração das capas tem frases em português desenhadas nela (subtítulo,
bordão). Em vez de cair na capa só tipográfica, a tradução reaproveita a
arte: apaga a tinta dessas áreas, reconstitui o papel e escreve o texto
traduzido na mesma inclinação.

    python -m pipeline cover-i18n php-one-v1-en

As áreas ficam no book.yaml do original (são da arte, não do idioma):

    cover_text_areas:
      subtitle:
        polygon: [[768, 190], [995, 140], [1005, 245], [790, 300]]
        center: [882, 222]              # quadro do texto novo, antes
        size: [236, 118]                # da rotação
        angle: 11.5                     # graus, anti-horário
        align: center
        grow: 9                         # opcional: quanto engordar a
                                        # máscara (ímpar, em px)

e as frases no book.yaml da tradução:

    cover_text:
      subtitle: ["PHP", "Fundamentals"]

Saem i18n/<idioma>/assets/capa.png e capa.jpg (a prévia usa o JPEG).
"""
from __future__ import annotations

import colorsys
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .loader import BOOKS, I18N, cover_art_path, split_translation

FONT_DIR = Path(__file__).resolve().parent.parent / "collection" / "theme" / "fonts"
FONT = "Kalam-Bold.ttf"
INK = (24, 21, 19)


def _ink_mask(img: Image.Image, polygon: list[list[int]], grow: int = 9) -> Image.Image:
    """Tinta escura e sem cor dentro do polígono (o roxo da arte fica)."""
    area = Image.new("L", img.size, 0)
    ImageDraw.Draw(area).polygon([tuple(p) for p in polygon], fill=255)
    x0, y0, x1, y1 = area.getbbox()
    mask = Image.new("L", img.size, 0)
    px, mp, ap = img.load(), mask.load(), area.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            if not ap[x, y]:
                continue
            r, g, b = (c / 255 for c in px[x, y][:3])
            _, lum, sat = colorsys.rgb_to_hls(r, g, b)
            if lum < 0.62 and (sat < 0.35 or lum < 0.2):
                mp[x, y] = 255
    # engorda a máscara para levar junto o serrilhado da letra
    return mask.filter(ImageFilter.MaxFilter(grow))


def _fill(img: Image.Image, mask: Image.Image, rounds: int = 3) -> Image.Image:
    """Preenche a máscara com o papel ao redor (convolução normalizada)."""
    x0, y0, x1, y1 = mask.getbbox()
    pad = 40
    box = (max(0, x0 - pad), max(0, y0 - pad),
           min(img.width, x1 + pad), min(img.height, y1 + pad))
    tile = img.crop(box).convert("RGB")
    hole = mask.crop(box)
    keep = hole.point(lambda v: 0 if v else 255)
    for radius in (14, 7, 3)[:rounds]:
        known = Image.composite(tile, Image.new("RGB", tile.size), keep)
        a = known.filter(ImageFilter.GaussianBlur(radius)).load()
        w = keep.filter(ImageFilter.GaussianBlur(radius)).load()
        tp, hp = tile.load(), hole.load()
        for y in range(tile.height):
            for x in range(tile.width):
                if hp[x, y] and w[x, y] > 2:
                    k = 255 / w[x, y]
                    r, g, b = a[x, y]
                    tp[x, y] = (min(255, int(r * k)), min(255, int(g * k)),
                                min(255, int(b * k)))
    # um grão leve, para o remendo não ficar liso demais
    grain = tile.filter(ImageFilter.GaussianBlur(1))
    tile = Image.composite(grain, tile, hole)
    out = img.convert("RGB").copy()
    out.paste(tile, box[:2])
    return out


def _write(img: Image.Image, lines: list[str], area: dict, font_path: Path) -> None:
    """Escreve as linhas no quadro da área, inclinadas como a arte.

    `center` e `size` descrevem o quadro antes da rotação: a maior fonte
    em que as linhas cabem nele é a escolhida.
    """
    fw, fh = area["size"]
    angle = float(area.get("angle", 0))
    align = str(area.get("align", "center"))
    size = 90
    while size > 12:
        font = ImageFont.truetype(str(font_path), size)
        lead = int(size * float(area.get("leading", 0.92)))
        widths = [font.getlength(t) for t in lines]
        top = font.getbbox(lines[0])[1]
        h = lead * (len(lines) - 1) + font.getbbox("Ág")[3] - top
        if max(widths) <= fw and h <= fh:
            break
        size -= 2
    layer = Image.new("RGBA", (fw + 40, fh + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 20 + (fh - h) // 2 - top
    for t, w in zip(lines, widths):
        x = 20 + {"left": 0, "right": fw - w}.get(align, (fw - w) / 2)
        d.text((x, y), t, font=font, fill=INK + (255,))
        y += lead
    rot = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    cx, cy = area["center"]
    img.paste(rot, (int(cx - rot.width / 2), int(cy - rot.height / 2)), rot)


def translate_cover(slug: str) -> list[Path]:
    base, lang = split_translation(slug)
    if not lang:
        raise SystemExit(f"{slug}: não é uma tradução (ex.: {slug}-en)")
    src_cfg = yaml.safe_load((BOOKS / base / "book.yaml").read_text(encoding="utf-8")) or {}
    tr_cfg = yaml.safe_load((BOOKS / base / I18N / lang / "book.yaml")
                            .read_text(encoding="utf-8")) or {}
    areas = src_cfg.get("cover_text_areas") or {}
    texts = tr_cfg.get("cover_text") or {}
    art = cover_art_path(base)
    if art is None or not areas or not texts:
        raise SystemExit(f"{slug}: falta arte, cover_text_areas (original) "
                         "ou cover_text (tradução)")
    font = FONT_DIR / FONT
    if not font.exists():
        raise SystemExit(f"fonte ausente: {font} — rode collection/theme/fonts/_fetch.py")
    # sempre do PNG, que não perdeu nada na compressão
    png = art.with_suffix(".png")
    img = Image.open(png if png.exists() else art).convert("RGB")
    for key, area in areas.items():
        lines = texts.get(key)
        if not lines:
            continue
        mask = _ink_mask(img, area["polygon"], int(area.get("grow", 9)) | 1)
        if mask.getbbox():
            img = _fill(img, mask)
        _write(img, [str(t) for t in lines], area, font)
    dest = BOOKS / base / I18N / lang / "assets"
    dest.mkdir(parents=True, exist_ok=True)
    out = [dest / "capa.png", dest / "capa.jpg"]
    img.save(out[0], optimize=True)
    img.save(out[1], quality=88, optimize=True, progressive=True)
    return out


def main(slug: str) -> int:
    for path in translate_cover(slug):
        print(f"  capa  {path.relative_to(BOOKS.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
