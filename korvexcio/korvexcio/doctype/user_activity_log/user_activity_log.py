# Copyright (c) 2026, Korvex and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UserActivityLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		action: DF.Literal["login", "logout", "failed_login", "role_change", "session_limit_exceeded", "password_change", "permission_change", "document_create", "document_read", "document_update", "document_delete", "document_submit", "document_cancel"]
		details: DF.Text | None
		ip_address: DF.Data | None
		reference_doctype: DF.Link | None
		reference_name: DF.Data | None
		status: DF.Literal["Success", "Failed"]
		timestamp: DF.Datetime
		user: DF.Link
	# end: auto-generated types

	pass