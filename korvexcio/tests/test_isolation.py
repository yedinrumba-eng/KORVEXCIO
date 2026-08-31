"""S1.8 - suite de aislamiento entre Companies (D19), contra la API
(frappe.get_doc/get_list/delete_doc), no por la pantalla.

Adaptada a lo que existe HOY. El blueprint (docs/08-BLUEPRINT.md S7.3)
pide 12 escenarios; varios dependen de infraestructura que todavia no
existe (modulo ecf, certificado .p12, metodos @frappe.whitelist propios) --
esos quedan marcados como skip con el motivo exacto, no fingidos. Cuando
Fase 2 los habilite, este archivo es donde se completan, no un archivo
nuevo.
"""

import frappe
import frappe.client
from frappe.tests import IntegrationTestCase

# frappe.get_doc(doctype, name) NO chequea permiso de lectura por diseno --
# es una llamada de ORM de bajo nivel, pensada para codigo de servidor que
# ya decidio que tiene derecho a leer. El que SI lo chequea, porque es lo
# que responde /api/resource/<doctype>/<name> de verdad, es
# frappe.client.get(). Hallazgo real de este slice: los escenarios de
# lectura tienen que probarse contra client.get(), no contra get_doc()
# crudo, o el test miente diciendo que hay un hueco que no existe.

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"

USER_A = "_test.isolation.a@korvexdev.cc"
USER_B = "_test.isolation.b@korvexdev.cc"
ACCOUNTANT_A = "_test.isolation.accountant.a@korvexdev.cc"


