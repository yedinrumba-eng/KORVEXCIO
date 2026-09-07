"""ECF module - Facturación Electrónica para República Dominicana.

Exports:
- thermal_print: Thermal receipt generation (HTML + ESC/POS) with e-CF QR
- print_queue: Server-side print queue with offline sync support
- qr: QR code generation for e-CF verification
- tasks: Async e-CF emission and polling
- sales_invoice_hooks: Sales Invoice doc_events for ECF lifecycle
"""

from .thermal_print import (
    ThermalReceiptBuilder,
    generate_thermal_receipt_html,
    generate_thermal_receipt_escpos,
    save_receipt_for_test,
    _dev_test_thermal_print,
)
from .print_queue import (
    queue_print_job,
    process_print_queue,
    get_pending_print_count,
    requeue_failed_prints,
    pos_queue_print,
    pos_get_print_status,
    pos_sync_offline_prints,
)

__all__ = [
    # Thermal printing
    "ThermalReceiptBuilder",
    "generate_thermal_receipt_html",
    "generate_thermal_receipt_escpos",
    "save_receipt_for_test",
    "_dev_test_thermal_print",
    # Print queue
    "queue_print_job",
    "process_print_queue",
    "get_pending_print_count",
    "requeue_failed_prints",
    "pos_queue_print",
    "pos_get_print_status",
    "pos_sync_offline_prints",
]
