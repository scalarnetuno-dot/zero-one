"""
model.py — o documento semântico.

Este arquivo é o contrato entre o conteúdo e QUALQUER saída.
Nada aqui sabe o que é PDF, EPUB, cor, fonte ou milímetro.
Se um nó novo precisar existir, ele nasce aqui primeiro.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Literal

# ─── inline ──────────────────────────────────────────────────────────────────


@dataclass
class Text:
    value: str


@dataclass
class Strong:
    children: list["Inline"]


@dataclass
class Em:
    children: list["Inline"]


@dataclass
class Code:
    value: str


@dataclass
class Link:
    href: str
    children: list["Inline"]


@dataclass
class Ref:
    """Referência cruzada: @fig:pilha, @cap:loops, @ex:3."""
    target: str


Inline = Text | Strong | Em | Code | Link | Ref


# ─── blocos ──────────────────────────────────────────────────────────────────


@dataclass
class Heading:
    level: int                      # 2 = seção (4.1), 3 = subseção, 4 = rótulo
    title: str                      # texto puro: sumário, validação, busca
    id: str = ""
    children: list["Inline"] = field(default_factory=list)  # com formatação


@dataclass
class Paragraph:
    children: list[Inline]
    lead: bool = False              # primeiro parágrafo: sem recuo


@dataclass
class CodeBlock:
    code: str
    lang: str = "text"
    title: str = ""
    numbered: bool | None = None    # None = decide pelo tokens.yaml
    caption: str = ""
    id: str = ""


@dataclass
class Figure:
    src: str
    caption: str = ""
    alt: str = ""
    width: float = 1.0              # fração da mancha
    id: str = ""


@dataclass
class Diagram:
    kind: str                       # flowchart | sequence | stack | blocks
    spec: dict[str, Any]
    caption: str = ""
    id: str = ""


@dataclass
class Callout:
    kind: str                       # tip | warning | note | key | practice
    title: str
    blocks: list["Block"]


@dataclass
class Example:
    title: str
    blocks: list["Block"]


@dataclass
class Exercise:
    blocks: list["Block"]
    level: int = 1                  # 1..3
    answer: list["Block"] = field(default_factory=list)
    number: int = 0                 # atribuído no parse
    id: str = ""


@dataclass
class Summary:
    blocks: list["Block"]


@dataclass
class Anatomy:
    """Código anotado: crachá na linha, legenda embaixo."""
    code: str
    lang: str = "java"
    title: str = ""
    notes: list[tuple[int, list["Inline"]]] = field(default_factory=list)
    id: str = ""


@dataclass
class Http:
    """Par requisição/resposta — o livro é sobre API."""
    verb: str = "GET"
    path: str = ""
    req_headers: list[str] = field(default_factory=list)
    req_body: str = ""
    status: str = ""
    res_headers: list[str] = field(default_factory=list)
    res_body: str = ""
    title: str = ""
    id: str = ""


@dataclass
class Tree:
    """Estrutura de pastas: o autor indenta, a pipeline desenha os fios."""
    lines: list[tuple[int, str, str]] = field(default_factory=list)  # nível, nome, nota
    title: str = ""


@dataclass
class Story:
    """Cena corporativa: a camada satélite que envolve o conteúdo técnico."""
    title: str = ""
    blocks: list["Block"] = field(default_factory=list)


@dataclass
class Art:
    """Ilustração — existente (`src`) ou ainda por produzir (só o `prompt`)."""
    prompt: str = ""
    caption: str = ""
    src: str = ""
    id: str = ""
    chapter: str = ""          # preenchido no carregamento, para o manifesto


@dataclass
class Compare:
    """Antes e depois, lado a lado."""
    left: str
    right: str
    left_label: str = ""
    right_label: str = ""
    lang: str = "java"


@dataclass
class ListBlock:
    items: list[list["Block"]]
    ordered: bool = False


@dataclass
class Table:
    header: list[list[Inline]]
    rows: list[list[list[Inline]]]
    align: list[str] = field(default_factory=list)
    caption: str = ""
    id: str = ""


@dataclass
class Quote:
    children: list[Inline]
    attribution: str = ""


@dataclass
class Term:
    term: str
    definition: list[Inline]


@dataclass
class Rule:
    pass


Block = (
    Heading | Paragraph | CodeBlock | Figure | Diagram | Callout | Example
    | Exercise | Summary | ListBlock | Table | Quote | Term | Rule
    | Anatomy | Http | Tree | Compare | Story | Art
)


# ─── estrutura do livro ──────────────────────────────────────────────────────


@dataclass
class Chapter:
    number: int
    title: str
    slug: str
    kicker: str = ""                # a frase sob o título na abertura
    epigraph: str = ""              # citação na abertura
    epigraph_by: str = ""
    goal: str = ""                  # o que o leitor sai sabendo fazer
    blocks: list[Block] = field(default_factory=list)
    source: Path | None = None
    part: str = ""
    matter: Literal["front", "body", "back"] = "body"
    numbered: bool = True

    def walk(self) -> Iterator[Block]:
        yield from _walk(self.blocks)


@dataclass
class Part:
    number: int
    title: str
    blurb: str = ""
    id: str = ""                    # casa com `part:` do front matter
    chapters: list[str] = field(default_factory=list)  # títulos, para a abertura


@dataclass
class BookMeta:
    title: str
    subtitle: str = ""
    author: str = ""
    slug: str = ""
    volume: int = 0
    accent: str = "red"
    accent_hex: str = ""
    language: str = "pt-BR"
    isbn: str = ""
    publisher: str = ""
    year: int = 0
    edition: str = "1ª edição"
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    course_slug: str = ""           # de onde o conteúdo veio, na Knowpill
    cover_bird: str = ""            # ilustração do volume (opcional)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Book:
    meta: BookMeta
    chapters: list[Chapter] = field(default_factory=list)
    parts: list[Part] = field(default_factory=list)
    root: Path = Path(".")
    missing: list[str] = field(default_factory=list)  # listados, ainda não escritos

    @property
    def body(self) -> list[Chapter]:
        return [c for c in self.chapters if c.matter == "body"]

    def walk(self) -> Iterator[tuple[Chapter, Block]]:
        for ch in self.chapters:
            for b in ch.walk():
                yield ch, b


def _walk(blocks: list[Block]) -> Iterator[Block]:
    """Percorre blocos e seus filhos, em ordem de leitura."""
    for b in blocks:
        yield b
        if isinstance(b, (Callout, Example, Summary, Story)):
            yield from _walk(b.blocks)
        elif isinstance(b, Exercise):
            yield from _walk(b.blocks)
            yield from _walk(b.answer)
        elif isinstance(b, ListBlock):
            for item in b.items:
                yield from _walk(item)


def plain(inlines: list[Inline]) -> str:
    """Texto puro de uma sequência inline — para validação, alt, TOC e busca."""
    out: list[str] = []
    for n in inlines:
        if isinstance(n, Text):
            out.append(n.value)
        elif isinstance(n, Code):
            out.append(n.value)
        elif isinstance(n, Ref):
            out.append(n.target)
        elif isinstance(n, (Strong, Em, Link)):
            out.append(plain(n.children))
    return "".join(out)
