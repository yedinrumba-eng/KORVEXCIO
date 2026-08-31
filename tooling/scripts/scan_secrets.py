#!/usr/bin/env python3
"""
scan_secrets.py — Fase 3.2 del Secure Vibe Coding Toolkit.

Pase rápido de detección de secretos por regex (sin depender de gitleaks/trufflehog).
Úsalo en local o como fallback de CI. NO reemplaza un secret scanner con verificación
de "live keys" — es complementario.

Uso:
    python scan_secrets.py [PATH] [--exit-code 1] [--no-history]
                          [--exclude node_modules,.git,dist,build]

Referencias: docs/vulnerabilidades/01-secrets-management.md,
             skill/secure-vibe/reference/secret-regex.md (patrones fuente).
Checklist: filas C1, C10.

Notas:
- NUNCA imprime el valor completo del match — solo prefix…suffix recortado.
- Ignora .env.example y valores obviamente ficticios (PLACEHOLDER, EXAMPLE, xxx, your_key_here).
- Los patrones requieren longitud realista (ej. sk_live necesita 24+ chars tras el prefijo)
  para reducir falsos positivos; una clave truncada corta NO se detecta. Úsalo junto a
  gitleaks/trufflehog, no como unico escaner.
- No escanea el historial git por defecto; pasa --history para invocar `git log -p`.
"""

from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# --- Patrones de alta precisión (ver reference/secret-regex.md) ---
PATTERNS: dict[str, str] = {
    "aws_akid": r"AKIA[0-9A-Z]{16}",
    "aws_temp": r"ASIA[0-9A-Z]{16}",
    "github_pat": r"ghp_[A-Za-z0-9]{36}",
    "github_fine": r"github_pat_[A-Za-z0-9_]{82}",
    "github_oauth": r"gho_[A-Za-z0-9]{36}",
    "github_app_u2s": r"ghu_[A-Za-z0-9]{36}",
    "github_app_s2s": r"ghs_[A-Za-z0-9]{36}",
    "gcp_key": r"AIza[0-9A-Za-z_\-]{35}",
    "stripe_live": r"sk_live_[A-Za-z0-9]{24,}",
    "stripe_webhook": r"whsec_[A-Za-z0-9]{24,}",
    "slack": r"xox[baprs]-[0-9A-Za-z-]{10,}",
    "openai": r"sk-[A-Za-z0-9]{20,}",
    "anthropic": r"sk-ant-[A-Za-z0-9_\-]{93,}",
    "private_key": r"-----BEGIN (RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----",
    "db_url": r"(?i)(postgres(ql)?|mysql|mongodb(\+srv)?|redis)://[^:\s]+:[^@\s]+@[^\s]+",
    "jwt": r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
}

# Patrones contextuales (entropy genérica —alto falso positivo → solo como INFO)
GENERIC_SECRET = re.compile(
    r"""(?i)(password|passwd|pwd|secret|api_key|apikey|access_key|auth_token|client_secret)\s*["'\s:=]+\s*["']?[A-Za-z0-9_\-]{16,}["']?"""
)

# Valores obviamente ficticios (falsos positivos de docs/tests)
FICTIONAL = re.compile(
    r"(?i)(example|placeholder|your_key_here|xxxxxxxx|changeme|test_key|dummy|sample|sk_test_x+)"
)

DEFAULT_EXCLUDE = {
    "node_modules", ".git", "dist", "build", ".next", "out", "vendor",
    "target", "__pycache__", ".venv", "venv", "env", ".cache", "coverage",
}


def redact(value: str) -> str:
    """Nunca exponer el secret completo en el reporte."""
    if len(value) <= 12:
        return value[:2] + "…" + value[-2:]
    return value[:6] + "…" + value[-4:]


def is_fictional(line: str, value: str) -> bool:
    return bool(FICTIONAL.search(value)) or "EXAMPLE" in line.upper()


def should_skip(path: Path, excludes: set[str]) -> bool:
    parts = set(path.parts)
    return bool(parts & excludes) or path.name == ".env.example"


def scan_text(text: str, path: Path) -> list[dict]:
    findings: list[dict] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for name, pat in PATTERNS.items():
            for m in re.finditer(pat, line):
                val = m.group(0)
                if is_fictional(line, val):
                    continue
                # skip si el RHS es solo una env var (forma correcta)
                if re.search(r"process\.env\.|os\.environ|env\[", line):
                    continue
                findings.append({
                    "tipo": name, "path": str(path), "line": line_no,
                    "match": redact(val),
                })
        for m in GENERIC_SECRET.finditer(line):
            val = m.group(0).split("=")[-1].strip("'\"")
            if len(val) >= 16 and not is_fictional(line, val):
                findings.append({
                    "tipo": "generic_high_entropy", "path": str(path),
                    "line": line_no, "match": redact(val),
                })
    return findings


def scan_files(root: Path, excludes: set[str]) -> list[dict]:
    findings: list[dict] = []
    for p in root.rglob("*"):
        if not p.is_file() or should_skip(p, excludes):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        findings.extend(scan_text(text, p))
    return findings


def scan_git_history() -> list[dict]:
    """git log -p de TODO el historial, linea por linea (lento en repos grandes)."""
    try:
        out = subprocess.run(
            ["git", "log", "--all", "-p", "--no-color"],
            capture_output=True, text=True, check=False,
        ).stdout
    except FileNotFoundError:
        print("::warn::git no disponible — saltando escaneo de historial.", file=sys.stderr)
        return []
    findings = []
    cur_path = "<unknown>"
    for line in out.splitlines():
        if line.startswith("diff --git"):
            m = re.match(r"diff --git a/(.*) b/", line)
            if m: cur_path = m.group(1)
        else:
            tmp = scan_text(line, Path(cur_path))
            findings.extend(tmp)
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Fast secret scanner (regex-based).")
    ap.add_argument("path", nargs="?", default=".", help="raíz a escanear (default: .)")
    ap.add_argument("--exit-code", type=int, default=1, help="exit code si hallazgos (default 1)")
    ap.add_argument("--no-history", action="store_true", help="no escanea historial git")
    ap.add_argument("--exclude", default=",".join(sorted(DEFAULT_EXCLUDE)),
                    help="dirs a excluir (csv)")
    args = ap.parse_args()

    excludes = set(args.exclude.split(","))
    root = Path(args.path).resolve()
    print(f"::group::scan_secrets — {root}")
    findings = scan_files(root, excludes)
    if not args.no_history and (root / ".git").exists():
        findings.extend(scan_git_history())

    if not findings:
        print("✅ No se detectaron secretos (pase regex).")
        print("::endgroup::")
        return 0

    print(f"🚨 Se detectaron {len(findings)} posible(s) secreto(s):")
    for f in findings:
        print(f"  - [{f['tipo']}] {f['path']}:{f['line']}  match={f['match']}")
    print("::endgroup::")
    print("Rotate cualquier clave real y muévela a un gestor de secretos / env.",
          file=sys.stderr)
    return args.exit_code


if __name__ == "__main__":
    sys.exit(main())
