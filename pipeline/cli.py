"""
cli.py — a porta de entrada.

    python -m pipeline list
    python -m pipeline check java-one
    python -m pipeline build java-one
    python -m pipeline build all --strict
    python -m pipeline new python-one --title "Python One" --accent blue --volume 2
    python -m pipeline i18n php-one-v1             # situação das traduções
    python -m pipeline i18n php-one-v1 --new fr    # abre uma tradução nova
    python -m pipeline i18n php-one-v1-en --stamp  # marca como em dia
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

from .build import BUILD, build, prepare
from .cover import build_wrap
from .loader import (
    BOOKS,
    I18N,
    book_languages,
    chapter_front_matter,
    content_path,
    list_books,
    load_book,
    load_config,
    source_hash,
    split_translation,
)
from .preview import generate_preview
from .theme import COLLECTION, load_theme
from .validate import validate_ast


def cmd_list(args: argparse.Namespace) -> int:
    for slug in list_books():
        b = load_book(slug)
        vol = f"vol. {b.meta.volume}" if b.meta.volume else "—"
        print(f"  {slug:<26} {b.meta.language:<6} {vol:<8} {b.meta.accent:<7} "
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
        print(f"  prévia  {slug}: {len(generated)} imagens leves")
    return 0


# Campos do book.yaml que uma tradução precisa trazer no próprio idioma.
TRANSLATABLE = ("title", "subtitle", "edition", "description", "keywords",
                "cover_bullets", "volume_label")


def cmd_i18n(args: argparse.Namespace) -> int:
    """Traduções: o português é a fonte; cada idioma acompanha o original."""
    base, lang = split_translation(args.slug)
    if args.new:
        return _i18n_new(base, args.new)
    if args.stamp:
        if not lang:
            print("  --stamp pede o slug da tradução, ex.: php-one-v1-en",
                  file=sys.stderr)
            return 1
        return _i18n_stamp(base, lang, args.chapters)

    bases = [base] if args.slug not in ("all", "*") else list_books(translations=False)
    for b in bases:
        cfg = load_config(b)
        names = [str(n) for n in cfg.get("chapters", []) or []]
        if cfg.get("preview_source"):
            langs = book_languages(b)
            print(f"\n{b}: prévia — {', '.join(langs) or 'só pt-BR'} "
                  "(capítulos vêm do volume fonte)")
            continue
        for code in ([lang] if lang else book_languages(b)):
            ok, old, todo = [], [], []
            for name in names:
                path, original = content_path(f"{b}-{code}", name)
                if path == original:
                    todo.append(name)
                elif chapter_front_matter(path).get("source_hash") == source_hash(original):
                    ok.append(name)
                else:
                    old.append(name)
            tr = yaml.safe_load((BOOKS / b / I18N / code / "book.yaml")
                                .read_text(encoding="utf-8")) or {}
            gaps = [k for k in TRANSLATABLE if k in (yaml.safe_load(
                (BOOKS / b / "book.yaml").read_text(encoding="utf-8")) or {})
                and k not in tr]
            print(f"\n{b}-{code}: {len(ok)}/{len(names)} em dia, "
                  f"{len(old)} desatualizados, {len(todo)} sem tradução")
            for name in old:
                print(f"  desatualizado  {name}")
            for name in todo:
                print(f"  falta          {name}")
            for key in gaps:
                print(f"  book.yaml      falta traduzir '{key}'")
        if not lang and not book_languages(b):
            print(f"\n{b}: só pt-BR")
    return 0


def _i18n_new(base: str, code: str) -> int:
    dest = BOOKS / base / I18N / code
    if (dest / "book.yaml").exists():
        print(f"já existe: {dest}", file=sys.stderr)
        return 1
    cfg = yaml.safe_load((BOOKS / base / "book.yaml").read_text(encoding="utf-8")) or {}
    out = {"language": code}
    out.update({k: cfg[k] for k in TRANSLATABLE if k in cfg})
    if cfg.get("parts"):
        out["parts"] = [{"id": p["id"], "title": p.get("title", ""),
                         "blurb": p.get("blurb", "")} for p in cfg["parts"]]
    (dest / "content").mkdir(parents=True)
    head = (f"# {base} — tradução ({code}).\n"
            "# Fonte oficial: ../../book.yaml, em português. Aqui entram só os\n"
            "# campos traduzidos; o resto (capítulos, cor, volume) é herdado.\n")
    (dest / "book.yaml").write_text(
        head + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=78),
        encoding="utf-8")
    print(f"criado: {dest}  — traduza book.yaml e escreva content/*.md")
    return 0


def _i18n_stamp(base: str, code: str, only: list[str]) -> int:
    """Grava `source_hash` do original em cada capítulo traduzido."""
    slug = f"{base}-{code}"
    for name in [str(n) for n in load_config(slug).get("chapters", []) or []]:
        if only and not any(name.startswith(o) for o in only):
            continue
        path, original = content_path(slug, name)
        if path == original:
            continue
        text = path.read_text(encoding="utf-8")
        mark = f"source_hash: {source_hash(original)}"
        if re.search(r"^source_hash:.*$", text, flags=re.M):
            text = re.sub(r"^source_hash:.*$", mark, text, count=1, flags=re.M)
        else:
            text = text.replace("---\n", f"---\n{mark}\n", 1)
        path.write_text(text, encoding="utf-8")
        print(f"  em dia  {name}")
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

    tr = sub.add_parser("i18n", help="situação das traduções (português é a fonte)")
    tr.add_argument("slug", help="volume (php-one-v1), tradução (php-one-v1-en) ou all")
    tr.add_argument("--new", metavar="IDIOMA", help="abre books/<slug>/i18n/<idioma>/")
    tr.add_argument("--stamp", action="store_true",
                    help="marca os capítulos traduzidos como em dia com o original")
    tr.add_argument("chapters", nargs="*", help="com --stamp: só estes (prefixo, ex.: 08)")
    tr.set_defaults(fn=cmd_i18n)

    pv = sub.add_parser("preview", help="gera os assets leves de uma prévia")
    pv.add_argument("slug")
    pv.set_defaults(fn=cmd_preview)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
