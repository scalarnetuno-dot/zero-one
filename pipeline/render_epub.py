"""
render_epub.py — AST → EPUB 3.

Mesmo conteúdo, mesmo design system, outro meio: no EPUB não existe página,
então recuo vira espaço, diagrama vira SVG e o realce de sintaxe sai do
Pygments com a MESMA paleta do PDF.
"""
from __future__ import annotations

import html
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .diagrams import DiagramLayout, build as build_diagram
from .model import (
    Block, Book, Callout, Chapter, Code, CodeBlock, Diagram, Em, Example,
    Exercise, Figure, Heading, Inline, Link, ListBlock, Paragraph, Quote, Ref,
    Rule, Strong, Summary, Table, Term, Text, plain,
)
from .theme import Theme

PT = 0.3528  # pt → mm


def e(s: str) -> str:
    return html.escape(s, quote=False)


# ─── realce de sintaxe ───────────────────────────────────────────────────────

_TOKEN_CLASS = [
    ("Token.Comment", "comment"),
    ("Token.Literal.String", "string"),
    ("Token.Literal.Number", "number"),
    ("Token.Keyword", "keyword"),
    ("Token.Operator", "operator"),
    ("Token.Punctuation", "operator"),
    ("Token.Name.Function", "function"),
    ("Token.Name.Class", "type"),
    ("Token.Name.Namespace", "type"),
    ("Token.Name.Decorator", "meta"),
    ("Token.Name.Builtin", "builtin"),
    ("Token.Name.Attribute", "meta"),
]


def highlight(code: str, lang: str) -> str:
    try:
        from pygments import lex
        from pygments.lexers import get_lexer_by_name
    except ImportError:
        return e(code)
    try:
        lexer = get_lexer_by_name(lang or "text")
    except Exception:
        return e(code)
    out: list[str] = []
    for token, value in lex(code, lexer):
        cls = ""
        name = str(token)
        for prefix, css in _TOKEN_CLASS:
            if name.startswith(prefix):
                cls = css
                break
        out.append(f'<span class="tok-{cls}">{e(value)}</span>' if cls else e(value))
    return "".join(out).rstrip("\n")


# ─── SVG dos diagramas ───────────────────────────────────────────────────────

def svg(d: DiagramLayout, theme: Theme) -> str:
    w, h = d.width + 2, d.height + 2
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'style="width:100%;max-width:{w:.0f}mm;height:auto" '
        f'font-family="{theme.t("type.sans")}, sans-serif">'
    ]
    fs = d.font_size * PT
    ls = d.label_size * PT
    ink = theme.t("color.ink")
    soft = theme.t("color.ink_soft")

    def text_lines(x: float, y: float, h_box: float, lines: list[str], size: float,
                   fill: str = "", weight: str = "") -> str:
        n = len(lines)
        start = y + h_box / 2 - (n - 1) * size * 0.6
        bits = []
        for i, ln in enumerate(lines):
            bits.append(
                f'<text x="{x:.1f}" y="{start + i * size * 1.2:.1f}" font-size="{size:.2f}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'fill="{fill or ink}"'
                + (f' font-weight="{weight}"' if weight else "")
                + f">{e(ln)}</text>")
        return "".join(bits)

    for s in d.shapes:
        fill = s.fill or "#fff"
        stroke = s.stroke or theme.t("color.rule_strong")
        sw = 0.22
        if s.kind in ("rect", "cell", "stadium"):
            rx = s.h / 2 if s.kind == "stadium" else 0
            parts.append(
                f'<rect x="{s.x:.1f}" y="{s.y:.1f}" width="{s.w:.1f}" height="{s.h:.1f}" '
                f'rx="{rx:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        elif s.kind == "diamond":
            pts = [(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)]
            poly = " ".join(f"{s.x + px * s.w:.1f},{s.y + py * s.h:.1f}" for px, py in pts)
            parts.append(f'<polygon points="{poly}" fill="{fill}" stroke="{stroke}" '
                         f'stroke-width="{sw}"/>')
        elif s.kind == "parallelogram":
            pts = [(0.14, 0), (1, 0), (0.86, 1), (0, 1)]
            poly = " ".join(f"{s.x + px * s.w:.1f},{s.y + py * s.h:.1f}" for px, py in pts)
            parts.append(f'<polygon points="{poly}" fill="{fill}" stroke="{stroke}" '
                         f'stroke-width="{sw}"/>')
        elif s.kind == "line":
            dash = ' stroke-dasharray="1.2,1.2"' if s.dashed else ""
            parts.append(
                f'<line x1="{s.x:.1f}" y1="{s.y:.1f}" x2="{s.x + s.w:.1f}" '
                f'y2="{s.y + s.h:.1f}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')
        if s.text and s.kind != "line":
            lines = s.text.split("\n")
            parts.append(text_lines(s.x + s.w / 2, s.y, s.h, lines, fs,
                                    weight="600" if s.bold else ""))
        if s.sub:
            parts.append(
                f'<text x="{s.x + s.w / 2:.1f}" y="{s.y + s.h - 0.9:.1f}" '
                f'font-size="{ls:.2f}" text-anchor="middle" fill="{soft}">{e(s.sub)}</text>')

    for i, edge in enumerate(d.edges):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in edge.points)
        dash = ' stroke-dasharray="1.2,1.2"' if edge.dashed else ""
        head = f' marker-end="url(#arrow)"' if edge.arrow else ""
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{soft}" '
                     f'stroke-width="0.25"{dash}{head}/>')
        if edge.label and edge.label_at:
            x, y = edge.label_at
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" font-size="{ls:.2f}" '
                f'fill="{soft}" text-anchor="middle">{e(edge.label)}</text>')

    parts.insert(1,
                 '<defs><marker id="arrow" viewBox="0 0 6 6" refX="5" refY="3" '
                 'markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
                 f'<path d="M 0 0 L 6 3 L 0 6 z" fill="{soft}"/></marker></defs>')
    parts.append("</svg>")
    return "".join(parts)


