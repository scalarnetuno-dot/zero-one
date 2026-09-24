"""
parser.py — Markdown editorial → AST semântico.

Um só parser, sem dependência externa. O dialeto é Markdown normal mais
duas coisas:

  1. front matter YAML no topo do arquivo;
  2. contêineres `:::tipo título ... :::` para os blocos editoriais.

Tudo que o autor escreve cai em um nó de model.py. Se não cair, é erro
de escrita e o validador avisa — a pipeline nunca "inventa" um bloco.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from .model import (
    Anatomy, Block, Callout, Chapter, Code, CodeBlock, Compare, Diagram, Em,
    Example, Exercise, Figure, Heading, Http, Inline, Link, ListBlock,
    Paragraph, Quote, Ref, Rule, Story, Strong, Summary, Table, Term, Text,
    Tree, Art,
)
from .model import plain as plain_text

# ─── inline ──────────────────────────────────────────────────────────────────

_INLINE = re.compile(
    r"(?P<code>`[^`]+`)"
    r"|(?P<strong>\*\*[^*]+\*\*)"
    r"|(?P<em>\*[^*\n]+\*|_[^_\n]+_)"
    r"|(?P<link>\[[^\]]+\]\([^)\s]+\))"
    r"|(?P<ref>@[a-z]{2,4}:[A-Za-z0-9_\-]+)"
)


def parse_inline(raw: str) -> list[Inline]:
    out: list[Inline] = []
    pos = 0
    for m in _INLINE.finditer(raw):
        if m.start() > pos:
            out.append(Text(raw[pos:m.start()]))
        kind = m.lastgroup
        tok = m.group()
        if kind == "code":
            out.append(Code(tok[1:-1]))
        elif kind == "strong":
            out.append(Strong(parse_inline(tok[2:-2])))
        elif kind == "em":
            out.append(Em(parse_inline(tok[1:-1])))
        elif kind == "link":
            text, href = tok[1:-1].split("](", 1)
            out.append(Link(href, parse_inline(text)))
        elif kind == "ref":
            out.append(Ref(tok[1:]))
        pos = m.end()
    if pos < len(raw):
        out.append(Text(raw[pos:]))
    return out or [Text("")]


# ─── utilidades ──────────────────────────────────────────────────────────────

_ATTR = re.compile(r'(\w+)(?:=(?:"([^"]*)"|([^\s]+)))?')


def parse_attrs(raw: str) -> tuple[str, dict[str, str]]:
    """`Título livre key="v" flag` → ("Título livre", {"key": "v", "flag": ""})."""
    attrs: dict[str, str] = {}
    title_parts: list[str] = []
    for tok in _split_tokens(raw.strip()):
        m = _ATTR.fullmatch(tok)
        if m and ("=" in tok or tok in _FLAGS):
            attrs[m.group(1)] = m.group(2) or m.group(3) or ""
        else:
            title_parts.append(tok)
    return " ".join(title_parts).strip(), attrs


_FLAGS = {"numbered", "plain", "wide", "tight", "nobreak"}

# Diretivas que são MARCADORES dentro de outro bloco, não contêineres
# próprios: não abrem um nível novo e não precisam de fechamento.
_MARKERS = {"answer"}


def _split_tokens(s: str) -> list[str]:
    out, buf, quoted = [], "", False
    for ch in s:
        if ch == '"':
            quoted = not quoted
            buf += ch
        elif ch == " " and not quoted:
            if buf:
                out.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def slugify(text: str) -> str:
    n = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    n = re.sub(r"[^\w\s-]", "", n).strip().lower()
    return re.sub(r"[-\s]+", "-", n) or "x"


# ─── parser de blocos ────────────────────────────────────────────────────────

_FENCE = re.compile(r"^(```|~~~)(.*)$")
_DIRECTIVE = re.compile(r"^:::+\s*(\w+)?\s*(.*)$")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UL = re.compile(r"^[-*]\s+(.*)$")
_OL = re.compile(r"^(\d+)[.)]\s+(.*)$")
_IMG = re.compile(r'^!\[(.*?)\]\(([^)\s]+)(?:\s+"(.*?)")?\)\s*$')
_TABLE_SEP = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


class ParseError(Exception):
    pass


def parse_chapter(path: Path, default_number: int = 0,
                  overrides: dict[str, Any] | None = None) -> Chapter:
    """Lê um capítulo. `overrides` sobrepõe o front matter — a tradução
    herda número, slug e parte do original; a prévia marca `previa`."""
    raw = path.read_text(encoding="utf-8")
    meta, body = _front_matter(raw)
    meta.update(overrides or {})
    lines = body.splitlines()

    chapter = Chapter(
        number=int(meta.get("number", default_number)),
        title=str(meta.get("title", path.stem)),
        slug=str(meta.get("slug", slugify(str(meta.get("title", path.stem))))),
        kicker=str(meta.get("kicker", "")),
        epigraph=str(meta.get("epigraph", "")),
        epigraph_by=str(meta.get("epigraph_by", "")),
        goal=str(meta.get("goal", "")),
        source=path,
        part=str(meta.get("part", "")),
        matter=str(meta.get("matter", "body")),  # type: ignore[arg-type]
        numbered=bool(meta.get("numbered", meta.get("matter", "body") == "body")),
        locked=bool(meta.get("previa", False)),
    )
    chapter.blocks = _blocks(lines, path)
    if chapter.locked:
        # capítulo fechado: só os títulos de seção, que seguem no sumário
        chapter.blocks = [b for b in chapter.blocks if isinstance(b, Heading)]

    n = 0
    for b in chapter.walk():
        if isinstance(b, Exercise):
            n += 1
            b.number = n
            b.id = b.id or f"ex:{chapter.slug}-{n}"
    return chapter


def _front_matter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end < 0:
        return {}, raw
    head = raw[3:end]
    rest = raw[end + 4:].lstrip("\n")
    return (yaml.safe_load(head) or {}), rest


def _blocks(lines: list[str], src: Path) -> list[Block]:
    out: list[Block] = []
    i = 0
    para: list[str] = []
    first_in_section = True

    def flush() -> None:
        nonlocal para, first_in_section
        if para:
            out.append(Paragraph(parse_inline(" ".join(para).strip()),
                                 lead=first_in_section))
            first_in_section = False
            para = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush()
            i += 1
            continue

        m = _HEADING.match(line)
        if m:
            flush()
            title = m.group(2)
            children = parse_inline(title)
            out.append(Heading(len(m.group(1)), plain_text(children),
                               slugify(title), children))
            first_in_section = True
            i += 1
            continue

        m = _FENCE.match(line)
        if m:
            flush()
            lang_raw = m.group(2).strip()
            body, i = _take_until(lines, i + 1, lambda ln: _FENCE.match(ln))
            lang, attrs = (lang_raw.split(" ", 1) + [""])[:2] if lang_raw else ("text", "")
            title, kv = parse_attrs(attrs)
            out.append(CodeBlock(
                code="\n".join(body),
                lang=(lang or "text").lower(),
                title=kv.get("title", title),
                numbered=True if "numbered" in kv else (False if "plain" in kv else None),
                caption=kv.get("caption", ""),
                id=kv.get("id", ""),
            ))
            first_in_section = True
            continue

        m = _DIRECTIVE.match(line)
        if m and m.group(1):
            flush()
            kind = m.group(1).lower()
            title, kv = parse_attrs(m.group(2))
            body, i = _take_until(lines, i + 1,
                                  lambda ln: _DIRECTIVE.match(ln) and not _DIRECTIVE.match(ln).group(1),
                                  nestable=True)
            out.append(_directive(kind, title, kv, body, src))
            first_in_section = True
            continue

        m = _IMG.match(line)
        if m:
            flush()
            alt, srcpath, cap = m.group(1), m.group(2), m.group(3) or ""
            out.append(Figure(src=srcpath, caption=cap, alt=alt or cap,
                              id=slugify(cap or Path(srcpath).stem)))
            first_in_section = True
            i += 1
            continue

        if stripped in ("---", "***", "* * *"):
            flush()
            out.append(Rule())
            first_in_section = True
            i += 1
            continue

        if line.lstrip().startswith(">"):
            flush()
            quote, i = _take_while(lines, i, lambda ln: ln.lstrip().startswith(">"))
            out.append(_quote([ln.lstrip()[1:].strip() for ln in quote]))
            first_in_section = True
            continue

        # "25. A documentação..." no meio de um parágrafo é uma frase que
        # quebrou de linha, não um item de lista: só abre lista em bloco novo.
        if not para and (_UL.match(stripped) or _OL.match(stripped)):
            flush()
            block, i = _list(lines, i, src)
            out.append(block)
            first_in_section = True
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            flush()
            block, i = _table(lines, i)
            out.append(block)
            first_in_section = True
            continue

        para.append(stripped)
        i += 1

    flush()
    return out


def _take_until(lines: list[str], i: int, is_end, nestable: bool = False) -> tuple[list[str], int]:
    body: list[str] = []
    depth = 0
    in_fence = False
    while i < len(lines):
        ln = lines[i]
        # o rastreio de cerca só vale ao varrer um contêiner (nestable):
        # dentro de um bloco de código já estamos "na cerca" por definição.
        if nestable and _FENCE.match(ln):
            in_fence = not in_fence
        if not in_fence and nestable:
            m = _DIRECTIVE.match(ln)
            if m and m.group(1) and m.group(1).lower() not in _MARKERS:
                depth += 1
        if not in_fence and is_end(ln):
            if depth == 0:
                return body, i + 1
            depth -= 1
        body.append(ln)
        i += 1
    return body, i


def _take_while(lines: list[str], i: int, pred) -> tuple[list[str], int]:
    body: list[str] = []
    while i < len(lines) and pred(lines[i]):
        body.append(lines[i])
        i += 1
    return body, i


def _quote(raw_lines: list[str]) -> Quote:
    attribution = ""
    if raw_lines and raw_lines[-1].startswith(("—", "--", "–")):
        attribution = raw_lines.pop().lstrip("—–- ").strip()
    return Quote(parse_inline(" ".join(l for l in raw_lines if l).strip()), attribution)


def _list(lines: list[str], i: int, src: Path) -> tuple[ListBlock, int]:
    ordered = bool(_OL.match(lines[i].strip()))
    items: list[list[Block]] = []
    current: list[str] = []
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            if i + 1 < len(lines) and lines[i + 1].startswith(("  ", "\t")):
                current.append("")
                i += 1
                continue
            break
        m = _OL.match(stripped) if ordered else _UL.match(stripped)
        if m and not raw.startswith(("  ", "\t")):
            if current:
                items.append(_blocks(current, src))
            current = [m.group(2) if ordered else m.group(1)]
            i += 1
            continue
        if raw.startswith(("  ", "\t")):
            current.append(raw[2:] if raw.startswith("  ") else raw[1:])
            i += 1
            continue
        break
    if current:
        items.append(_blocks(current, src))
    return ListBlock(items=items, ordered=ordered), i


def _table(lines: list[str], i: int) -> tuple[Table, int]:
    def cells(ln: str) -> list[str]:
        return [c.strip() for c in ln.strip().strip("|").split("|")]

    header = [parse_inline(c) for c in cells(lines[i])]
    align = []
    for spec in cells(lines[i + 1]):
        align.append("center" if spec.startswith(":") and spec.endswith(":")
                     else "right" if spec.endswith(":") else "left")
    i += 2
    rows: list[list[list[Inline]]] = []
    caption = ""
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append([parse_inline(c) for c in cells(lines[i])])
        i += 1
    j = i
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j < len(lines) and lines[j].strip().lower().startswith(("table:", "tabela:")):
        parts = [lines[j].split(":", 1)[1].strip()]
        j += 1
        while j < len(lines) and lines[j].strip():   # legenda continua
            parts.append(lines[j].strip())
            j += 1
        caption = " ".join(parts)
        i = j
    return Table(header=header, rows=rows, align=align, caption=caption,
                 id=slugify(caption) if caption else ""), i


CALLOUT_KINDS = {
    "tip", "warning", "note", "key", "practice",
    "trivia", "pitfall", "history", "checkpoint", "milestone",
}


def _directive(kind: str, title: str, kv: dict[str, str], body: list[str],
               src: Path) -> Block:
    if kind in CALLOUT_KINDS:
        return Callout(kind=kind, title=title, blocks=_blocks(body, src))
    if kind == "example":
        return Example(title=title, blocks=_blocks(body, src))
    if kind == "exercise":
        answer: list[str] = []
        content: list[str] = []
        sink = content
        for ln in body:
            m = _DIRECTIVE.match(ln)
            if m and m.group(1) == "answer":
                sink = answer
                continue
            sink.append(ln)
        return Exercise(
            blocks=_blocks(content, src),
            level=int(kv.get("level", "1")),
            answer=_blocks(answer, src) if answer else [],
            id=kv.get("id", ""),
        )
    if kind == "summary":
        return Summary(blocks=_blocks(body, src))
    if kind == "diagram":
        spec = yaml.safe_load("\n".join(body)) or {}
        if not isinstance(spec, dict):
            raise ParseError(f"{src.name}: :::diagram precisa de YAML (mapa), veio {type(spec)}")
        return Diagram(kind=kv.get("type", title or "flowchart"),
                       spec=spec, caption=kv.get("caption", spec.get("caption", "")),
                       id=kv.get("id", slugify(spec.get("caption", "") or title or "diagrama")))
    if kind == "anatomy":
        spec = yaml.safe_load("\n".join(body)) or {}
        if not isinstance(spec, dict) or "code" not in spec:
            raise ParseError(f"{src.name}: :::anatomy precisa de YAML com `code:`")
        notes = []
        for n in spec.get("notes") or []:
            notes.append((int(n["line"]), parse_inline(str(n["text"]))))
        return Anatomy(code=str(spec["code"]).rstrip("\n"),
                       lang=str(spec.get("lang", kv.get("lang", "java"))),
                       title=str(spec.get("title", kv.get("title", title))), notes=notes,
                       id=kv.get("id", ""))
    if kind == "story":
        return Story(title=title, blocks=_blocks(body, src))
    if kind == "art":
        # O atributo pode vir na linha da diretiva OU no corpo do bloco:
        # trocar o marcador pela arte pronta é um gesto de copiar e colar,
        # e o parser não pode punir quem escreveu de um jeito razoável.
        campos, prompt = _art_fields(body)
        kv = {**campos, **kv}
        return Art(prompt=prompt,
                   caption=kv.get("caption", title),
                   src=kv.get("src", ""),
                   id=kv.get("id", slugify(kv.get("caption", title) or "arte")))
    if kind == "http":
        return _http(title, kv, body, src)
    if kind == "tree":
        return _tree(title, body)
    if kind == "compare":
        sep = [i for i, l in enumerate(body) if l.strip() == "---"]
        if not sep:
            raise ParseError(f"{src.name}: :::compare precisa de `---` entre os lados")
        i0 = sep[0]
        return Compare(
            left="\n".join(body[:i0]).strip("\n"),
            right="\n".join(body[i0 + 1:]).strip("\n"),
            left_label=kv.get("left", ""), right_label=kv.get("right", ""),
            lang=kv.get("lang", "java"))
    if kind == "term":
        return Term(term=title, definition=parse_inline(" ".join(l.strip() for l in body).strip()))
    if kind == "quote":
        return _quote([l.strip() for l in body if l.strip()])
    raise ParseError(f"{src.name}: bloco desconhecido ':::{kind}'")


def _http(title: str, kv: dict[str, str], body: list[str], src: Path) -> Http:
    """`VERBO /caminho` + cabeçalhos + corpo, `---`, status + corpo."""
    sep = [i for i, l in enumerate(body) if l.strip() == "---"]
    cut = sep[0] if sep else len(body)
    req, res = body[:cut], body[cut + 1:]

    def split(lines: list[str]) -> tuple[str, list[str], str]:
        lines = [l for l in lines]
        while lines and not lines[0].strip():
            lines.pop(0)
        if not lines:
            return "", [], ""
        first = lines[0].strip()
        headers: list[str] = []
        i = 1
        while i < len(lines) and lines[i].strip():
            headers.append(lines[i].strip())
            i += 1
        body_txt = "\n".join(lines[i:]).strip("\n")
        return first, headers, body_txt

    req_first, req_headers, req_body = split(req)
    res_first, res_headers, res_body = split(res)
    parts = req_first.split(None, 1)
    if not parts:
        raise ParseError(f"{src.name}: :::http sem linha `VERBO /caminho`")
    return Http(
        verb=parts[0].upper(), path=parts[1] if len(parts) > 1 else "",
        req_headers=req_headers, req_body=req_body,
        status=res_first, res_headers=res_headers, res_body=res_body,
        title=title, id=kv.get("id", ""))


def _tree(title: str, body: list[str]) -> Tree:
    """Indentação de 2 espaços = um nível. A pipeline desenha os fios."""
    lines: list[tuple[int, str, str]] = []
    for raw in body:
        if not raw.strip():
            continue
        stripped = raw.lstrip(" ")
        level = (len(raw) - len(stripped)) // 2
        name, _, note = stripped.partition("#")
        lines.append((level, name.strip(), note.strip()))
    return Tree(lines=lines, title=title)


_ART_FIELD = re.compile(
    r'^\s*(src|caption|id)\s*[:=]\s*["“]?(.+?)["”]?\s*$', re.I)


def _art_fields(body: list[str]) -> tuple[dict[str, str], str]:
    """Separa `src:`/`caption:`/`id:` do texto da descrição."""
    campos: dict[str, str] = {}
    resto: list[str] = []
    for linha in body:
        m = _ART_FIELD.match(linha)
        if m:
            campos[m.group(1).lower()] = m.group(2).strip()
        elif linha.strip():
            resto.append(linha.strip())
    return campos, " ".join(resto).strip()
