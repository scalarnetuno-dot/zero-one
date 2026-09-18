"""
diagrams.py — dados estruturados → geometria de diagrama.

O autor descreve o QUE o diagrama diz; aqui se decide ONDE cada coisa fica.
O resultado é geometria pura (mm, origem no canto superior esquerdo), que
o renderizador de PDF desenha com primitivas do Typst e o de EPUB desenha
em SVG. Mesma conta, dois traços — nenhum diagrama é editado à mão.

Tipos: flowchart · sequence · cells (array/pilha/fila) · blocks (arquitetura)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .theme import Theme, _mm

Point = tuple[float, float]


@dataclass
class Shape:
    kind: Literal["rect", "stadium", "diamond", "parallelogram", "line", "text", "cell"]
    x: float
    y: float
    w: float = 0.0
    h: float = 0.0
    text: str = ""
    sub: str = ""                 # segunda linha menor (índice, nota)
    fill: str = ""
    stroke: str = ""
    dashed: bool = False
    bold: bool = False
    align: str = "center"


@dataclass
class Edge:
    points: list[Point]
    label: str = ""
    arrow: bool = True
    dashed: bool = False
    label_at: Point | None = None


@dataclass
class DiagramLayout:
    width: float
    height: float
    shapes: list[Shape] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    font_size: float = 8.2
    label_size: float = 7.4


class DiagramError(Exception):
    pass


# ─── helpers ─────────────────────────────────────────────────────────────────

def _wrap(text: str, width_mm: float, size_pt: float, max_lines: int = 3) -> list[str]:
    """Quebra grosseira por largura média de caractere. Suficiente para caixas."""
    char_mm = size_pt * 0.3528 * 0.53
    per_line = max(6, int((width_mm - 3) / char_mm))
    words, lines, cur = text.split(), [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if len(cand) <= per_line or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return lines or [""]


def _text_h(lines: int, size_pt: float) -> float:
    return lines * size_pt * 0.3528 * 1.25


# ─── flowchart ───────────────────────────────────────────────────────────────

_SHAPE_BY_TYPE = {
    "start": "stadium", "end": "stadium", "terminator": "stadium",
    "decision": "diamond", "io": "parallelogram",
    "process": "rect", "": "rect",
}


def _flowchart(spec: dict[str, Any], theme: Theme) -> DiagramLayout:
    nodes = spec.get("nodes") or []
    edges_in = spec.get("edges") or []
    if not nodes:
        raise DiagramError("flowchart sem 'nodes'")

    nw = _mm(theme.t("diagram.node.width"))
    nh = _mm(theme.t("diagram.node.height"))
    gx = _mm(theme.t("diagram.node.gap_x"))
    gy = _mm(theme.t("diagram.node.gap_y"))
    fs = float(str(theme.t("diagram.font_size")).rstrip("pt"))

    ids = [str(n["id"]) for n in nodes]
    by_id = {str(n["id"]): n for n in nodes}
    outs: dict[str, list[dict]] = {i: [] for i in ids}
    for e in edges_in:
        a, b = str(e["from"]), str(e["to"])
        if a not in by_id or b not in by_id:
            raise DiagramError(f"aresta {a}→{b} aponta para nó inexistente")
        outs[a].append(e)

    # rank = profundidade em ordem de declaração (arestas para trás viram laço)
    rank: dict[str, int] = {ids[0]: 0}
    for i in ids:
        for e in outs.get(i, []):
            t = str(e["to"])
            if t not in rank or rank[t] <= rank.get(i, 0):
                if t not in rank or rank[t] < rank.get(i, 0) + 1:
                    if _is_back(i, t, ids):
                        continue
                    rank[t] = rank.get(i, 0) + 1
    for i in ids:
        rank.setdefault(i, 0)

    rows: dict[int, list[str]] = {}
    for i in ids:
        rows.setdefault(rank[i], []).append(i)

    widest = max(len(r) for r in rows.values())
    lane = 7.0 if any(_is_back(str(e["from"]), str(e["to"]), ids) for e in edges_in) else 0.0
    canvas_w = widest * nw + (widest - 1) * gx + lane

    geo: dict[str, tuple[float, float, float, float]] = {}
    shapes: list[Shape] = []
    y = 0.0
    for r in sorted(rows):
        row = rows[r]
        row_w = len(row) * nw + (len(row) - 1) * gx
        x = (canvas_w - lane - row_w) / 2
        row_h = nh
        for nid in row:
            n = by_id[nid]
            kind = _SHAPE_BY_TYPE.get(str(n.get("type", "process")).lower(), "rect")
            lines = _wrap(str(n.get("text", nid)), nw, fs)
            h = max(nh, _text_h(len(lines), fs) + 5)
            if kind == "diamond":
                h = max(h, nh + 3)
            geo[nid] = (x, y, nw, h)
            row_h = max(row_h, h)
            shapes.append(Shape(
                kind=kind, x=x, y=y, w=nw, h=h, text="\n".join(lines),
                fill=theme.t("diagram.fill"),
                stroke=theme.resolve_color("accent") if kind == "stadium"
                else theme.t("color.rule_strong"),
                bold=kind == "stadium",
            ))
            x += nw + gx
        y += row_h + gy

    height = max(y - gy, nh)

    edges: list[Edge] = []
    for e in edges_in:
        a, b = str(e["from"]), str(e["to"])
        ax, ay, aw, ah = geo[a]
        bx, by, bw, bh = geo[b]
        label = str(e.get("label", ""))
        if _is_back(a, b, ids) or rank[b] <= rank[a]:
            # laço: sai pela direita, sobe pela faixa lateral, entra pela direita
            lane_x = canvas_w - lane / 2
            pts = [(ax + aw, ay + ah / 2), (lane_x, ay + ah / 2),
                   (lane_x, by + bh / 2), (bx + bw, by + bh / 2)]
            edges.append(Edge(points=pts, label=label,
                              label_at=(lane_x, (ay + by) / 2)))
            continue
        start = (ax + aw / 2, ay + ah)
        end = (bx + bw / 2, by)
        if abs(start[0] - end[0]) < 0.6:
            pts = [start, end]
            lbl = (start[0] + 1.5, (start[1] + end[1]) / 2)
        else:
            mid = (start[1] + end[1]) / 2
            pts = [start, (start[0], mid), (end[0], mid), end]
            lbl = (start[0] + (2 if end[0] > start[0] else -2), start[1] + 2.5)
        edges.append(Edge(points=pts, label=label, label_at=lbl))

    return DiagramLayout(width=canvas_w, height=height, shapes=shapes, edges=edges,
                         font_size=fs,
                         label_size=float(str(theme.t("diagram.label_size")).rstrip("pt")))


def _is_back(a: str, b: str, order: list[str]) -> bool:
    return order.index(b) <= order.index(a)


# ─── sequence ────────────────────────────────────────────────────────────────

def _sequence(spec: dict[str, Any], theme: Theme) -> DiagramLayout:
    actors = spec.get("actors") or []
    msgs = spec.get("messages") or []
    if not actors:
        raise DiagramError("sequence sem 'actors'")

    fs = float(str(theme.t("diagram.font_size")).rstrip("pt"))
    lbl = float(str(theme.t("diagram.label_size")).rstrip("pt"))
    bw = _mm(theme.t("diagram.small_node.width"))
    bh = _mm(theme.t("diagram.small_node.height"))
    gap = 12.0
    step = 11.0

    shapes: list[Shape] = []
    xs: dict[str, float] = {}
    x = 0.0
    for a in actors:
        name = a if isinstance(a, str) else str(a.get("name", a.get("id", "")))
        aid = name if isinstance(a, str) else str(a.get("id", name))
        shapes.append(Shape(kind="rect", x=x, y=0, w=bw, h=bh,
                            text="\n".join(_wrap(name, bw, lbl, 2)),
                            fill=theme.t("diagram.fill_alt"),
                            stroke=theme.t("color.rule_strong")))
        xs[aid] = x + bw / 2
        x += bw + gap

    height = bh + step * (len(msgs) + 1)
    for cx in xs.values():
        shapes.append(Shape(kind="line", x=cx, y=bh, w=0, h=height - bh,
                            stroke=theme.t("color.rule"), dashed=True))

    edges: list[Edge] = []
    y = bh + step
    for m in msgs:
        a, b = str(m["from"]), str(m["to"])
        if a not in xs or b not in xs:
            raise DiagramError(f"mensagem {a}→{b} usa ator inexistente")
        edges.append(Edge(points=[(xs[a], y), (xs[b], y)],
                          label=str(m.get("text", "")),
                          dashed=bool(m.get("dashed", m.get("kind") == "return")),
                          label_at=((xs[a] + xs[b]) / 2, y - 1.2)))
        y += step

    return DiagramLayout(width=x - gap, height=height, shapes=shapes, edges=edges,
                         font_size=fs, label_size=lbl)


# ─── cells (array, pilha, fila) ──────────────────────────────────────────────

def _cells(spec: dict[str, Any], theme: Theme) -> DiagramLayout:
    items = [str(i) for i in (spec.get("items") or [])]
    if not items:
        raise DiagramError("cells sem 'items'")
    vertical = str(spec.get("orientation", "horizontal")) == "vertical"
    index_from = spec.get("index")
    fs = float(str(theme.t("diagram.font_size")).rstrip("pt"))
    lbl = float(str(theme.t("diagram.label_size")).rstrip("pt"))
    cw = _mm(theme.t("diagram.small_node.width")) * 0.72
    ch = _mm(theme.t("diagram.small_node.height"))

    shapes: list[Shape] = []
    for k, item in enumerate(items):
        x = 0 if vertical else k * cw
        y = k * ch if vertical else 0
        sub = "" if index_from is None else str(int(index_from) + k)
        shapes.append(Shape(kind="cell", x=x, y=y, w=cw, h=ch, text=item, sub=sub,
                            fill=theme.t("diagram.fill"),
                            stroke=theme.t("color.rule_strong")))

    base_w = cw if vertical else cw * len(items)
    base_h = ch * len(items) if vertical else ch
    w, h = base_w, base_h

    edges: list[Edge] = []
    for note in spec.get("notes") or []:
        at = int(note.get("at", 0))
        text = str(note.get("text", ""))
        span = len(text) * lbl * 0.3528 * 0.52
        if vertical:
            y = at * ch + ch / 2
            edges.append(Edge(points=[(base_w + 6, y), (base_w + 0.8, y)],
                              label=text, label_at=(base_w + 7 + span / 2, y)))
            w = max(w, base_w + 8 + span)
        else:
            x = at * cw + cw / 2
            edges.append(Edge(points=[(x, base_h + 6), (x, base_h + 0.8)],
                              label=text, label_at=(x, base_h + 9)))
            h = max(h, base_h + 10)
            w = max(w, x + span / 2 + 1)

    return DiagramLayout(width=w, height=h, shapes=shapes, edges=edges,
                         font_size=fs, label_size=lbl)


# ─── blocks (arquitetura / camadas) ──────────────────────────────────────────

def _blocks(spec: dict[str, Any], theme: Theme) -> DiagramLayout:
    rows = spec.get("rows") or []
    if not rows:
        raise DiagramError("blocks sem 'rows'")
    nw = _mm(theme.t("diagram.node.width"))
    nh = _mm(theme.t("diagram.node.height"))
    gx = _mm(theme.t("diagram.node.gap_x")) * 0.6
    gy = _mm(theme.t("diagram.node.gap_y")) * 0.7
    fs = float(str(theme.t("diagram.font_size")).rstrip("pt"))
    lbl = float(str(theme.t("diagram.label_size")).rstrip("pt"))

    widest = max(len(r) for r in rows)
    canvas_w = widest * nw + (widest - 1) * gx
    shapes: list[Shape] = []
    centers: list[list[Point]] = []
    y = 0.0
    for r_i, row in enumerate(rows):
        cells = [c if isinstance(c, dict) else {"text": str(c)} for c in row]
        w_each = (canvas_w - (len(cells) - 1) * gx) / len(cells)
        x = 0.0
        row_centers: list[Point] = []
        h_row = nh
        for c in cells:
            lines = _wrap(str(c.get("text", "")), w_each, fs, 2)
            note = str(c.get("note", ""))
            h = max(nh, _text_h(len(lines), fs) + (4.5 if not note else 8.5))
            h_row = max(h_row, h)
            shapes.append(Shape(
                kind="rect", x=x, y=y, w=w_each, h=h, text="\n".join(lines), sub=note,
                fill=theme.t("diagram.fill_alt") if r_i % 2 else theme.t("diagram.fill"),
                stroke=theme.t("color.rule_strong")))
            row_centers.append((x + w_each / 2, y))
            x += w_each + gx
        centers.append(row_centers)
        y += h_row + gy

    edges: list[Edge] = []
    if spec.get("flow", True) and len(centers) > 1:
        for i in range(len(centers) - 1):
            a = centers[i][len(centers[i]) // 2]
            b = centers[i + 1][len(centers[i + 1]) // 2]
            y_a = a[1] + nh
            edges.append(Edge(points=[(a[0], y_a), (b[0], b[1])]))

    return DiagramLayout(width=canvas_w, height=max(y - gy, nh), shapes=shapes,
                         edges=edges, font_size=fs, label_size=lbl)



# ─── timeline (história) ─────────────────────────────────────────────────────

def _timeline(spec: dict[str, Any], theme: Theme) -> DiagramLayout:
    events = spec.get("events") or []
    if not events:
        raise DiagramError("timeline sem 'events'")
    fs = float(str(theme.t("diagram.font_size")).rstrip("pt"))
    lbl = float(str(theme.t("diagram.label_size")).rstrip("pt"))
    accent = theme.resolve_color("accent")
    soft = theme.t("color.ink_soft")

    step = 11.0          # altura de cada evento
    axis_x = 17.0        # onde corre a linha do tempo
    width = float(spec.get("width", 110))
    height = step * len(events) + 4

    shapes: list[Shape] = []
    edges: list[Edge] = [Edge(points=[(axis_x, 1.0), (axis_x, height - 3)],
                              arrow=False)]
    for i, ev in enumerate(events):
        y = 4.0 + i * step
        year = str(ev.get("year", ""))
        text = str(ev.get("text", ""))
        mark = bool(ev.get("mark", False))
        shapes.append(Shape(kind="text", x=0, y=y - 2.0, w=axis_x - 4, h=4,
                            text=year, align="right", bold=True,
                            fill=accent if mark else soft))
        shapes.append(Shape(kind="cell", x=axis_x - 1.2, y=y - 1.2, w=2.4, h=2.4,
                            fill=accent if mark else "#FFFFFF", stroke=accent))
        lines = _wrap(text, width - axis_x - 5, fs, 2)
        shapes.append(Shape(kind="text", x=axis_x + 4, y=y - 2.2,
                            w=width - axis_x - 4, h=5, text="\n".join(lines),
                            align="left"))
    return DiagramLayout(width=width, height=height, shapes=shapes, edges=edges,
                         font_size=fs, label_size=lbl)


# ─── entidade-relacionamento ─────────────────────────────────────────────────

def _er(spec: dict[str, Any], theme: Theme) -> DiagramLayout:
    entities = spec.get("entities") or []
    if not entities:
        raise DiagramError("er sem 'entities'")
    fs = float(str(theme.t("diagram.font_size")).rstrip("pt"))
    lbl = float(str(theme.t("diagram.label_size")).rstrip("pt"))
    ew = _mm(theme.t("diagram.node.width")) * 0.92
    gap_x = 12.0
    gap_y = 11.0
    head_h = 6.2
    row_h = 4.4
    per_row = int(spec.get("columns", 2))

    geo: dict[str, tuple[float, float, float, float]] = {}
    shapes: list[Shape] = []
    x = y = 0.0
    row_max = 0.0
    for i, ent in enumerate(entities):
        name = str(ent.get("name", "?"))
        fields = [str(f) for f in (ent.get("fields") or [])]
        h = head_h + row_h * len(fields) + 1.5
        col = i % per_row
        if col == 0 and i:
            y += row_max + gap_y
            row_max = 0.0
        x = col * (ew + gap_x)
        geo[name] = (x, y, ew, h)
        row_max = max(row_max, h)
        # ordem de desenho: moldura, faixa do título, textos
        shapes.append(Shape(kind="rect", x=x, y=y, w=ew, h=h,
                            fill=theme.t("diagram.fill"),
                            stroke=theme.t("color.rule_strong")))
        shapes.append(Shape(kind="rect", x=x, y=y, w=ew, h=head_h,
                            fill=theme.resolve_color("accent"),
                            stroke=theme.resolve_color("accent")))
        shapes.append(Shape(kind="text", x=x, y=y, w=ew, h=head_h, text=name,
                            align="center", bold=True, fill="#FFFFFF"))
        for k, f in enumerate(fields):
            shapes.append(Shape(kind="text", x=x + 2.2,
                                y=y + head_h + k * row_h,
                                w=ew - 4.4, h=row_h, text=f, align="left"))
    height = y + row_max

    edges: list[Edge] = []
    for rel in spec.get("relations") or []:
        a, b = str(rel["from"]), str(rel["to"])
        if a not in geo or b not in geo:
            raise DiagramError(f"relação {a}→{b} usa entidade inexistente")
        ax, ay, aw, ah = geo[a]
        bx, by, bw, bh = geo[b]
        label = str(rel.get("label", rel.get("kind", "")))
        if abs(ay - by) < 0.5:              # mesma linha: liga pelas laterais
            start = (ax + aw, ay + ah / 2) if ax < bx else (ax, ay + ah / 2)
            end = (bx, by + bh / 2) if ax < bx else (bx + bw, by + bh / 2)
            mid = ((start[0] + end[0]) / 2, start[1] - 1.5)
        else:                                # linhas diferentes: por baixo
            start = (ax + aw / 2, ay + ah)
            end = (bx + bw / 2, by)
            mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        edges.append(Edge(points=[start, end], label=label, label_at=mid))

    return DiagramLayout(width=per_row * ew + (per_row - 1) * gap_x,
                         height=height, shapes=shapes, edges=edges,
                         font_size=fs, label_size=lbl)


BUILDERS = {
    "flowchart": _flowchart,
    "sequence": _sequence,
    "cells": _cells,
    "array": _cells,
    "stack": _cells,
    "blocks": _blocks,
    "architecture": _blocks,
    "layers": _blocks,
    "timeline": _timeline,
    "er": _er,
    "model": _er,
}


def build(kind: str, spec: dict[str, Any], theme: Theme) -> DiagramLayout:
    fn = BUILDERS.get(kind.lower())
    if fn is None:
        raise DiagramError(
            f"diagrama '{kind}' não existe. Disponíveis: {', '.join(sorted(BUILDERS))}")
    return fn(spec, theme)
