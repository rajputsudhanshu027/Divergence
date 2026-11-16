"""Compile or execute code cells without requiring Jupyter as a project dependency."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def validate(path: Path, execute: bool) -> None:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    namespace = {"__name__": "__notebook__"}
    previous = Path.cwd()
    try:
        os.chdir(path.parent)
        for index, cell in enumerate(notebook.get("cells", []), start=1):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            code = compile(source, f"{path.name}:cell-{index}", "exec")
            if execute:
                exec(code, namespace)
    finally:
        os.chdir(previous)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebooks", nargs="+", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    for notebook in args.notebooks:
        validate(notebook.resolve(), args.execute)
        print(f"{'executed' if args.execute else 'compiled'}: {notebook}")


if __name__ == "__main__":
    main()
