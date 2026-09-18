"""Lista as linhas de código que estouram a mancha (uso durante a escrita)."""
import sys
from pathlib import Path

LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 62
for f in sorted(Path(sys.argv[1]).glob("*.md")):
    inside = False
    for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        # blocos de código dentro de :::anatomy e :::compare também contam
        if inside and len(line) > LIMIT:
            print(f"{f.name}:{n} ({len(line)}) {line}")