# ─── XHTML ───────────────────────────────────────────────────────────────────

class HtmlRenderer:
    def __init__(self, theme: Theme, book: Book):
        self.theme = theme
        self.book = book
        self.fig_n = 0
        self.tbl_n = 0
        self.chapter_n = 0

    def inline(self, nodes: list[Inline]) -> str:
        out = []
        for n in nodes:
            if isinstance(n, Text):
                out.append(e(n.value))
            elif isinstance(n, Strong):
                out.append(f"<strong>{self.inline(n.children)}</strong>")
            elif isinstance(n, Em):
                out.append(f"<em>{self.inline(n.children)}</em>")
            elif isinstance(n, Code):
                out.append(f"<code>{e(n.value)}</code>")
            elif isinstance(n, Link):
                out.append(f'<a href="{e(n.href)}">{self.inline(n.children)}</a>')
            elif isinstance(n, Ref):
                out.append(f'<a href="#{e(n.target.replace(":", "-"))}">'
                           f'{e(n.target.split(":")[-1])}</a>')
        return "".join(out)

    def blocks(self, blocks: list[Block]) -> str:
        return "\n".join(self.block(b) for b in blocks)

    def block(self, b: Block) -> str:
        t = self.theme
        if isinstance(b, Paragraph):
            cls = ' class="lead"' if b.lead else ""
            return f"<p{cls}>{self.inline(b.children)}</p>"
        if isinstance(b, Heading):
            if b.level == 2:
                self.sec_n = getattr(self, "sec_n", 0) + 1
                num = f'<span class="n">{self.chapter_n}.{self.sec_n}</span>' \
                    if self.chapter_n else ""
                return f'<h2 id="{e(b.id)}">{num}{e(b.title)}</h2>'
            return f"<h{b.level} id=\"{e(b.id)}\">{e(b.title)}</h{b.level}>"
        if isinstance(b, CodeBlock):
            lines = b.code.split("\n")
            numbered = (len(lines) >= int(t.t("code.numbered_from_lines", 6))
                        if b.numbered is None else b.numbered)
            body = highlight(b.code, b.lang)
            if numbered:
                width = len(str(len(lines)))
                body_lines = body.split("\n")
                body = "\n".join(
                    f'<span class="ln">{str(i + 1).rjust(width)}</span>  {ln}'
                    for i, ln in enumerate(body_lines))
            head = ""
            if b.title:
                head = (f'<div class="code-head"><span>{e(b.title)}</span>'
                        f"<span>{e(b.lang)}</span></div>")
            return (f'<div class="code">{head}<pre><code>{body}</code></pre></div>')
        if isinstance(b, Callout):
            label = b.title or t.s(t.t(f"callouts.{b.kind}.label_key", "note"))
            return (f'<aside class="callout callout-{e(b.kind)}">'
                    f'<span class="label">{e(label)}</span>'
                    f"{self.blocks(b.blocks)}</aside>")
        if isinstance(b, Example):
            head = f'<span class="label">{e(t.s("example"))}</span>'
            title = f" <strong>{e(b.title)}</strong>" if b.title else ""
            return f'<div class="example">{head}{title}{self.blocks(b.blocks)}</div>'
        if isinstance(b, Exercise):
            return (f'<div class="exercise" id="{e(b.id.replace(":", "-"))}">'
                    f'<span class="num">{b.number}</span>'
                    f"<div>{self.blocks(b.blocks)}</div></div>")
        if isinstance(b, Summary):
            return (f'<section class="summary"><span class="label">{e(t.s("summary"))}'
                    f"</span>{self.blocks(b.blocks)}</section>")
        if isinstance(b, ListBlock):
            tag = "ol" if b.ordered else "ul"
            items = "".join(f"<li>{self._strip_p(self.blocks(i))}</li>" for i in b.items)
            return f"<{tag}>{items}</{tag}>"
        if isinstance(b, Figure):
            self.fig_n += 1
            cap = self._caption(t.s("figure"), self.fig_n, b.caption)
            return (f'<figure id="fig-{e(b.id)}">'
                    f'<img src="{e(b.src)}" alt="{e(b.alt)}"/>{cap}</figure>')
        if isinstance(b, Diagram):
            self.fig_n += 1
            layout = build_diagram(b.kind, b.spec, self.theme)
            cap = self._caption(t.s("figure"), self.fig_n, b.caption)
            return (f'<figure id="fig-{e(b.id)}">{svg(layout, self.theme)}{cap}</figure>')
        if isinstance(b, Table):
            self.tbl_n += 1
            head = "".join(f"<th>{self.inline(c)}</th>" for c in b.header)
            rows = "".join("<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in r)
                           + "</tr>" for r in b.rows)
            cap = self._caption(t.s("table"), self.tbl_n, b.caption) if b.caption else ""
            return (f'<figure id="tbl-{e(b.id)}"><table><thead><tr>{head}</tr></thead>'
                    f"<tbody>{rows}</tbody></table>{cap}</figure>")
        if isinstance(b, Quote):
            attr = (f'<span class="attribution">{e(b.attribution)}</span>'
                    if b.attribution else "")
            return f"<blockquote><p>{self.inline(b.children)}</p>{attr}</blockquote>"
        if isinstance(b, Term):
            return (f'<dl class="term"><dt>{e(b.term)}</dt>'
                    f"<dd>{self.inline(b.definition)}</dd></dl>")
        if isinstance(b, Rule):
            return '<hr class="ornament"/>'
        return ""

    def _caption(self, supplement: str, n: int, text: str) -> str:
        if not text:
            return ""
        return (f'<figcaption><span class="label">{e(supplement)} '
                f"{self.chapter_n or 1}.{n}</span>{e(text)}</figcaption>")

    @staticmethod
    def _strip_p(html_str: str) -> str:
        return re.sub(r"^<p[^>]*>(.*)</p>$", r"\1", html_str.strip(), flags=re.S)

    def chapter(self, ch: Chapter) -> str:
        self.fig_n = self.tbl_n = 0
        self.sec_n = 0
        self.chapter_n = ch.number if ch.numbered else 0
        head = ['<section class="chapter-open">']
        if ch.numbered:
            head.append(f'<span class="kicker-label">{e(self.theme.s("chapter"))}</span>'
                        f'<span class="num">{ch.number}</span>')
        head.append(f'<h1 id="{e(ch.slug)}">{e(ch.title)}</h1>')
        if ch.kicker:
            head.append(f'<p class="kicker">{e(ch.kicker)}</p>')
        head.append("<hr/></section>")
        return "\n".join(head) + "\n" + self.blocks(ch.blocks)


