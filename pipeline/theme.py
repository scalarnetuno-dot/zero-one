"""
theme.py — tokens.yaml + collection.yaml + a cor do volume → estilo concreto.

É o único lugar que lê o design system. Os renderizadores recebem um Theme
e nunca abrem YAML nem inventam medida.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent.parent
COLLECTION = ROOT / "collection"
THEME_DIR = COLLECTION / "theme"
TEMPLATES = THEME_DIR / "templates"
FONTS = THEME_DIR / "fonts"


@dataclass
class Theme:
    tokens: dict[str, Any]
    collection: dict[str, Any]
    accent: str = "red"
    accent_hex: str = "#B32B23"
    language: str = "pt-BR"
    env: Environment = field(init=False)

    def __post_init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES)),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["hex"] = lambda c: self.resolve_color(c)

    # ─── acesso aos tokens ───────────────────────────────────────────────
    def t(self, path: str, default: Any = None) -> Any:
        """theme.t('type.scale.h2') → 15pt (como string, do jeito do Typst)."""
        node: Any = self.tokens
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def resolve_color(self, value: str) -> str:
        """'accent' → hex do volume; '#abc' → ele mesmo; 'color.ink' → token."""
        if not isinstance(value, str):
            return str(value)
        if value == "accent":
            return self.accent_hex
        if value.startswith("#"):
            return value
        found = self.t(value if "." in value else f"color.{value}")
        return found if isinstance(found, str) else value

    def strings(self) -> dict[str, str]:
        """Tabela de rótulos do idioma do livro — nenhuma chave faltando."""
        strings = self.collection.get("strings", {})
        table = (strings.get(self.language)
                 or strings.get(self.language.split("-")[0])
                 or strings.get("pt-BR", {}))
        return {str(k): str(v) for k, v in table.items()}

    def s(self, key: str) -> str:
        """Rótulo do sistema no idioma do livro."""
        return self.strings().get(key, key)

    # ─── saídas ──────────────────────────────────────────────────────────
    def render(self, template: str, **ctx: Any) -> str:
        return self.env.get_template(template).render(theme=self, tk=self.tokens,
                                                      accent=self.accent_hex, **ctx)

    def tm_theme(self) -> str:
        """Tema TextMate para o realce de sintaxe nativo do Typst."""
        p = self.t("code.palette", {})
        scopes = [
            ("Comment", "comment", p["comment"], "italic"),
            ("String", "string, constant.character", p["string"], ""),
            ("Number", "constant.numeric, constant.language", p["number"], ""),
            ("Keyword", "keyword, storage.modifier, keyword.control", p["keyword"], ""),
            ("Storage type", "storage.type", p["keyword"], ""),
            ("Type", "entity.name.type, entity.name.class, support.type, support.class",
             p["type"], ""),
            ("Function", "entity.name.function, support.function", p["function"], ""),
            ("Builtin", "variable.language, support.constant", p["builtin"], ""),
            ("Operator", "keyword.operator, punctuation", p["operator"], ""),
            ("Meta", "meta.annotation, entity.other.attribute-name", p["meta"], ""),
            ("Tag", "entity.name.tag", p["keyword"], ""),
        ]
        items = []
        for name, scope, color, style in scopes:
            extra = f"\n\t\t\t\t<key>fontStyle</key>\n\t\t\t\t<string>{style}</string>" if style else ""
            items.append(
                f"\t\t<dict>\n\t\t\t<key>name</key>\n\t\t\t<string>{name}</string>\n"
                f"\t\t\t<key>scope</key>\n\t\t\t<string>{scope}</string>\n"
                f"\t\t\t<key>settings</key>\n\t\t\t<dict>\n"
                f"\t\t\t\t<key>foreground</key>\n\t\t\t\t<string>{color}</string>{extra}\n"
                f"\t\t\t</dict>\n\t\t</dict>"
            )
        base = (
            f"\t\t<dict>\n\t\t\t<key>settings</key>\n\t\t\t<dict>\n"
            f"\t\t\t\t<key>background</key>\n\t\t\t\t<string>{self.t('code.background')}</string>\n"
            f"\t\t\t\t<key>foreground</key>\n\t\t\t\t<string>{p['text']}</string>\n"
            f"\t\t\t</dict>\n\t\t</dict>"
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n<dict>\n'
            "\t<key>name</key>\n\t<string>Zero One Editorial</string>\n"
            "\t<key>settings</key>\n\t<array>\n"
            + base + "\n" + "\n".join(items) +
            "\n\t</array>\n</dict>\n</plist>\n"
        )

    # ─── medidas derivadas ───────────────────────────────────────────────
    def gutter_extra(self, pages: int) -> str:
        for step in self.t("page.gutter_steps", []):
            if pages <= int(step["max_pages"]):
                return str(step["add"])
        return "0mm"

    def text_width_mm(self, pages: int = 0) -> float:
        w = _mm(self.t("page.trim.width"))
        inside = _mm(self.t("page.margin.inside")) + _mm(self.gutter_extra(pages))
        outside = _mm(self.t("page.margin.outside"))
        return w - inside - outside

    def text_height_mm(self, pages: int = 0) -> float:
        h = _mm(self.t("page.trim.height"))
        return h - _mm(self.t("page.margin.top")) - _mm(self.t("page.margin.bottom"))


_UNIT = re.compile(r"^([\d.]+)\s*(mm|cm|in|pt)$")


def _mm(value: str | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    m = _UNIT.match(str(value).strip())
    if not m:
        return 0.0
    n, unit = float(m.group(1)), m.group(2)
    return {"mm": n, "cm": n * 10, "in": n * 25.4, "pt": n * 25.4 / 72}[unit]


def load_theme(accent: str = "red", language: str = "pt-BR",
               overrides: dict[str, Any] | None = None) -> Theme:
    tokens = yaml.safe_load((THEME_DIR / "tokens.yaml").read_text(encoding="utf-8"))
    collection = yaml.safe_load((COLLECTION / "collection.yaml").read_text(encoding="utf-8"))
    if overrides:
        _deep_update(tokens, overrides)
    accents = collection.get("accents", {})
    hexcode = accents.get(accent, accent if str(accent).startswith("#") else "#B32B23")
    tokens.setdefault("color", {})["accent"] = hexcode
    return Theme(tokens=tokens, collection=collection, accent=accent,
                 accent_hex=hexcode, language=language)


def _deep_update(base: dict, extra: dict) -> None:
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
