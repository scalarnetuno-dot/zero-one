#!/usr/bin/env python3
"""
Baixa as fontes da coleção (todas OFL — livres para incorporar em PDF comercial).

    python collection/theme/fonts/_fetch.py

Rodar uma vez por máquina. As fontes não vão para o git (ver .gitignore):
são grandes e sempre recuperáveis por este script.

Famílias:
    IBM Plex Serif  → corpo do texto
    IBM Plex Sans   → títulos, rótulos, números
    IBM Plex Mono   → código

Só arquivos ESTÁTICOS: o Typst lê apenas a instância padrão de fontes
variáveis, e a coleção precisa de Light/Medium/SemiBold/Bold de verdade.
"""
from __future__ import annotations

import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"
PLEX = "https://raw.githubusercontent.com/IBM/plex/master/packages"

SERIF_STYLES = ("Light", "LightItalic", "Regular", "Italic", "Medium", "MediumItalic",
                "SemiBold", "SemiBoldItalic", "Bold", "BoldItalic")
# Os estáticos do Sans registram Medium/SemiBold como FAMÍLIAS separadas
# ("IBM Plex Sans Medm"), o que confunde o Typst. A coleção usa 300/400/700.
SANS_STYLES = ("Light", "LightItalic", "Regular", "Italic", "Bold", "BoldItalic")
MONO_STYLES = ("Regular", "Italic", "Medium", "SemiBold", "Bold")

SOURCES: list[tuple[str, str]] = []
SOURCES += [(f"{GF}/ibmplexserif/IBMPlexSerif-{s}.ttf", f"IBMPlexSerif-{s}.ttf")
            for s in SERIF_STYLES]
SOURCES += [(f"{PLEX}/plex-sans/fonts/complete/ttf/IBMPlexSans-{s}.ttf",
             f"IBMPlexSans-{s}.ttf") for s in SANS_STYLES]
SOURCES += [(f"{GF}/ibmplexmono/IBMPlexMono-{s}.ttf", f"IBMPlexMono-{s}.ttf")
            for s in MONO_STYLES]

LICENSES = [
    (f"{GF}/ibmplexserif/OFL.txt", "licenses/IBMPlex-OFL.txt"),
]

# lixo de versões anteriores do script
STALE = ("IBMPlexSans[wdth,wght].ttf", "IBMPlexSans-Italic[wdth,wght].ttf",
         "IBMPlexSans-Medium.ttf", "IBMPlexSans-MediumItalic.ttf",
         "IBMPlexSans-SemiBold.ttf", "IBMPlexSans-SemiBoldItalic.ttf")


def fetch(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return False
    with urllib.request.urlopen(urllib.parse.quote(url, safe=":/[]"), timeout=60) as r:
        data = r.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


def main() -> int:
    for name in STALE:
        (HERE / name).unlink(missing_ok=True)

    new = 0
    for url, name in SOURCES:
        dest = HERE / name
        try:
            if fetch(url, dest):
                new += 1
                print(f"  baixado  {name}  ({dest.stat().st_size // 1024} KB)")
        except Exception as exc:
            print(f"  FALHOU   {name}: {exc}", file=sys.stderr)
            return 1
    for url, name in LICENSES:
        try:
            fetch(url, HERE / name)
        except Exception:
            pass

    total = len(list(HERE.glob("*.ttf")))
    print(f"fontes: {total} arquivos em {HERE}  ({new} novos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