PAGE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"
      lang="{lang}" xml:lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body epub:type="{kind}">
{body}
</body>
</html>
"""


def write_epub(book: Book, theme: Theme, out: Path,
               cover_png: Path | None = None) -> Path:
    m = book.meta
    coll = theme.collection.get("collection", {})
    lang = m.language
    r = HtmlRenderer(theme, book)

    files: dict[str, str] = {}

    title_html = (
        f'<section class="titlepage">'
        f'<p class="collection">{e(coll.get("name", ""))}'
        + (f" · {m.volume}" if m.volume else "") + "</p>"
        f"<h1>{e(m.title)}</h1>"
        + (f'<p class="subtitle">{e(m.subtitle)}</p>' if m.subtitle else "")
        + f'<p class="author">{e(m.author)}</p></section>'
        f'<section class="copyright"><p>© {m.year} {e(m.author)} · '
        f'{e(m.publisher)}</p><p>{e(m.edition)}'
        + (f" · ISBN {e(m.isbn)}" if m.isbn else "") + "</p></section>"
    )
    files["title.xhtml"] = PAGE.format(lang=lang, title=e(m.title), kind="titlepage",
                                       body=title_html)

    spine: list[str] = []
    if cover_png and cover_png.exists():
        files["cover.xhtml"] = PAGE.format(
            lang=lang, title=e(m.title), kind="cover",
            body='<section class="cover"><img src="cover.png" '
                 f'alt="{e(m.title)}"/></section>')
        spine.append("cover.xhtml")
    spine.append("title.xhtml")
    nav_items: list[tuple[str, str]] = []
    for ch in book.chapters:
        name = f"ch-{ch.slug}.xhtml"
        files[name] = PAGE.format(lang=lang, title=e(ch.title), kind="chapter",
                                  body=r.chapter(ch))
        spine.append(name)
        nav_items.append((name, ch.title))

    files["style.css"] = theme.render("epub/style.css.j2")

    nav_list = "\n".join(f'      <li><a href="{n}">{e(t)}</a></li>'
                         for n, t in nav_items)
    files["nav.xhtml"] = PAGE.format(
        lang=lang, title=e(theme.s("toc")), kind="frontmatter",
        body=(f'<nav epub:type="toc" id="toc"><h1>{e(theme.s("toc"))}</h1>\n'
              f"    <ol>\n{nav_list}\n    </ol>\n</nav>"),
    )

    book_id = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'zeroone:' + m.slug)}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = []
    if cover_png and cover_png.exists():
        manifest.append('    <item id="cover-image" href="cover.png" '
                        'media-type="image/png" properties="cover-image"/>')
    for name in files:
        mime = ("application/xhtml+xml" if name.endswith(".xhtml")
                else "text/css" if name.endswith(".css") else "image/png")
        props = ' properties="nav"' if name == "nav.xhtml" else ""
        if name.endswith(".xhtml") and name != "nav.xhtml":
            props = ' properties="svg"'
        manifest.append(f'    <item id="{name.replace(".", "_")}" href="{name}" '
                        f'media-type="{mime}"{props}/>')

    assets = book.root / "assets"
    used = {Path(b.src).name for _, b in book.walk() if isinstance(b, Figure)}
    asset_files: list[Path] = []
    if assets.exists():
        for p in sorted(assets.glob("*")):
            # só o que o livro realmente usa: a arte da capa já vira cover.png
            if p.name in used and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".svg"):
                asset_files.append(p)
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                        "svg": "image/svg+xml"}[p.suffix.lower().lstrip(".")]
                manifest.append(f'    <item id="a_{p.stem}" href="assets/{p.name}" '
                                f'media-type="{mime}"/>')

    spine_xml = "\n".join(f'    <itemref idref="{n.replace(".", "_")}"/>' for n in spine)
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"
         xml:lang="{lang}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{book_id}</dc:identifier>
{'    <meta name="cover" content="cover-image"/>' if cover_png and cover_png.exists() else ''}
    <dc:title>{e(m.title)}</dc:title>
    <dc:creator>{e(m.author)}</dc:creator>
    <dc:language>{lang}</dc:language>
    <dc:publisher>{e(m.publisher)}</dc:publisher>
    <dc:description>{e(m.description)}</dc:description>
{chr(10).join(f'    <dc:subject>{e(k)}</dc:subject>' for k in m.keywords)}
    <meta property="dcterms:modified">{now}</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest)}
  </manifest>
  <spine>
{spine_xml}
  </spine>
</package>
"""

    path = out / f"{m.slug}.epub"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0" encoding="utf-8"?>\n'
                   '<container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                   '  <rootfiles><rootfile full-path="OEBPS/content.opf" '
                   'media-type="application/oebps-package+xml"/></rootfiles>\n'
                   "</container>\n", zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, zipfile.ZIP_DEFLATED)
        for name, content in files.items():
            z.writestr(f"OEBPS/{name}", content, zipfile.ZIP_DEFLATED)
        for p in asset_files:
            z.write(p, f"OEBPS/assets/{p.name}", zipfile.ZIP_DEFLATED)
        if cover_png and cover_png.exists():
            z.write(cover_png, "OEBPS/cover.png", zipfile.ZIP_DEFLATED)
    return path
