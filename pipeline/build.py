"""
build.py — orquestra a pipeline.

    conteúdo → AST → validação → componentes → Typst/XHTML → PDF/EPUB

Duas passagens no PDF: a primeira descobre o número de páginas, a segunda
aplica a margem de lombada que a KDP exige para aquela espessura.
"""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import typst

from .collection_page import COLLECTION_DIR, write_thumbnails
from .cover import build_front, find_cover_art, merge_with_cover
from .diagram_png import render_all as render_diagram_png
from .loader import asset_dirs, load_book, theme_overrides
from .model import Art, Book
from .render_epub import write_epub
from .render_typst import render as render_typst
from .theme import FONTS, ROOT, Theme, load_theme
from .validate import Issue, validate_ast, validate_pdf

BUILD = ROOT / "build"


@dataclass
class BuildResult:
    slug: str
    pdf: Path | None = None          # miolo limpo, para a KDP impressa
    reading_pdf: Path | None = None   # capa + miolo, para ler e mandar
    cover: Path | None = None
    epub: Path | None = None
    pages: int = 0
    seconds: float = 0.0
    issues: list[Issue] = field(default_factory=list)
    typst_warnings: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]


def prepare(slug: str) -> tuple[Book, Theme, Path]:
    book = load_book(slug)
    theme = load_theme(accent=book.meta.accent, language=book.meta.language,
                       overrides=theme_overrides(slug))
    out = BUILD / slug
    out.mkdir(parents=True, exist_ok=True)
    return book, theme, out


def build(slug: str, pdf: bool = True, epub: bool = True, cover: bool = True,
          strict: bool = False, verbose: bool = True) -> BuildResult:
    t0 = time.time()
    book, theme, out = prepare(slug)
    res = BuildResult(slug=slug)

    res.issues = validate_ast(book, theme)
    errors = res.errors
    if verbose:
        _report(res.issues)
    if errors and strict:
        res.seconds = time.time() - t0
        return res

    cover_png: Path | None = None
    if cover:
        res.cover, cover_png = build_front(slug, out)
        if verbose:
            art = find_cover_art(slug, book)
            print(f"  capa    {res.cover.name}"
                  + (f"  (arte: {art.name})" if art else "  (sem arte: só tipografia)"))

    if pdf:
        res.pdf, res.pages, res.typst_warnings = _build_pdf(book, theme, out, verbose)
        res.issues += validate_pdf(res.pdf, theme, res.pages)
        if res.cover:
            res.reading_pdf = merge_with_cover(
                res.cover, res.pdf, out / f"{slug}-leitura.pdf")
            if verbose:
                print(f"  pdf     {res.reading_pdf.name}  (capa + miolo)")
    manifesto, pendentes, prontas = write_art_manifest(book, out)
    if verbose and (pendentes or prontas):
        print(f"  arte    {manifesto.name}  ({pendentes} a produzir, "
              f"{prontas} prontas)")

    if epub:
        # PNG de cada diagrama, no MESMO traço do PDF (Typst desenha os
        # dois): o Kindle não escala SVG inline de forma confiável, então
        # o EPUB usa imagem pronta em vez de <svg> embutido.
        diagram_png = render_diagram_png(book, theme, out)
        res.epub = write_epub(book, theme, out, cover_png=cover_png,
                              diagram_png=diagram_png)
        if verbose:
            print(f"  epub    {res.epub.name}"
                  + ("  (com capa)" if cover_png else "")
                  + (f"  ({len(diagram_png)} diagramas em PNG)" if diagram_png else ""))

    res.seconds = time.time() - t0
    return res


