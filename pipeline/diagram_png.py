"""
diagram_png.py — os diagramas do livro, rasterizados para o EPUB.

Por que não SVG: leitores de e-book tratam SVG embutido de formas
diferentes, e o Kindle em particular calcula medidas físicas (mm) com um
DPI próprio — o desenho chega minúsculo na tela. PNG funciona em todo
leitor, de qualquer geração.

O traço é o MESMO do PDF: a geometria sai de diagrams.py e quem desenha é o
Typst, com as primitivas de style.typ. Um único documento, uma página por
diagrama, uma compilação só.
"""
from __future__ import annotations

from pathlib import Path

import typst

from .diagrams import build as build_diagram
from .model import Book, Diagram
from .theme import FONTS, Theme

PPI = 300          # 300 DPI na largura impressa: nítido em tela retina
PADDING_MM = 2.0


def render_all(book: Book, theme: Theme, out: Path) -> dict[int, bytes]:
    """Devolve {id(bloco): png} para todo diagrama do livro.

    A chave é a identidade do bloco no AST, então o renderizador de EPUB
    encontra o PNG do diagrama que está desenhando sem depender de ordem.
    """
    from .render_typst import TypstRenderer

    blocos: list[Diagram] = [
        b for _, b in book.walk() if isinstance(b, Diagram)
    ]
    if not blocos:
        return {}

    r = TypstRenderer(theme, book)
    paginas: list[str] = ['#import "style.typ": *\n']
    ordem: list[int] = []

    for b in blocos:
        try:
            layout = build_diagram(b.kind, b.spec, theme)
        except Exception:
            continue
        paginas.append(
            f"#page(width: {layout.width + PADDING_MM * 2:.2f}mm, "
            f"height: {layout.height + PADDING_MM * 2:.2f}mm, "
            f"margin: {PADDING_MM}mm, fill: white)[\n"
            f"#set text(font: sans, fill: ink)\n"
            f"{r.draw(layout)}]\n"
        )
        ordem.append(id(b))

    src_dir = out / "typst"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "style.typ").write_text(theme.render("style.typ.j2"),
                                       encoding="utf-8")
    src = src_dir / "_diagramas.typ"
    src.write_text("\n".join(paginas), encoding="utf-8")

    dados = typst.Compiler(input=src, root=src_dir, font_paths=[FONTS],
                           ignore_system_fonts=True).compile(
                               format="png", ppi=PPI)
    imagens = dados if isinstance(dados, list) else [dados]

    return {chave: png for chave, png in zip(ordem, imagens)}