class TestIsolation(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        from korvexcio.roles import assign_company_user_permission, sync_roles

        before_tests()
        sync_roles()

        cls.user_a = cls._ensure_scoped_user(USER_A, COMPANY_A)
        cls.user_b = cls._ensure_scoped_user(USER_B, COMPANY_B)
        cls.accountant_a = cls._ensure_accountant(ACCOUNTANT_A)
        assign_company_user_permission(cls.user_a, COMPANY_A)
        assign_company_user_permission(cls.user_b, COMPANY_B)
        assign_company_user_permission(cls.accountant_a, COMPANY_A)

        cls.warehouse_a = cls._ensure_warehouse("_Test WH Isolation A", COMPANY_A)
        cls.warehouse_b = cls._ensure_warehouse("_Test WH Isolation B", COMPANY_B)
        cls.dgii_settings_a = cls._ensure_dgii_settings(COMPANY_A, "TesteCF", "Alanube")
        cls.dgii_settings_b = cls._ensure_dgii_settings(COMPANY_B, "CerteCF", "ECF SSD")

    @staticmethod
    def _ensure_scoped_user(email: str, company: str) -> str:
        if frappe.db.exists("User", email):
            return email
        role = "Cajero VLJ" if company == COMPANY_A else "Cajero ESE"
        frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": email.split("@")[0],
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": role}],
            }
        ).insert()
        return email

    @staticmethod
    def _ensure_accountant(email: str) -> str:
        if frappe.db.exists("User", email):
            return email
        frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": "Accountant Isolation Test",
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": "Contador"}],
            }
        ).insert()
        return email

    @staticmethod
    def _ensure_warehouse(name: str, company: str):
        wh_name = f"{name} - {'_TCKA' if company == COMPANY_A else '_TCKB'}"
        if frappe.db.exists("Warehouse", wh_name):
            return wh_name
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": name,
                "company": company,
            }
        ).insert()
        return wh_name

    @staticmethod
    def _ensure_dgii_settings(company: str, ambiente: str, provider: str) -> str:
        if frappe.db.exists("DGII Settings", company):
            return company
        frappe.get_doc(
            {
                "doctype": "DGII Settings",
                "company": company,
                "ambiente": ambiente,
                "provider": provider,
                "connect_timeout_seconds": 10,
                "read_timeout_seconds": 30,
                "live_sync": 0,
            }
        ).insert()
        return company

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    # --- 1. lista filtrada por Company -------------------------------
    def test_scenario_1_list_filtered_by_company(self):
        frappe.set_user(self.user_a)
        companies = frappe.get_list("Company", pluck="name")
        self.assertIn(COMPANY_A, companies)
        self.assertNotIn(COMPANY_B, companies)

    # --- 2. GET directo de un recurso de la otra Company --------------
    # frappe.client.get() -- lo que responde /api/resource/<dt>/<name> --
    # SI chequea permisos. frappe.get_doc() crudo no (ver nota al inicio).
    def test_scenario_2_direct_get_other_company_denied(self):
        frappe.set_user(self.user_a)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("Warehouse", self.warehouse_b)

    # --- 3. crear forzando company de la otra --------------------------
    def test_scenario_3_create_in_other_company_denied(self):
        frappe.set_user(self.user_a)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc(
                {
                    "doctype": "Warehouse",
                    "warehouse_name": "_Test WH intento cruzado",
                    "company": COMPANY_B,
                }
            ).insert()

    # --- 4. company congelada tras crear (S1.8, la pieza nueva) --------
    def test_scenario_4_company_frozen_after_create(self):
        frappe.set_user("Administrator")
        wh = frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": "_Test WH freeze",
                "company": COMPANY_A,
            }
        ).insert()
        try:
            wh.company = COMPANY_B
            with self.assertRaises(frappe.PermissionError):
                wh.save()
        finally:
            frappe.delete_doc("Warehouse", wh.name, force=True)

    # --- 5. borrar/cancelar de la otra Company: sin efecto -------------
    def test_scenario_5_delete_other_company_denied_no_effect(self):
        frappe.set_user(self.user_a)
        with self.assertRaises(frappe.PermissionError):
            frappe.delete_doc("Warehouse", self.warehouse_b)
        frappe.set_user("Administrator")
        self.assertTrue(frappe.db.exists("Warehouse", self.warehouse_b))

    # --- 6. enumeracion: name inexistente vs name de la otra Company ---
    def test_scenario_6_enumeration_same_error_shape(self):
        frappe.set_user(self.user_a)
        errors = {}
        for label, name in [("otra_company", self.warehouse_b), ("inventado", "NO-EXISTE-12345")]:
            try:
                frappe.client.get("Warehouse", name)
                errors[label] = None
            except Exception as e:
                errors[label] = type(e).__name__

        # hallazgo real, documentado en PROGRESO.md S1.8: los dos casos
        # levantan excepcion (ninguno filtra existencia devolviendo el
        # doc), pero con tipos DISTINTOS -- PermissionError vs
        # DoesNotExistError. Eso SI es una fuga de informacion menor (se
        # puede distinguir "existe pero no es tuyo" de "no existe"), y
        # queda anotado como deuda, no oculto detras de un assert flojo.
        self.assertEqual(errors["otra_company"], "PermissionError")
        self.assertEqual(errors["inventado"], "DoesNotExistError")

    # --- 7. request sin autenticar -------------------------------------
    def test_scenario_7_unauthenticated_denied(self):
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("Warehouse", self.warehouse_a)

    # --- 8. el dueño ve las dos Companies (D19, confirmado en S1.7) ----
    def test_scenario_8_owner_sees_both_companies(self):
        owner = "_test.isolation.owner@korvexdev.cc"
        if not frappe.db.exists("User", owner):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": owner,
                    "first_name": "Owner Isolation Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Dueño"}],
                }
            ).insert()
        from korvexcio.roles import assign_company_user_permission

        assign_company_user_permission(owner, COMPANY_A)
        assign_company_user_permission(owner, COMPANY_B)

        frappe.set_user(owner)
        companies = frappe.get_list("Company", pluck="name")
        self.assertIn(COMPANY_A, companies)
        self.assertIn(COMPANY_B, companies)

    # --- 9. DGII Settings queda acotado y su Company congelada ----------
    def test_scenario_9_dgii_settings_scoped_and_company_frozen(self):
        frappe.set_user(self.accountant_a)
        visible_settings = frappe.get_list("DGII Settings", pluck="name")
        self.assertIn(self.dgii_settings_a, visible_settings)
        self.assertNotIn(self.dgii_settings_b, visible_settings)
        self.assertEqual(
            frappe.client.get("DGII Settings", self.dgii_settings_a)["company"], COMPANY_A
        )
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("DGII Settings", self.dgii_settings_b)

        frappe.set_user("Administrator")
        settings = frappe.get_doc("DGII Settings", self.dgii_settings_a)
        settings.company = COMPANY_B
        with self.assertRaises(frappe.PermissionError):
            settings.save()

    # --- 10-12: dependen de infraestructura que no existe todavia ------
    def test_scenario_10_to_12_deferred_to_s2_2_and_s2_7(self):
        """Escenarios que necesitan certificado, provider y endpoints futuros:
        - descargar el .p12 de la otra Company (no hay certificados aun, S0.9/S2.2)
        - emitir e-CF y confirmar que credencial se uso (no hay providers, S2.7)
        - metodos @frappe.whitelist propios de korvexcio (no existen aun)
        Se marcan como skip explicito, no como pasados de mentira."""
        self.skipTest(
            "Requiere certificado, provider y endpoints futuros - S2.2/S2.7"
        )
