"""Gera o conteúdo de uma prévia a partir do volume completo."""
from __future__ import annotations

import shutil
import re
from pathlib import Path
from typing import Any

import yaml

from .loader import BOOKS, book_dir, load_config


def generate_preview(slug: str) -> list[Path]:
    """Materializa capítulos liberados e teasers para a prévia ``slug``."""
    target = book_dir(slug)
    config = load_config(slug)
    source_slug = str(config.get("preview_source", "") or "")
    if not source_slug:
        paired = BOOKS / f"{slug}-previa"
        if (paired / "book.yaml").exists():
            return generate_preview(paired.name)
        raise ValueError(f"{slug}: book.yaml precisa de preview_source")

    source = book_dir(source_slug)
    chapter_names = [str(name) for name in config.get("chapters", []) or []]
    source_config = load_config(source_slug)
    source_names = {str(name) for name in source_config.get("chapters", []) or []}
    allowed = _chapter_names(config.get("preview_chapters", []) or [], source_names)

    content = target / "content"
    content.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for name in chapter_names:
        source_file = source / "content" / name
        if not source_file.exists():
            raise FileNotFoundError(f"capítulo ausente no volume fonte: {source_file}")
        destination = content / name
        if name in allowed:
            shutil.copy2(source_file, destination)
        else:
            destination.write_text(_teaser(source_file), encoding="utf-8")
        generated.append(destination)

    return generated


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _chapter_names(values: list[Any], source_names: set[str]) -> set[str]:
    names: set[str] = set()
    for value in values:
        text = str(value)
        if text.isdigit():
            prefix = f"{int(text):02d}-"
            names.update(name for name in source_names if name.startswith(prefix))
        else:
            names.add(text)
    return names


def _teaser(source_file: Path) -> str:
    text = source_file.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"capítulo sem front matter: {source_file}")
    _, front_matter, _ = text.split("---", 2)
    metadata = _read_front_matter(front_matter)
    title = str(metadata.get("title", source_file.stem))
    number = metadata.get("number")
    part = metadata.get("part")
    lines = ["---", f'title: "{title}"']
    if number is not None:
        lines.append(f"number: {number}")
    if part:
        lines.append(f"part: {part}")
    lines += ["---", "", "Este capítulo faz parte da edição completa de Java One.", "", "A prévia apresenta o sumário completo para mostrar o caminho do livro. O conteúdo integral deste capítulo está disponível na edição completa.", ""]
    for heading in _section_headings(text):
        lines += [heading, "", "Este tópico é desenvolvido na edição completa, com exemplos, código e exercícios.", ""]
    lines += [":::summary", "", "Na edição completa, este capítulo desenvolve este assunto com exemplos, código e exercícios.", "", ":::", ""]
    return "\n".join(lines)


def _section_headings(text: str) -> list[str]:
    headings: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"^#{2,3}\s+\S", line):
            headings.append(line)
    return headings


def _read_front_matter(text: str) -> dict[str, Any]:
    return yaml.safe_load(text) or {}