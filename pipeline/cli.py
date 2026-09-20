"""
cli.py — a porta de entrada.

    python -m pipeline list
    python -m pipeline check java-one
    python -m pipeline build java-one
    python -m pipeline build all --strict
    python -m pipeline new python-one --title "Python One" --accent blue --volume 2
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from .build import BUILD, build, prepare
from .cover import build_wrap
from .loader import BOOKS, list_books, load_book
from .preview import generate_preview
from .theme import COLLECTION, load_theme
from .validate import validate_ast


def cmd_list(args: argparse.Namespace) -> int:
    for slug in list_books():
        b = load_book(slug)
        vol = f"vol. {b.meta.volume}" if b.meta.volume else "—"
        print(f"  {slug:<22} {vol:<8} {b.meta.accent:<7} "
              f"{len(b.body)} capítulos  {b.meta.title}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    bad = 0
    for slug in _slugs(args.slug):
        book, theme, _ = prepare(slug)
        issues = validate_ast(book, theme)
        errs = [i for i in issues if i.level == "error"]
        print(f"\n{slug}: {len(issues)} apontamentos, {len(errs)} erros")
        for i in issues:
            mark = {"error": "ERRO ", "warn": "aviso", "info": "nota "}[i.level]
            print(f"  {mark} {i.where}: {i.message}")
        bad += len(errs)
    return 1 if bad else 0


def cmd_build(args: argparse.Namespace) -> int:
    rc = 0
    for slug in _slugs(args.slug):
        print(f"\n▸ {slug}")
        res = build(slug, pdf=not args.epub_only, epub=not args.pdf_only,
                    strict=args.strict)
        print(f"  pronto em {res.seconds:.1f}s"
              f"  ·  {len(res.errors)} erros, "
              f"{len([i for i in res.issues if i.level == 'warn'])} avisos")
        if res.errors and args.strict:
            rc = 1
    return rc


def cmd_new(args: argparse.Namespace) -> int:
    dest = BOOKS / args.slug
    if dest.exists():
        print(f"já existe: {dest}", file=sys.stderr)
        return 1
    shutil.copytree(BOOKS / "_template", dest)
    cfg = (dest / "book.yaml").read_text(encoding="utf-8")
    cfg = (cfg.replace("{{TITLE}}", args.title or args.slug)
              .replace("{{SLUG}}", args.slug)
              .replace("{{ACCENT}}", args.accent)
              .replace("{{VOLUME}}", str(args.volume))
              .replace("{{SUBTITLE}}", args.subtitle or ""))
    (dest / "book.yaml").write_text(cfg, encoding="utf-8")
    print(f"criado: {dest}")
    print("  edite book.yaml e escreva em content/*.md; depois:")
    print(f"  python -m pipeline build {args.slug}")
    return 0


def cmd_cover(args: argparse.Namespace) -> int:
    from pypdf import PdfReader

    for slug in _slugs(args.slug):
        miolo = BUILD / slug / f"{slug}.pdf"
        if not miolo.exists():
            print(f"  {slug}: rode 'build' antes — a lombada depende do miolo",
                  file=sys.stderr)
            return 1
        pages = args.pages or len(PdfReader(str(miolo)).pages)
        pdf = build_wrap(slug, pages, BUILD / slug, paper=args.paper)
        print(f"  capa    {pdf.name}  (lombada de {pages} páginas, papel {args.paper})")
        if pages < 100:
            print("    nota: abaixo de 100 páginas a KDP não imprime texto na lombada")
    return 0


def cmd_art(args: argparse.Namespace) -> int:
    """Arte provisória: capa e figuras de exemplo, geradas localmente."""
    from .placeholder import cover_art, figure

    for slug in _slugs(args.slug):
        book, theme, _ = prepare(slug)
        assets = BOOKS / slug / "assets"
        made = [cover_art(assets / "capa.png", theme.accent_hex, seed=slug)]
        for i in range(1, args.figures + 1):
            made.append(figure(assets / f"exemplo-{i}.png", theme.accent_hex,
                               seed=f"{slug}-{i}"))
        for p in made:
            print(f"  arte    assets/{p.name}")
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    for slug in _slugs(args.slug):
        shutil.rmtree(BUILD / slug, ignore_errors=True)
        print(f"  limpo build/{slug}")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    for slug in _slugs(args.slug):
        generated = generate_preview(slug)
        print(f"  prévia  {slug}: {len(generated)} capítulos gerados")
    return 0


def _slugs(raw: str) -> list[str]:
    return list_books() if raw in ("all", "*") else [raw]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pipeline", description="Coleção Zero One")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="lista os livros").set_defaults(fn=cmd_list)

    c = sub.add_parser("check", help="valida sem gerar arquivo")
    c.add_argument("slug")
    c.set_defaults(fn=cmd_check)

    b = sub.add_parser("build", help="gera PDF e EPUB")
    b.add_argument("slug")
    b.add_argument("--pdf-only", action="store_true")
    b.add_argument("--epub-only", action="store_true")
    b.add_argument("--strict", action="store_true", help="erro de validação para o build")
    b.set_defaults(fn=cmd_build)

    n = sub.add_parser("new", help="cria um volume novo a partir do modelo")
    n.add_argument("slug")
    n.add_argument("--title", default="")
    n.add_argument("--subtitle", default="")
    n.add_argument("--accent", default="blue")
    n.add_argument("--volume", type=int, default=0)
    n.set_defaults(fn=cmd_new)

    cv = sub.add_parser("cover", help="capa completa da KDP (contracapa+lombada+capa)")
    cv.add_argument("slug")
    cv.add_argument("--paper", default="white", choices=["white", "cream", "color"])
    cv.add_argument("--pages", type=int, default=0, help="forçar contagem de páginas")
    cv.set_defaults(fn=cmd_cover)

    ar = sub.add_parser("art", help="gera arte provisória (capa e figuras)")
    ar.add_argument("slug")
    ar.add_argument("--figures", type=int, default=2)
    ar.set_defaults(fn=cmd_art)

    cl = sub.add_parser("clean", help="apaga o build")
    cl.add_argument("slug")
    cl.set_defaults(fn=cmd_clean)

    pv = sub.add_parser("preview", help="gera capítulos e assets de uma prévia")
    pv.add_argument("slug")
    pv.set_defaults(fn=cmd_preview)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
