"""Controller for ECF Print Queue DocType (S4.4).

Server-side persistence for thermal print jobs. Provides multi-device
print queue with retry logic and status tracking.
"""

import frappe
from frappe.model.document import Document


class ECFPrintQueue(Document):
    def before_insert(self) -> None:
        """Set created_at on insert."""
        if not self.created_at:
            self.created_at = frappe.utils.now()

    def on_update(self) -> None:
        """Track status transitions."""
        if self.has_value_changed("status"):
            now = frappe.utils.now()
            if self.status == "Printing" and not self.started_at:
                self.db_set("started_at", now, update_modified=False)
            elif self.status == "Completed" and not self.completed_at:
                self.db_set("completed_at", now, update_modified=False)


@frappe.whitelist()
def get_pending_prints(company: str | None = None, limit: int = 20, include_failed: bool = False) -> list[dict]:
    """Get pending print jobs for a company (for POS polling).

    Args:
        company: Filter by company
        limit: Max results (default 20)
        include_failed: If True, also include 'Failed' status jobs (for requeue UI)
    """
    statuses = ["Pending", "Printing"]
    if include_failed:
        statuses.append("Failed")

    filters = {"status": ["in", statuses]}
    if company:
        filters["company"] = company

    return frappe.get_all(
        "ECF Print Queue",
        filters=filters,
        fields=["name", "invoice_name", "status", "priority", "attempts", "error_message", "created_at"],
        order_by="priority asc, creation asc",
        limit=limit,
    )


@frappe.whitelist()
def mark_print_completed(queue_name: str) -> dict:
    """Mark a print job as completed (called by print worker)."""
    doc = frappe.get_doc("ECF Print Queue", queue_name)
    if doc.status not in ["Pending", "Printing"]:
        return {"success": False, "error": f"Invalid status: {doc.status}"}

    doc.status = "Completed"
    doc.completed_at = frappe.utils.now()
    doc.save(ignore_permissions=True)
    return {"success": True}


@frappe.whitelist()
def mark_print_failed(queue_name: str, error: str) -> dict:
    """Mark a print job as failed (called by print worker)."""
    doc = frappe.get_doc("ECF Print Queue", queue_name)
    doc.attempts = (doc.attempts or 0) + 1
    doc.error_message = error[:500]
    if doc.attempts >= 3:
        doc.status = "Failed"
    else:
        doc.status = "Pending"
    doc.save(ignore_permissions=True)
    return {"success": True}