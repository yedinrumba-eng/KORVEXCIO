"""Print queue for thermal receipts - offline (IndexedDB) + online (S4.4).

FASE 4.8: Este archivo ahora es solo un re-export del módulo dividido.
Los módulos reales están en:
- print_queue_server.py: Server-side queue processing
- print_queue_pos_api.py: POS API endpoints
- print_queue_offline.py: Offline sync utilities
"""

from __future__ import annotations

from .print_queue_server import (
    queue_print_job,
    process_print_queue,
    get_pending_print_count,
    requeue_failed_prints,
    _send_to_printer,
)
from .print_queue_pos_api import (
    pos_queue_print,
    pos_get_print_status,
    pos_sync_offline_prints,
)
from .print_queue_offline import (
    build_offline_queue_payload,
    resolve_offline_conflicts,
    sync_offline_to_server,
)


__all__ = [
    # Server-side queue (re-exported from print_queue_server)
    "queue_print_job",
    "process_print_queue",
    "get_pending_print_count",
    "requeue_failed_prints",
    "_send_to_printer",
    # POS API (re-exported from print_queue_pos_api)
    "pos_queue_print",
    "pos_get_print_status",
    "pos_sync_offline_prints",
    # Offline sync (re-exported from print_queue_offline)
    "build_offline_queue_payload",
    "resolve_offline_conflicts",
    "sync_offline_to_server",
]