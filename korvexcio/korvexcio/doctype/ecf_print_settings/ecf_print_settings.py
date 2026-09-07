"""ECF Print Settings — Configuración de impresión térmica por Company (FASE 4.4).

Permite configurar constantes de impresora por Company en lugar de hardcoded
en thermal_print.py. Cada Company puede tener su propia configuración según
el modelo de impresora que use (Epson, Star, Bixolon, Custom, Genérico)."""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe import _


class ECFPrintSettings(Document):
    """Configuración de impresión térmica para e-CF.

    Se crea una por Company (company es Link único). Los valores por defecto
    corresponden a una impresora genérica 80mm ESC/POS estándar.
    """

    def validate(self):
        if not self.company:
            frappe.throw(_("Company es requerida"))

        # Validar que solo existe una configuración por Company
        existing = frappe.db.exists(
            "ECF Print Settings",
            {"company": self.company, "name": ["!=", self.name]},
        )
        if existing:
            frappe.throw(
                _("Ya existe una configuración de impresión para {0}").format(self.company),
                frappe.DuplicateEntryError,
            )

        # Validar rangos
        if self.qr_module_size and (self.qr_module_size < 1 or self.qr_module_size > 8):
            frappe.throw(_("Tamaño de módulo QR debe estar entre 1 y 8"))

    def get_printer_constants(self) -> dict:
        """Retorna constantes de impresora para usar en ThermalReceiptBuilder.

        Si la configuración es un modelo conocido, usa valores optimizados.
        Si es Genérico, usa los valores custom configurados.
        """
        # Presets por modelo conocido
        presets = {
            "Epson TM-T20/T88": {
                "width_dots": 576,
                "char_width": 12,
                "char_height": 24,
            },
            "Star TSP100/TSP650": {
                "width_dots": 576,
                "char_width": 12,
                "char_height": 24,
            },
            "Bixolon SRP-350/SRP-275": {
                "width_dots": 576,
                "char_width": 12,
                "char_height": 24,
            },
            "Custom KUBE/SMART": {
                "width_dots": 576,
                "char_width": 12,
                "char_height": 24,
            },
        }

        if self.printer_model in presets:
            base = presets[self.printer_model]
        else:
            # Genérico: usar valores custom
            base = {
                "width_dots": self.printer_width_dots or 576,
                "char_width": self.char_width_dots or 12,
                "char_height": self.char_height_dots or 24,
            }

        return {
            "width_dots": base["width_dots"],
            "char_width": base["char_width"],
            "char_height": base["char_height"],
            "max_chars_per_line": base["width_dots"] // base["char_width"],
            "qr_module_size": self.qr_module_size or 4,
            "qr_error_correction": (self.qr_error_correction or "M (15%)")[0],  # L, M, Q, H
            "cut_paper": self.cut_paper or "Full cut (Guillotina)",
            "header_text": self.header_text or "",
            "footer_text": self.footer_text or "¡Gracias por su compra!",
        }


def get_print_settings_for_company(company: str) -> dict:
    """Obtiene constantes de impresora para una Company.

    Si no existe configuración, retorna defaults genéricos.
    """
    if not frappe.db.exists("ECF Print Settings", company):
        return _default_constants()

    settings = frappe.get_doc("ECF Print Settings", company)
    return settings.get_printer_constants()


def _default_constants() -> dict:
    """Defaults genéricos para impresora 80mm ESC/POS estándar."""
    return {
        "width_dots": 576,
        "char_width": 12,
        "char_height": 24,
        "max_chars_per_line": 48,
        "qr_module_size": 4,
        "qr_error_correction": "M",
        "cut_paper": "Full cut (Guillotina)",
        "header_text": "",
        "footer_text": "¡Gracias por su compra!",
    }