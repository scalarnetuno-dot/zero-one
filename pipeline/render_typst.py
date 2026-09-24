"""
render_typst.py — AST → documento Typst.

Este módulo não decide nada de visual: ele só escolhe QUAL componente do
design system chamar. Toda medida, cor e fonte vem de style.typ, que por sua
vez vem de tokens.yaml.
"""
from __future__ import annotations

import re
from pathlib import Path

from .collection_page import COLLECTION_DIR, other_cover_name
from .diagrams import DiagramLayout, build as build_diagram
from .loader import asset_path
from .parser import parse_inline
from .model import (
    Anatomy, Block, Book, Callout, Chapter, Code, CodeBlock, Compare, Diagram,
    Em, Example, Exercise, Figure, Heading, Http, Inline, Link, ListBlock,
    Paragraph, Part, Quote, Ref, Rule, Story, Strong, Summary, Table, Term,
    Text, Tree, Art, plain,
)
from .theme import Theme

_ESCAPE = str.maketrans({c: "\\" + c for c in "#$*_`<>@[]~\\"})


def esc(s: str) -> str:
    out = s.translate(_ESCAPE)
    # início de linha: - = + / . viram marcação no Typst
    return re.sub(r"(^|\n)([-=+/])", r"\1\\\2", out)


def tstr(s: str) -> str:
    """String literal Typst."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def label_of(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "-", raw.replace(":", "-")).strip("-")


class TypstRenderer:
    def __init__(self, theme: Theme, book: Book, pages_estimate: int = 0):
        self.theme = theme
        self.book = book
        self.pages = pages_estimate
        self.text_w = theme.text_width_mm(pages_estimate)
        self.numbered_chapter = True
        self.chapter_numbers = {
            **{slug: book.outline_ref(slug) for slug in book.outline},
            **{ch.slug: ch.number for ch in book.chapters},
        }
        self.answers: list[tuple[Chapter, Exercise]] = []
        self.art: list[Art] = []
        self.terms: list[Term] = []

    # ─── inline ──────────────────────────────────────────────────────────
    def inline(self, nodes: list[Inline]) -> str:
        out: list[str] = []
        for n in nodes:
            if isinstance(n, Text):
                out.append(esc(n.value))
            elif isinstance(n, Strong):
                out.append(f"#strong[{self.inline(n.children)}]")
            elif isinstance(n, Em):
                out.append(f"#emph[{self.inline(n.children)}]")
            elif isinstance(n, Code):
                out.append(f"#raw({tstr(n.value)})")
            elif isinstance(n, Link):
                out.append(f"#link({tstr(n.href)})[{self.inline(n.children)}]")
            elif isinstance(n, Ref):
                out.append(self.ref(n))
        return "".join(out)

    def ref(self, n: Ref) -> str:
        """`@cap:<slug>` vira o número do capítulo; o resto vira label Typst."""
        kind, _, target = n.target.partition(":")
        if kind == "cap":
            number = self.chapter_numbers.get(target)
            return esc(str(number)) if number else esc(target)
        return f"@{label_of(n.target)}"

    # ─── blocos ──────────────────────────────────────────────────────────
    def blocks(self, blocks: list[Block], indent: int = 0) -> str:
        return "\n".join(self.block(b) for b in blocks)

    def block(self, b: Block) -> str:
        if isinstance(b, Paragraph):
            text = self.inline(b.children)
            # parágrafo que abre um trecho não recua
            return (f"#par(first-line-indent: 0pt)[{text}]\n" if b.lead
                    else text + "\n")
        if isinstance(b, Heading):
            body = self.inline(b.children or [Text(b.title)])
            if self.numbered_chapter:
                return f"\n{'=' * b.level} {body}\n"
            return f"\n#heading(level: {b.level}, numbering: none)[{body}]\n"
        if isinstance(b, CodeBlock):
            return self.code(b)
        if isinstance(b, Callout):
            body = self.blocks(b.blocks)
            title = (f"title: [{self.inline(parse_inline(b.title))}], "
                     if b.title else "")
            # caixa curta não se parte: rótulo órfão no pé da página é defeito
            size = sum(len(plain(x.children)) for x in b.blocks
                       if isinstance(x, Paragraph))
            nobreak = size <= int(self.theme.t("blocks.callout_keep_together_chars", 600))
            return (f"#callout(kind: {tstr(b.kind)}, {title}"
                    f"nobreak: {str(nobreak).lower()})[\n{body}]\n")
        if isinstance(b, Example):
            title = f"title: [{self.inline(parse_inline(b.title))}], " if b.title else ""
            return f"#example({title})[\n{self.blocks(b.blocks)}]\n"
        if isinstance(b, Exercise):
            return (f"#exercise(number: {b.number}, level: {b.level})[\n"
                    f"{self.blocks(b.blocks)}]"
                    + (f" #label({tstr(label_of(b.id))})" if b.id else "") + "\n")
        if isinstance(b, Summary):
            return f"#summary[\n{self.blocks(b.blocks)}]\n"
        if isinstance(b, ListBlock):
            marker = "+" if b.ordered else "-"
            parts = []
            for item in b.items:
                content = self.blocks(item).strip()
                content = content.replace("\n", "\n  ")
                parts.append(f"{marker} {content}")
            return "\n".join(parts) + "\n"
        if isinstance(b, Figure):
            return self.figure(b)
        if isinstance(b, Diagram):
            return self.diagram(b)
        if isinstance(b, Table):
            return self.table(b)
        if isinstance(b, Quote):
            attr = f"attribution: {tstr(b.attribution)}, " if b.attribution else ""
            return f"#quote-block({attr})[{self.inline(b.children)}]\n"
        if isinstance(b, Term):
            self.terms.append(b)
            return f"#term({tstr(b.term)})[{self.inline(b.definition)}]\n"
        if isinstance(b, Story):
            title = f"title: {tstr(b.title)}, " if b.title else ""
            return f"#story({title})[\n{self.blocks(b.blocks)}]\n"
        if isinstance(b, Art):
            self.art.append(b)
            cap = (f"caption: [{self.inline(parse_inline(b.caption))}], "
                   if b.caption else "")
            src = f"src: {tstr(b.src)}, " if b.src else ""
            w = f"width: {self.largura_que_cabe(b.src):.0f}%, " if b.src else ""
            lbl = f" #label({tstr(label_of('fig:' + b.id))})" if b.id else ""
            return f"#art({cap}{src}{w}prompt: {tstr(b.prompt)}){lbl}\n"
        if isinstance(b, Anatomy):
            marks = ", ".join(str(n) for n, _ in b.notes)
            notes = ", ".join(f"[{self.inline(txt)}]" for _, txt in b.notes)
            title = f"title: {tstr(b.title)}, " if b.title else ""
            raw = f"raw(block: true, lang: {tstr(b.lang)}, {tstr(b.code)})"
            return (f"#anatomy({title}marks: ({marks}{',' if b.notes else ''}), "
                    f"notes: ({notes}{',' if b.notes else ''}), {raw})\n")
        if isinstance(b, Http):
            def arr(items: list[str]) -> str:
                return "(" + ", ".join(tstr(i) for i in items) + ("," if items else "") + ")"

            def body(txt: str, lang: str = "json") -> str:
                return (f"raw(block: true, lang: {tstr(lang)}, {tstr(txt)})"
                        if txt.strip() else "none")

            title = f"title: {tstr(b.title)}, " if b.title else ""
            return (f"#http-block(verb: {tstr(b.verb)}, path: {tstr(b.path)}, "
                    f"req-headers: {arr(b.req_headers)}, req-body: {body(b.req_body)}, "
                    f"status: {tstr(b.status)}, res-headers: {arr(b.res_headers)}, "
                    f"res-body: {body(b.res_body)}, {title})\n")
        if isinstance(b, Tree):
            rows = ", ".join(
                f"({tstr(prefix)}, {tstr(name)}, {tstr(note)})"
                for prefix, name, note in _tree_rows(b.lines))
            title = f"title: {tstr(b.title)}, " if b.title else ""
            return f"#tree-block({title}lines: ({rows},))\n"
        if isinstance(b, Compare):
            left = f"raw(block: true, lang: {tstr(b.lang)}, {tstr(b.left)})"
            right = f"raw(block: true, lang: {tstr(b.lang)}, {tstr(b.right)})"
            ll = b.left_label or self.theme.s("before")
            rl = b.right_label or self.theme.s("after")
            return (f"#compare-block(left-label: {tstr(ll)}, right-label: {tstr(rl)}, "
                    f"left: {left}, right: {right})\n")
        if isinstance(b, Rule):
            return "#v(4mm)\n#align(center)[#text(fill: ink-faint)[* * *]]\n#v(4mm)\n"
        return ""

    def code(self, b: CodeBlock) -> str:
        lines = b.code.split("\n")
        auto_number = len(lines) >= int(self.theme.t("code.numbered_from_lines", 6))
        numbered = auto_number if b.numbered is None else b.numbered
        nobreak = len(lines) <= int(self.theme.t("code.keep_together_lines", 26))
        title = f"title: {tstr(b.title)}, " if b.title else ""
        raw = f"raw(block: true, lang: {tstr(b.lang)}, {tstr(b.code)})"
        return (f"#codeblock(lang: {tstr(b.lang)}, {title}"
                f"numbered: {str(numbered).lower()}, nobreak: {str(nobreak).lower()}, "
                f"{raw})\n")

    def largura_que_cabe(self, src: str) -> float:
        """Percentual de largura que mantém a imagem dentro da mancha.

        Uma arte em pé ocuparia mais que a página inteira se fosse impressa
        com 100% da largura. Aqui a proporção real do arquivo decide.
        """
        limite = (self.theme.text_height_mm(self.pages)
                  * float(self.theme.t("figure.max_height", 0.62)))
        try:
            from PIL import Image

            caminho = asset_path(self.book, src)
            with Image.open(caminho) as im:
                proporcao = im.height / im.width
        except Exception:
            return 100.0
        altura_cheia = self.text_w * proporcao
        if altura_cheia <= limite:
            return 100.0
        return max(35.0, 100.0 * limite / altura_cheia)

    def figure(self, b: Figure) -> str:
        cap = (f"caption: [{self.inline(parse_inline(b.caption))}], "
               if b.caption else "")
        alt = f"alt: {tstr(b.alt)}, " if b.alt else ""
        lbl = f" #label({tstr(label_of('fig:' + b.id))})" if b.id else ""
        largura = min(b.width * 100, self.largura_que_cabe(b.src))
        return f"#fig({tstr(b.src)}, {cap}{alt}width: {largura:.0f}%){lbl}\n"

    def diagram(self, b: Diagram) -> str:
        # max_width entra ANTES de qualquer Typst existir: diagrams.py devolve
        # o layout já reduzido (geometria, fonte, tudo) quando não cabe na
        # coluna. Nada aqui precisa mais escalar — width/height/font_size do
        # layout já são os valores finais, e #diagram() em style.typ.j2
        # sempre pressupôs exatamente isso. O antigo #scale(..., reflow: true)
        # só encolhia o container; cada #place(dx:, dy:) dentro do desenho
        # continuava com coordenadas do tamanho cheio e vazava para a
        # direita — era esse o defeito visto no PDF.
        layout = build_diagram(b.kind, b.spec, self.theme, max_width=self.text_w - 1)
        body = self.draw(layout)
        cap = (f"caption: [{self.inline(parse_inline(b.caption))}], "
               if b.caption else "")
        lbl = f" #label({tstr(label_of('fig:' + b.id))})" if b.id else ""
        return (f"#diagram(width: {layout.width:.2f}mm, "
                f"height: {layout.height:.2f}mm, {cap})[\n{body}]{lbl}\n")

    def draw(self, d: DiagramLayout) -> str:
        out: list[str] = []
        for s in d.shapes:
            fill = f'rgb("{s.fill}")' if s.fill else "none"
            stroke = f'rgb("{s.stroke}")' if s.stroke else "rule-strong"
            label = esc(s.text).replace("\n", " \\\n")
            if s.kind == "rect" or s.kind == "cell":
                sub = f", sub: {tstr(s.sub)}" if s.sub else ""
                out.append(
                    f"#dg-rect({s.x:.2f}mm, {s.y:.2f}mm, {s.w:.2f}mm, {s.h:.2f}mm, "
                    f"label: [{label}]{sub}, fill: {fill}, stroke: {stroke}, "
                    f"size: {d.font_size}pt, bold: {str(s.bold).lower()})")
            elif s.kind == "stadium":
                out.append(
                    f"#dg-rect({s.x:.2f}mm, {s.y:.2f}mm, {s.w:.2f}mm, {s.h:.2f}mm, "
                    f"label: [{label}], fill: {fill}, stroke: {stroke}, "
                    f"radius: {s.h / 2:.2f}mm, size: {d.font_size}pt, "
                    f"bold: {str(s.bold).lower()})")
            elif s.kind == "diamond":
                pts = "((0.5, 0.0), (1.0, 0.5), (0.5, 1.0), (0.0, 0.5))"
                out.append(
                    f"#dg-poly({s.x:.2f}mm, {s.y:.2f}mm, {s.w:.2f}mm, {s.h:.2f}mm, "
                    f"{pts}, label: [{label}], fill: {fill}, stroke: {stroke}, "
                    f"size: {d.font_size}pt)")
            elif s.kind == "parallelogram":
                pts = "((0.14, 0.0), (1.0, 0.0), (0.86, 1.0), (0.0, 1.0))"
                out.append(
                    f"#dg-poly({s.x:.2f}mm, {s.y:.2f}mm, {s.w:.2f}mm, {s.h:.2f}mm, "
                    f"{pts}, label: [{label}], fill: {fill}, stroke: {stroke}, "
                    f"size: {d.font_size}pt)")
            elif s.kind == "line":
                out.append(
                    f"#dg-path((({s.x:.2f}mm, {s.y:.2f}mm), "
                    f"({s.x + s.w:.2f}mm, {s.y + s.h:.2f}mm)), arrow: false, "
                    f"dashed: {str(s.dashed).lower()}, stroke-color: {stroke})")
            elif s.kind == "text":
                fill_c = f'rgb("{s.fill}")' if s.fill else "ink"
                out.append(
                    f"#dg-text({s.x:.2f}mm, {s.y:.2f}mm, {s.w:.2f}mm, {s.h:.2f}mm, "
                    f"[{label}], align-to: {s.align}, size: {d.font_size}pt, "
                    f"fill: {fill_c}, bold: {str(s.bold).lower()})")
        for e in d.edges:
            pts = ", ".join(f"({x:.2f}mm, {y:.2f}mm)" for x, y in e.points)
            out.append(f"#dg-path(({pts}), arrow: {str(e.arrow).lower()}, "
                       f"dashed: {str(e.dashed).lower()})")
            if e.label and e.label_at:
                x, y = e.label_at
                out.append(f"#dg-label({x:.2f}mm, {y - 2:.2f}mm, [{esc(e.label)}], "
                           f"size: {d.label_size}pt)")
        return "\n".join(out) + "\n"

    def table(self, b: Table) -> str:
        # a coluna de conteúdo mais largo estica; as outras se ajustam
        widths = [max((len(plain(r[i])) for r in b.rows), default=0)
                  for i in range(len(b.header))]
        elastic = widths.index(max(widths)) if widths else 0
        cols = ", ".join("1fr" if i == elastic else "auto"
                         for i in range(len(b.header)))
        cols += "," if len(b.header) == 1 else ""
        aligns = ", ".join(b.align[i] if i < len(b.align) else "left"
                           for i in range(len(b.header)))
        header = ", ".join(f"[{self.inline(c)}]" for c in b.header)
        rows = []
        for r in b.rows:
            rows.append("(" + ", ".join(f"[{self.inline(c)}]" for c in r) + ",)")
        cap = (f"caption: [{self.inline(parse_inline(b.caption))}], "
               if b.caption else "")
        lbl = f" #label({tstr(label_of('tbl:' + b.id))})" if b.id else ""
        return (f"#tbl(columns: ({cols}), header: ({header},), "
                f"rows: ({', '.join(rows)},), {cap})" + lbl + "\n")

    # ─── documento ───────────────────────────────────────────────────────
    def chapter(self, ch: Chapter) -> str:
        # seção de capítulo não numerado não recebe "0.1"
        self.numbered_chapter = ch.numbered
        head = [f"\n// ── {ch.slug} " + "─" * 40]
        args = []
        if ch.numbered:
            args.append(f"number: {ch.number}")
        else:
            args.append("numbered: false")
        if ch.kicker:
            args.append(f"kicker: [{esc(ch.kicker)}]")
        if ch.epigraph:
            args.append(f"epigraph: [{esc(ch.epigraph)}]")
        if ch.epigraph_by:
            args.append(f"epigraph-by: {tstr(ch.epigraph_by)}")
        if ch.goal:
            args.append(f"goal: [{self.inline(parse_inline(ch.goal))}]")
        head.append(f"#chapter({', '.join(args)})[{esc(ch.title)}]")
        if ch.locked:
            head.append(self.locked(ch))
            return "\n".join(head)
        head.append(self.blocks(ch.blocks))
        for b in ch.walk():
            if isinstance(b, Exercise) and b.answer:
                self.answers.append((ch, b))
        return "\n".join(head)

    def locked(self, ch: Chapter) -> str:
        """Prévia: as seções seguem no sumário, o texto dá lugar ao aviso."""
        sections = ", ".join(
            f"({b.level}, [{self.inline(b.children or [Text(b.title)])}])"
            for b in ch.blocks if isinstance(b, Heading))
        sections += "," if sections else ""
        return (f"#locked-chapter(message: {tstr(self.theme.s('locked'))}, "
                f"sections: ({sections}))\n")

    def collection_page(self) -> str:
        """Última página: os demais volumes da coleção, com capa."""
        if not self.book.others:
            return ""
        books = ", ".join(
            f"(cover: {tstr(COLLECTION_DIR + '/' + other_cover_name(b))}, "
            f"title: {tstr(b.title)}, subtitle: {tstr(b.subtitle)})"
            for b in self.book.others)
        url = str(self.theme.collection.get("collection", {}).get("publisher_url", "") or "")
        visit = (f", url: {tstr(url)}, link-text: {tstr(self.theme.s('visit_publisher'))}"
                 if url else "")
        return (f"\n#collection-page(title: {tstr(self.theme.s('others'))}, "
                f"books: ({books},){visit})\n")

    def part_page(self, part: Part) -> str:
        chapters = ", ".join(
            f"({tstr(str(n))}, {tstr(t)})" for n, t in
            [(c.number, c.title) for c in self.book.chapters if c.part == part.id])
        blurb = f"blurb: [{esc(part.blurb)}], " if part.blurb else ""
        return (f"\n#part-page(number: {part.number}, {blurb}"
                f"chapters: ({chapters},))[{esc(part.title)}]\n")

    def document(self) -> str:
        m = self.book.meta
        th = self.theme
        coll = th.collection.get("collection", {})
        parts: list[str] = []
        parts.append('#import "style.typ": *\n')
        parts.append(
            "#show: book.with(\n"
            f"  title: {tstr(m.title)},\n"
            f"  author: {tstr(m.author)},\n"
            f"  keywords: ({', '.join(tstr(k) for k in m.keywords)}{',' if m.keywords else ''}),\n"
            f"  lang: {tstr(m.language.split('-')[0])},\n"
            f"  region: {tstr(m.language.split('-')[-1]) if '-' in m.language else 'none'},\n"
            f"  gutter-extra: {th.gutter_extra(self.pages)},\n"
            ")\n"
        )
        parts.append(
            f"#title-page(title: {tstr(m.title)}, subtitle: {tstr(m.subtitle)}, "
            f"author: {tstr(m.author)}, "
            f"volume: {tstr(str(m.volume)) if m.volume else 'none'}, "
            f"collection: {tstr(coll.get('name', ''))}, "
            f"publisher: {tstr(m.publisher or coll.get('publisher', ''))})\n"
        )
        parts.append(
            f"#copyright-page(title: {tstr(m.title)}, author: {tstr(m.author)}, "
            f"publisher: {tstr(m.publisher or coll.get('publisher', ''))}, "
            f"year: {tstr(str(m.year))}, isbn: {tstr(m.isbn)}, "
            f"edition: {tstr(m.edition)})\n"
        )
        parts.append("#toc-page()\n")
        parts.append("#counter(page).update(1)\n")

        seen_parts: set[str] = set()
        by_id = {p.id: p for p in self.book.parts}
        for ch in self.book.chapters:
            if ch.part and ch.part not in seen_parts and ch.part in by_id:
                seen_parts.add(ch.part)
                parts.append(self.part_page(by_id[ch.part]))
            parts.append(self.chapter(ch))

        parts.append(self.back_matter())
        parts.append(self.collection_page())
        # marcador lido pelo build para saber o número final de páginas
        parts.append(
            "\n#context [#metadata(counter(page).final().first()) <pagecount>]\n")
        return "\n".join(parts)

    def back_matter(self) -> str:
        out: list[str] = []
        if self.answers:
            out.append(f"\n#chapter(numbered: false)[{esc(self.theme.s('answers'))}]")
            last_ch = None
            for ch, ex in self.answers:
                if ch is not last_ch:
                    out.append(f"\n=== {esc(ch.title)}\n")
                    last_ch = ch
                out.append(f"#exercise(number: {ex.number}, level: {ex.level})[\n"
                           f"{self.blocks(ex.answer)}]\n")
        if self.terms:
            out.append(f"\n#chapter(numbered: false)[{esc(self.theme.s('glossary'))}]")
            for t in sorted(self.terms, key=lambda x: x.term.lower()):
                out.append(f"#term({tstr(t.term)})[{self.inline(t.definition)}]")
        return "\n".join(out)


def render(book: Book, theme: Theme, pages_estimate: int = 0) -> str:
    return TypstRenderer(theme, book, pages_estimate).document()


def _tree_rows(lines: list[tuple[int, str, str]]) -> list[tuple[str, str, str]]:
    """Transforma níveis de indentação nos fios ├── │ └── da árvore."""
    out: list[tuple[str, str, str]] = []
    for i, (level, name, note) in enumerate(lines):
        last = True
        for level2, _, _ in lines[i + 1:]:
            if level2 == level:
                last = False
                break
            if level2 < level:
                break
        prefix = ""
        for depth in range(level):
            # a linha vertical continua se ainda houver irmão naquele nível
            has_more = False
            for level2, _, _ in lines[i + 1:]:
                if level2 == depth:
                    has_more = True
                    break
                if level2 < depth:
                    break
            prefix += "│  " if has_more else "   "
        if level:
            prefix += "└─ " if last else "├─ "
        out.append((prefix, name, note))
    return out
