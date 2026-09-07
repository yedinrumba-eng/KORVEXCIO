"""Bulk catalog import from Excel/CSV for S5.1 — 500-1000 SKUs.

FASE 4.8: Este archivo ahora es solo un re-export del módulo dividido.
Los módulos reales están en:
- bulk_import_parser.py: parse_excel, parse_csv, parse_file, normalize_headers
- bulk_import_builder.py: create_item_with_variants, _create_template, _create_variant
- bulk_import_defaults.py: _upsert_item_price, _get_default_warehouse
- bulk_import_cli.py: ImportResult, bulk_import_cmd
"""

from __future__ import annotations

from .bulk_import_parser import (
    normalize_headers,
    validate_required_fields,
    parse_excel,
    parse_csv,
    parse_file,
    COLUMN_ALIASES,
    REQUIRED_COLUMNS,
)
from .bulk_import_builder import (
    create_item_with_variants,
    _create_template,
    _create_variant,
    _create_item_defaults,
)
from .bulk_import_defaults import (
    _upsert_item_price,
    _get_default_warehouse,
)
from .bulk_import_cli import (
    ImportResult,
    bulk_import_cmd,
)

__all__ = [
    # Parser
    "normalize_headers",
    "validate_required_fields",
    "parse_excel",
    "parse_csv",
    "parse_file",
    "COLUMN_ALIASES",
    "REQUIRED_COLUMNS",
    # Builder
    "create_item_with_variants",
    "_create_template",
    "_create_variant",
    "_create_item_defaults",
    # Defaults
    "_upsert_item_price",
    "_get_default_warehouse",
    # CLI
    "ImportResult",
    "bulk_import_cmd",
]