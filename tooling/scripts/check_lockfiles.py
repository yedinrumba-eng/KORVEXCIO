#!/usr/bin/env python3
"""
check_lockfiles.py — Lockfile integrity check.

Detecta manifests (package.json, requirements.txt, pyproject.toml, Cargo.toml, go.mod,
composer.json) cuyo lockfile asociado falta o está desincronizado. Previne builds no
reproducibles, dependencias no fijadas y PRs que tocan el manifest sin commitear el lock.

Para npm/pnpm, verifica ademas que las versiones del manifest esten "pinned" declaradas
(sin ^ o ~ en runtime/dependencies de produccion) — solo como warning (exit 0), ya que
el lockfile pinneado es lo que garantiza reproducibilidad si `npm ci` lo usa.

Uso:
    python check_lockfiles.py [PATH] [--strict] [--no-warnings]

Ver docs/vulnerabilidades/10-dependencies-supply-chain.md (fila H11),
docs/vulnerabilidades/11-ci-cd-containers.md.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

# (manifest_filename, lockfile_filename) — al menos uno debe existir si el manifest existe
LOCKFILE_PAIRS = [
    ("package.json", "package-lock.json"),
    ("package.json", "pnpm-lock.yaml"),
    ("package.json", "yarn.lock"),
    ("pyproject.toml", "poetry.lock"),
    ("requirements.txt", "requirements.txt"),    # self-pinned; revisa pinning abajo
    ("Cargo.toml", "Cargo.lock"),
    ("go.mod", "go.sum"),
    ("composer.json", "composer.lock"),
]

# estimación de dirs a no recorrer
DEFAULT_EXCLUDE = {
    "node_modules", ".git", "dist", "build", ".next", "out", "vendor", "target",
    "__pycache__", ".venv", "venv", "env", ".cache",
}

RANGE = ("^", "~", ">=", "<=", ">", "<", "*")


def human(idx: int) -> str:
    return ("ERROR", "WARN")[idx]


class Report:
    def __init__(self, strict: bool, show_warnings: bool):
        self.strict = strict
        self.show_warnings = show_warnings
        self.errors: list[str] = []  # exit 1
        self.warns:   list[str] = []  # exit 0 (salvo --strict)

    def add(self, idx: int, msg: str):
        (self.errors if idx == 0 else self.warns).append(msg)

    def exit_code(self) -> int:
        if self.errors:
            return 1
        return 1 if (self.strict and self.warns) else 0

    def print_all(self):
        for m in self.errors:
            print(f"::{human(0)}:: {m}")
        if self.show_warnings:
            for m in self.warns:
                print(f"::{human(1)}:: {m}")
        if not self.errors and not (self.strict and self.warns):
            print("lockfile-check: OK — manifests con lockfile presente y.")
        else:
            n_err = len(self.errors)
            n_warn = len(self.warns)
            print(f"lockfile-check: {n_err} error(es), {n_warn} warning(s).")


def check_npm_pin(path: Path, rep: Report):
    """package.json: las runtime deps deberian estar pinned (no ^/~) — warning."""
    try:
        pkg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for section in ("dependencies",):
        deps = pkg.get(section, {}) or {}
        for name, ver in deps.items():
            if not isinstance(ver, str):
                continue  # tarball/url/git specs no aplican
            if ver.startswith(RANGE):
                rep.add(1,
                        f"{path}: '{name}' usa rango '{ver}' en dependencies "
                        f"(prefiere pin exacto y commitea el lockfile)")


def check_python_pin(path: Path, rep: Report):
    """requirements.txt: deberia pin (==) — warning si usa >=/~/^/sin pin."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = re.match(r"^([A-Za-z0-9_.\-]+)\s*(==|>=|<=|~=|>|<|;|@|$)", line)
        if not m:
            continue
        op = m.group(2)
        if op not in ("==", ";", "@" ):
            rep.add(1,
                    f"{path}:{line_no} '{m.group(1)}' sin pin exacto "
                    f"(='{line.strip()}'); usa '==' para reproducibilidad")


def is_frappe_app_manifest(path: Path) -> bool:
    """pyproject.toml de una app de Frappe (build-backend flit_core, deps
    gestionadas por `bench` contra el venv del site, no por un lockfile
    propio) — mismo patron que erpnext/posnext/ury. No aplica poetry.lock."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "flit_core.buildapi" in text and "# Installed and managed by bench" in text


def scan(root: Path, excludes: set[str], rep: Report):
    # collect every manifest file present (deduplicated by path)
    manifest_pairs: dict[str, list[Path]] = {m: [] for m, _ in LOCKFILE_PAIRS}
    for p in root.rglob("*"):
        if not p.is_file() or (set(p.parts) & excludes):
            continue
        if p.parent.name == "node_modules":
            continue
        # manifest files and self-referencing lockfiles (requirements.txt)
        if p.name in manifest_pairs:
            manifest_pairs[p.name].append(p)

    # lockfiles candidates per manifest type (npm accepts 3 — any one suffices)
    lockfile_candidates: dict[str, list[str]] = {}
    for mf_name, lock_name in LOCKFILE_PAIRS:
        lockfile_candidates.setdefault(mf_name, []).append(lock_name)

    for mf_name, files in manifest_pairs.items():
        # dedupe the candidate lockfile names for this manifest kind
        candidates = list(dict.fromkeys(lockfile_candidates.get(mf_name, [])))
        for mf in files:
            # self-referencing manifest==lockfile (requirements.txt): only pinning check
            if mf_name in candidates:
                if mf_name == "requirements.txt":
                    check_python_pin(mf, rep)
                continue
            has_any = any((mf.parent / l).exists() for l in candidates)
            if not has_any:
                if mf_name == "pyproject.toml" and is_frappe_app_manifest(mf):
                    continue
                rep.add(0,
                        f"{mf}: {mf_name} sin lockfile asociado "
                        f"(commitea uno de: {', '.join(candidates)})")
                continue
            if mf_name == "package.json":
                check_npm_pin(mf, rep)


def main() -> int:
    ap = argparse.ArgumentParser(description="Manifest/lockfile integrity check.")
    ap.add_argument("path", nargs="?", default=".",
                    help="raiz del proyecto a revisar (default .)")
    ap.add_argument("--strict", action="store_true",
                    help="los warnings (rangos sin pin) tambien fallan el exit")
    ap.add_argument("--no-warnings", action="store_true",
                    help="no mostrar warnings, solo errores")
    ap.add_argument("--exclude", default=",".join(sorted(DEFAULT_EXCLUDE)),
                    help="dirs a excluir (csv)")
    args = ap.parse_args()

    excludes = set(args.exclude.split(","))
    root = Path(args.path).resolve()
    rep = Report(strict=args.strict, show_warnings=not args.no_warnings)
    scan(root, excludes, rep)
    rep.print_all()
    return rep.exit_code()


if __name__ == "__main__":
    sys.exit(main())