def write_art_manifest(book: Book, out: Path) -> tuple[Path, int, int]:
    """Lista toda ilustração do livro — a ponte com a etapa de geração de arte.

    Arte com `src` já existe; arte só com `prompt` ainda é um buraco marcado
    na página. O manifesto é o que o gerador de imagens consome.
    """
    pendentes: list[dict] = []
    prontas: list[dict] = []
    for ch in book.chapters:
        for blk in ch.walk():
            if not isinstance(blk, Art):
                continue
            item = {
                "chapter": ch.number if ch.numbered else 0,
                "chapter_title": ch.title,
                "id": blk.id,
                "caption": blk.caption,
                "prompt": blk.prompt,
                "src": blk.src,
            }
            (prontas if blk.src else pendentes).append(item)

    dados = {"book": book.meta.slug, "pending": pendentes, "done": prontas}
    (out / "art-prompts.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    linhas = [f"# Arte — {book.meta.title}", "",
              f"{len(pendentes)} a produzir · {len(prontas)} prontas", "",
              "Estilo da coleção: ilustração editorial minimalista, humor de",
              "revista de tecnologia, composição limpa, poucos elementos,",
              "personagens expressivos, sem estética infantil, texto mínimo.",
              ""]
    linhas += ["Não desenhe a legenda dentro da imagem: a pipeline numera e",
               "imprime a legenda embaixo. Mínimo de 300 DPI no tamanho",
               "impresso (≈1400 px de largura para a mancha de 6×9).", ""]
    for item in pendentes:
        linhas += [f"## cap. {item['chapter']} · {item['id']}", "",
                   f"**Legenda:** {item['caption'] or '—'}", "",
                   item["prompt"], "",
                   f"Salve em `books/<livro>/assets/{item['id']}.png` e",
                   "acrescente `src` ao bloco, **sem apagar a legenda nem a",
                   "descrição** — o manifesto usa as duas:", "",
                   "```",
                   f':::art caption="{item["caption"]}" src="{item["id"]}.png"',
                   "(a descrição continua aqui)",
                   ":::",
                   "```", ""]
    path = out / "art-prompts.md"
    path.write_text("\n".join(linhas), encoding="utf-8")
    return path, len(pendentes), len(prontas)


def _build_pdf(book: Book, theme: Theme, out: Path,
               verbose: bool) -> tuple[Path, int, list[str]]:
    src = out / "typst"
    src.mkdir(parents=True, exist_ok=True)

    # da pasta mais geral para a mais específica: a tradução sobrescreve
    assets_dst = src / "assets"
    shutil.rmtree(assets_dst, ignore_errors=True)
    assets_dst.mkdir(parents=True)
    for assets_src in reversed(asset_dirs(book)):
        if assets_src.exists():
            shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
    shutil.rmtree(src / COLLECTION_DIR, ignore_errors=True)
    write_thumbnails(book, src / COLLECTION_DIR)

    (src / "editorial.tmTheme").write_text(theme.tm_theme(), encoding="utf-8")

    def write_sources(pages: int) -> Path:
        (src / "style.typ").write_text(theme.render("style.typ.j2"), encoding="utf-8")
        doc = render_typst(book, theme, pages_estimate=pages)
        main = src / f"{book.meta.slug}.typ"
        main.write_text(doc, encoding="utf-8")
        return main

    main = write_sources(0)
    pdf_path = out / f"{book.meta.slug}.pdf"

    compiler = typst.Compiler(input=main, root=src, font_paths=[FONTS],
                              ignore_system_fonts=True)
    _, warnings = compiler.compile_with_warnings(output=pdf_path)
    pages = _page_count(compiler, pdf_path)

    # segunda passagem: a lombada muda a margem interna
    if theme.gutter_extra(pages) != theme.gutter_extra(0):
        main = write_sources(pages)
        compiler = typst.Compiler(input=main, root=src, font_paths=[FONTS],
                                  ignore_system_fonts=True)
        _, warnings = compiler.compile_with_warnings(output=pdf_path)
        pages = _page_count(compiler, pdf_path)

    msgs = sorted({_warn_text(w) for w in warnings})
    if verbose:
        print(f"  pdf     {pdf_path.name}  ({pages} páginas)")
        for m in msgs[:10]:
            print(f"    typst: {m}")
    return pdf_path, pages, msgs


def _warn_text(w: object) -> str:
    return getattr(w, "message", str(w))


def _page_count(compiler: typst.Compiler, pdf_path: Path) -> int:
    """Páginas FÍSICAS — é o que a gráfica cobra e o que define a lombada."""
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        pass
    try:  # sem pypdf: o contador do Typst (ignora a renumeração do miolo)
        data = json.loads(compiler.query("<pagecount>", field="value", format="json"))
        return int(data[0]) if data else 0
    except Exception:
        return 0


def _report(issues: list[Issue]) -> None:
    for i in issues:
        mark = {"error": "ERRO ", "warn": "aviso", "info": "nota "}[i.level]
        print(f"  {mark} {i.where}: {i.message}")
