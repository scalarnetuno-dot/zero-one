"""
validate.py — o revisor automático.

Roda antes de imprimir: o objetivo é que nenhum defeito de diagramação
chegue à Amazon. Erros param o build em modo --strict; avisos aparecem
no terminal e ficam no relatório.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .diagrams import DiagramError, build as build_diagram
from .model import (
    Anatomy, Art, Block, Book, Callout, Chapter, CodeBlock, Compare, Diagram,
    Exercise, Figure, Heading, Http, ListBlock, Paragraph, Ref, Story, Summary,
    Table, Text, Tree, plain,
)
from .loader import asset_path
from .theme import Theme, _mm

Level = Literal["error", "warn", "info"]


@dataclass
class Issue:
    level: Level
    where: str
    message: str


def validate_ast(book: Book, theme: Theme) -> list[Issue]:
    out: list[Issue] = []
    max_cols = int(theme.t("code.max_line_chars", 62))
    min_dpi = int(theme.t("figure.min_dpi", 300))
    seen_slugs: dict[str, str] = {}
    labels: set[str] = set()
    refs: list[tuple[str, str]] = []

    # Todo capítulo é alvo de `@cap:<slug>`. Assim "no capítulo 26" deixa de
    # ser um número digitado à mão — e um capítulo que mude de lugar vira
    # erro de build, não uma frase errada impressa.
    for ch in book.chapters:
        labels.add(f"cap:{ch.slug}")
    # Numa prévia, o capítulo que ficou de fora continua sendo alvo válido.
    for slug in book.outline:
        labels.add(f"cap:{slug}")

    for ch in book.chapters:
        where = f"{ch.source.name if ch.source else ch.slug}"
        if not ch.title.strip():
            out.append(Issue("error", where, "capítulo sem título"))
        if ch.slug in seen_slugs:
            out.append(Issue("error", where, f"slug repetido de '{seen_slugs[ch.slug]}'"))
        seen_slugs[ch.slug] = where
        # capítulo fechado da prévia: só títulos, de propósito
        if ch.locked:
            continue

        blocks = list(ch.blocks)
        words = sum(len(plain(b.children).split()) for b in ch.walk()
                    if isinstance(b, Paragraph))
        if ch.matter == "body":
            if words < 150:
                out.append(Issue("warn", where, f"capítulo curto ({words} palavras)"))
            if not any(isinstance(b, Summary) for b in ch.walk()):
                out.append(Issue("warn", where, "capítulo sem :::summary"))
        if not blocks:
            out.append(Issue("error", where, "capítulo vazio"))

        # títulos órfãos e saltos de nível
        prev_level = 1
        for i, b in enumerate(blocks):
            if isinstance(b, Heading):
                if b.level > prev_level + 1:
                    out.append(Issue("warn", where,
                                     f"salto de nível de título em “{b.title}”"))
                prev_level = b.level
                nxt = blocks[i + 1] if i + 1 < len(blocks) else None
                if nxt is None or isinstance(nxt, Heading):
                    out.append(Issue("warn", where, f"título órfão: “{b.title}”"))

        for b in ch.walk():
            out += _check_block(b, ch, book, where, theme, max_cols, min_dpi,
                                labels, refs)

    for name in book.missing:
        out.append(Issue("info", "book.yaml", f"capítulo ainda não escrito: {name}"))
    # Pendências de tradução: uma linha por tipo, não uma por capítulo.
    if book.untranslated:
        n = len(book.untranslated)
        out.append(Issue("warn", "i18n", f"{n} capítulo{'s' * (n > 1)} sem tradução "
                         f"({_chapter_ranges(book.untranslated)}): sai o original "
                         "em português"))
    if book.outdated:
        n = len(book.outdated)
        out.append(Issue("warn", "i18n", f"{n} tradu{'ções' if n > 1 else 'ção'} "
                         f"atrás do original ({_chapter_ranges(book.outdated)}): "
                         "revise e rode `python -m pipeline i18n "
                         f"{book.meta.slug} --stamp <NN>`"))

    for target, where in refs:
        if target.split(":", 1)[-1] and target not in labels:
            out.append(Issue("error", where, f"referência sem alvo: @{target}"))

    return out


def _chapter_ranges(names: list[str]) -> str:
    """['15-a', '16-b', '17-c', '20-d'] → '15–17, 20'."""
    nums: list[int] = []
    for name in names:
        head = name.split("-", 1)[0]
        if not head.isdigit():
            return ", ".join(names)
        nums.append(int(head))
    width = max(len(n.split("-", 1)[0]) for n in names)
    parts, start = [], None
    for i, n in enumerate(sorted(nums)):
        if start is None:
            start = n
        nxt = sorted(nums)[i + 1] if i + 1 < len(nums) else None
        if nxt != n + 1:
            a, b = f"{start:0{width}d}", f"{n:0{width}d}"
            parts.append(a if start == n else f"{a}–{b}")
            start = None
    return ", ".join(parts)


def _check_block(b: Block, ch: Chapter, book: Book, where: str, theme: Theme,
                 max_cols: int, min_dpi: int, labels: set[str],
                 refs: list[tuple[str, str]]) -> list[Issue]:
    out: list[Issue] = []

    if isinstance(b, Paragraph):
        for n in b.children:
            if isinstance(n, Ref):
                refs.append((n.target, where))
        text = plain(b.children)
        if not text.strip():
            out.append(Issue("warn", where, "parágrafo vazio"))

    elif isinstance(b, CodeBlock):
        longest = max((len(l) for l in b.code.split("\n")), default=0)
        if longest > max_cols:
            out.append(Issue("warn", where,
                             f"código com linha de {longest} colunas "
                             f"(máximo {max_cols}) em “{b.title or b.lang}”"))
        if not b.code.strip():
            out.append(Issue("error", where, "bloco de código vazio"))
        if b.lang in ("", "plain") and len(b.code.split("\n")) > 3:
            out.append(Issue("info", where, "bloco de código sem linguagem declarada"))
        if b.id:
            labels.add(f"lst:{b.id}")

    elif isinstance(b, Figure):
        path = asset_path(book, b.src) if ch.source else Path(b.src)
        if not path.exists():
            out.append(Issue("error", where, f"imagem ausente: {b.src}"))
        else:
            out += _check_image(path, b, where, theme, min_dpi)
        if not b.caption:
            out.append(Issue("info", where, f"figura sem legenda: {b.src}"))
        if b.id:
            labels.add(f"fig:{b.id}")

    elif isinstance(b, Diagram):
        try:
            layout = build_diagram(b.kind, b.spec, theme)
            if layout.height > theme.text_height_mm() * float(theme.t("figure.max_height", 0.62)):
                out.append(Issue("warn", where,
                                 f"diagrama alto demais ({layout.height:.0f} mm): "
                                 "vai sobrar página"))
        except DiagramError as exc:
            out.append(Issue("error", where, f"diagrama inválido: {exc}"))
        if b.id:
            labels.add(f"fig:{b.id}")

    elif isinstance(b, Table):
        ncols = len(b.header)
        if ncols == 0:
            out.append(Issue("error", where, "tabela sem cabeçalho"))
        for r in b.rows:
            if len(r) != ncols:
                out.append(Issue("error", where,
                                 f"tabela com linha de {len(r)} células "
                                 f"(cabeçalho tem {ncols})"))
                break
        if ncols > 5:
            out.append(Issue("warn", where,
                             f"tabela com {ncols} colunas: não cabe em 6×9 pol"))
        if b.id:
            labels.add(f"tbl:{b.id}")

    elif isinstance(b, Exercise):
        if not b.answer:
            out.append(Issue("info", where, f"exercício {b.number} sem :::answer"))
        if b.id:
            labels.add(b.id)

    elif isinstance(b, ListBlock):
        if len(b.items) == 1:
            out.append(Issue("info", where, "lista com um item só"))

    elif isinstance(b, Callout):
        if not b.blocks:
            out.append(Issue("warn", where, f"caixa :::{b.kind} vazia"))

    elif isinstance(b, Anatomy):
        total = len(b.code.split("\n"))
        for line, _ in b.notes:
            if line < 1 or line > total:
                out.append(Issue("error", where,
                                 f"anatomia aponta para a linha {line}, "
                                 f"mas o código tem {total}"))
        if not b.notes:
            out.append(Issue("warn", where, "anatomia sem nenhuma nota"))
        if len(b.notes) > 8:
            out.append(Issue("warn", where,
                             f"anatomia com {len(b.notes)} notas: "
                             "quebre em duas"))
        longest = max((len(l) for l in b.code.split("\n")), default=0)
        if longest > max_cols - 6:
            out.append(Issue("warn", where,
                             f"anatomia com linha de {longest} colunas "
                             f"(o crachá precisa de folga: máximo {max_cols - 6})"))

    elif isinstance(b, Http):
        if not b.status:
            out.append(Issue("warn", where,
                             f"{b.verb} {b.path}: bloco http sem resposta"))
        if not b.path.startswith("/"):
            out.append(Issue("warn", where,
                             f"caminho '{b.path}' deveria começar com /"))

    elif isinstance(b, Story):
        if not b.blocks:
            out.append(Issue("warn", where, "cena vazia"))
        palavras = sum(len(plain(x.children).split()) for x in b.blocks
                       if isinstance(x, Paragraph))
        if palavras > 260:
            out.append(Issue("warn", where,
                             f"cena com {palavras} palavras: a camada narrativa "
                             "não pode competir com o conteúdo (máximo ~260)"))

    elif isinstance(b, Art):
        if b.src:
            path = (asset_path(book, b.src)
                if ch.source else Path(b.src))
            if not path.exists():
                out.append(Issue("error", where, f"arte ausente: {b.src}"))
            else:
                out += _check_image(
                    path, Figure(src=b.src, caption=b.caption), where,
                    theme, min_dpi)
        elif len(b.prompt) < 40:
            out.append(Issue("warn", where,
                             "marcador de arte com descrição curta demais "
                             "para alimentar um gerador"))
        if not b.caption:
            out.append(Issue("info", where, "ilustração sem legenda"))
        if b.id:
            labels.add(f"fig:{b.id}")

    elif isinstance(b, Tree):
        if not b.lines:
            out.append(Issue("warn", where, "árvore de arquivos vazia"))

    elif isinstance(b, Compare):
        limit = int(theme.t("compare.max_line_chars", 40))
        for side, code in (("esquerda", b.left), ("direita", b.right)):
            longest = max((len(l) for l in code.split("\n")), default=0)
            if longest > limit:
                out.append(Issue("warn", where,
                                 f"comparação: lado da {side} com {longest} "
                                 f"colunas (máximo {limit} em duas colunas)"))

    return out


def _check_image(path: Path, fig: Figure, where: str, theme: Theme,
                 min_dpi: int) -> list[Issue]:
    try:
        from PIL import Image
    except ImportError:
        return []
    out: list[Issue] = []
    try:
        with Image.open(path) as im:
            px_w = im.width
    except Exception as exc:
        return [Issue("error", where, f"imagem ilegível ({path.name}): {exc}")]
    printed_mm = theme.text_width_mm() * fig.width
    dpi = px_w / (printed_mm / 25.4) if printed_mm else 0
    if dpi < min_dpi:
        out.append(Issue("warn", where,
                         f"{path.name}: {dpi:.0f} DPI impressos "
                         f"(mínimo {min_dpi} para a KDP)"))
    return out


# ─── PDF pronto ──────────────────────────────────────────────────────────────

def validate_pdf(pdf: Path | None, theme: Theme, pages: int) -> list[Issue]:
    out: list[Issue] = []
    if pdf is None or not pdf.exists():
        return [Issue("error", "pdf", "PDF não foi gerado")]
    where = pdf.name

    if pages and pages % 2:
        out.append(Issue("warn", where,
                         f"{pages} páginas (ímpar): a gráfica vai acrescentar "
                         "uma folha em branco"))
    if pages and pages < 24:
        out.append(Issue("warn", where, f"{pages} páginas: a KDP exige 24 no mínimo"))

    try:
        from pypdf import PdfReader
    except ImportError:
        out.append(Issue("info", where,
                         "pypdf não instalado: sem checagem de página em branco"))
        return out

    reader = PdfReader(str(pdf))
    trim_w = _mm(theme.t("page.trim.width"))
    trim_h = _mm(theme.t("page.trim.height"))
    blanks: list[int] = []
    for i, page in enumerate(reader.pages, start=1):
        w = float(page.mediabox.width) * 25.4 / 72
        h = float(page.mediabox.height) * 25.4 / 72
        if abs(w - trim_w) > 0.6 or abs(h - trim_h) > 0.6:
            out.append(Issue("error", where,
                             f"página {i} tem {w:.1f}×{h:.1f} mm, "
                             f"esperado {trim_w:.1f}×{trim_h:.1f} mm"))
            break
        if i < len(reader.pages) and not (page.extract_text() or "").strip():
            blanks.append(i)
    if blanks:
        # páginas em branco antes de abertura de capítulo são intencionais
        out.append(Issue("info", where,
                         f"páginas sem texto: {', '.join(map(str, blanks[:12]))}"
                         + (" …" if len(blanks) > 12 else "")))
    return out
