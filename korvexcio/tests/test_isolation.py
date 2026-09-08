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


class TestIsolation(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        from korvexcio.roles import assign_company_user_permission, sync_roles

        before_tests()
        sync_roles()

        # Generate unique hash for this test instance to ensure isolation
        self.test_hash = frappe.generate_hash(8)

        # Define base names
        self.base_company_a = "_Test Company KORVEXCIO A"
        self.base_company_b = "_Test Company KORVEXCIO B"
        self.base_user_a = "_test.isolation.a@korvexdev.cc"
        self.base_user_b = "_test.isolation.b@korvexdev.cc"
        self.base_accountant_a = "_test.isolation.accountant.a@korvexdev.cc"
        self.base_owner_a = "_test.isolation.owner.a@korvexdev.cc"
        self.base_warehouse_a = "_Test WH Isolation A"
        self.base_warehouse_b = "_Test WH Isolation B"

        # Create unique names for this test instance
        self.company_a = f"{self.base_company_a}-{self.test_hash}"
        self.company_b = f"{self.base_company_b}-{self.test_hash}"
        self.user_a = f"{self.base_user_a.split('@')[0]}+{self.test_hash}@korvexdev.cc"
        self.user_b = f"{self.base_user_b.split('@')[0]}+{self.test_hash}@korvexdev.cc"
        self.accountant_a = f"{self.base_accountant_a.split('@')[0]}+{self.test_hash}@korvexdev.cc"
        self.owner_a = f"{self.base_owner_a.split('@')[0]}+{self.test_hash}@korvexdev.cc"
        self.warehouse_a = f"{self.base_warehouse_a} [{self.test_hash}]"
        self.warehouse_b = f"{self.base_warehouse_b} [{self.test_hash}]"

        # Create test data
        self.user_a = self._ensure_scoped_user(self.user_a, self.company_a)
        self.user_b = self._ensure_scoped_user(self.user_b, self.company_b)
        self.accountant_a = self._ensure_accountant(self.accountant_a)
        self.owner_a = self._ensure_owner_scoped_to_one(self.owner_a)
        assign_company_user_permission(self.user_a, self.company_a)
        assign_company_user_permission(self.user_b, self.company_b)
        assign_company_user_permission(self.accountant_a, self.company_a)
        assign_company_user_permission(self.owner_a, self.company_a)

        self.warehouse_a = self._ensure_warehouse(self.warehouse_a, self.company_a)
        self.warehouse_b = self._ensure_warehouse(self.warehouse_b, self.company_b)
        self.dgii_settings_a = self._ensure_dgii_settings(self.company_a, "TesteCF", "Alanube")
        self.dgii_settings_b = self._ensure_dgii_settings(self.company_b, "CerteCF", "ECF SSD")
        self.cert_a = self._ensure_certificate(self.company_a)
        self.cert_b = self._ensure_certificate(self.company_b)

    def tearDown(self):
        frappe.set_user("Administrator")
        # Clean up in reverse dependency order to avoid foreign key constraints
        try:
            # Clean ECFs first (they depend on Sales Invoices)
            for ecf_name in frappe.get_all("ECF", filters={"reference_doctype": "Sales Invoice"}, pluck="name"):
                ecf_doc = frappe.get_doc("ECF", ecf_name)
                if ecf_doc.docstatus == 1:
                    ecf_doc.cancel()
                frappe.delete_doc("ECF", ecf_name, force=True)

            # Clean Sales Invoices
            for si_name in frappe.get_all("Sales Invoice", pluck="name"):
                si_doc = frappe.get_doc("Sales Invoice", si_name)
                if si_doc.docstatus == 1:
                    si_doc.cancel()
                frappe.delete_doc("Sales Invoice", si_name, force=True)

            # Clean Print Queue entries
            for pq_name in frappe.get_all("Print Queue", pluck="name"):
                frappe.delete_doc("Print Queue", pq_name, force=True)

            # Clean Customers
            for customer_name in frappe.get_all("Customer", pluck="name"):
                frappe.delete_doc("Customer", customer_name, force=True)

            # Clean Items
            for item_name in frappe.get_all("Item", pluck="name"):
                frappe.delete_doc("Item", item_name, force=True)

            # Clean Warehouses
            for warehouse_name in frappe.get_all("Warehouse", pluck="name"):
                frappe.delete_doc("Warehouse", warehouse_name, force=True)

            # Clean Users (except Administrator and Guest)
            for user_email in frappe.get_all("User", filters=[["email", "not in", ["Administrator@example.com", "guest@example.com"]]], pluck="email"):
                frappe.delete_doc("User", user_email, force=True)

            # Clean Companies
            for company_name in frappe.get_all("Company", pluck="name"):
                frappe.delete_doc("Company", company_name, force=True)

            # Clean DGII Settings
            for settings_name in frappe.get_all("DGII Settings", pluck="name"):
                frappe.delete_doc("DGII Settings", settings_name, force=True)

            # Clean DGII Digital Certificates
            for cert_name in frappe.get_all("DGII Digital Certificate", pluck="name"):
                frappe.delete_doc("DGII Digital Certificate", cert_name, force=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            # Ignore if documents don't exist or validation errors during cleanup
            pass

        super().tearDown()

    @staticmethod
    def _ensure_scoped_user(email: str, company: str) -> str:
        if frappe.db.exists("User", email):
            return email
        role = "Cajero VLJ" if company == "_Test Company KORVEXCIO A" else "Cajero ESE"
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
    def _ensure_owner_scoped_to_one(email: str) -> str:
        """Dueño real ve las dos Companies (escenario 8). Para probar
        aislamiento en doctypes donde Contador/Cajero no tienen acceso
        (DGII Digital Certificate), hace falta un Dueño restringido a UNA
        sola Company via User Permission -- no es el caso de uso real
        (el dueño del negocio ve sus dos empresas), es la unica forma de
        probar la denegacion cruzada con el modelo de permisos actual."""
        if frappe.db.exists("User", email):
            return email
        frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": "Owner Scoped Isolation Test",
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": "Dueño"}],
            }
        ).insert()
        return email

    @staticmethod
    def _ensure_warehouse(name: str, company: str):
        wh_name = f"{name} - {'_TCKA' if company == '_Test Company KORVEXCIO A' else '_TCKB'}"
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

    @staticmethod
    def _ensure_certificate(company: str) -> str:
        if frappe.db.exists("DGII Digital Certificate", company):
            return company
        from frappe.utils import add_days

        frappe.get_doc(
            {
                "doctype": "DGII Digital Certificate",
                "company": company,
                "certificate": "/private/files/isolation-test-cert.p12",
                "password": "dummy-cert-password-isolation",
                "valid_until": add_days(frappe.utils.today(), 365),
            }
        ).insert()
        return company

    # --- 1. lista filtrada por Company -------------------------------
    def test_scenario_1_list_filtered_by_company(self):
        frappe.set_user(self.user_a)
        companies = frappe.get_list("Company", pluck="name")
        self.assertIn(self.company_a, companies)
        self.assertNotIn(self.company_b, companies)

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
                    "company": self.company_b,
                }
            ).insert()

    # --- 4. company congelada tras crear (S1.8, la pieza nueva) --------
    def test_scenario_4_company_frozen_after_create(self):
        frappe.set_user("Administrator")
        wh = frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": "_Test WH freeze",
                "company": self.company_a,
            }
        ).insert()
        try:
            wh.company = self.company_b
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
        owner = f"_test.isolation.owner+{self.test_hash}@korvexdev.cc"
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

        assign_company_user_permission(owner, self.company_a)
        assign_company_user_permission(owner, self.company_b)

        frappe.set_user(owner)
        companies = frappe.get_list("Company", pluck="name")
        self.assertIn(self.company_a, companies)
        self.assertIn(self.company_b, companies)

    # --- 9. DGII Settings queda acotado y su Company congelada ----------
    def test_scenario_9_dgii_settings_scoped_and_company_frozen(self):
        frappe.set_user(self.accountant_a)
        visible_settings = frappe.get_list("DGII Settings", pluck="name")
        self.assertIn(self.dgii_settings_a, visible_settings)
        self.assertNotIn(self.dgii_settings_b, visible_settings)
        self.assertEqual(
            frappe.client.get("DGII Settings", self.dgii_settings_a)["company"], self.company_a
        )
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("DGII Settings", self.dgii_settings_b)

        frappe.set_user("Administrator")
        settings = frappe.get_doc("DGII Settings", self.dgii_settings_a)
        settings.company = self.company_b
        with self.assertRaises(frappe.PermissionError):
            settings.save()

    # --- 10. certificado digital: acotado, password nunca sale por API --
    # Cajero/Contador no tienen NINGUN permiso sobre este doctype (a
    # proposito -- ni deberian ver el .p12). Se prueba con Dueño acotado
    # a una sola Company, el unico rol con acceso ademas de System Manager.
    def test_scenario_10_certificate_scoped_and_password_never_exposed(self):
        frappe.set_user(self.owner_a)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("DGII Digital Certificate", self.cert_b)

        own = frappe.client.get("DGII Digital Certificate", self.cert_a)
        self.assertEqual(own["company"], self.company_a)
        self.assertNotIn("dummy-cert-password-isolation", str(own.get("password", "")))

        frappe.set_user("Administrator")
        stored = frappe.db.get_value("DGII Digital Certificate", self.cert_a, "password")
        self.assertNotEqual(stored, "dummy-cert-password-isolation")

    # --- 11-12: dependen de un provider real, todavia no existe ---------
    def test_scenario_11_to_12_deferred_to_s2_7(self):
        """Escenarios que necesitan un provider real conectado (S2.7):
        - emitir e-CF y confirmar que credencial se uso (no hay providers, S2.7)
        - metodos @frappe.whitelist propios de korvexcio/ecf (no existen aun)
        Se marcan como skip explicito, no como pasados de mentira."""
        self.skipTest("Requiere un provider real conectado - S2.7")

    # --- 13. ECF insert con ignore_permissions=True se queda en Company del cajero (SEC-A03) ---
    def test_scenario_13_ecf_created_by_cashier_stays_company_scoped(self):
        """Test de aislamiento dedicado para ecf.insert(ignore_permissions=True) en sales_invoice_hooks.py:122.

        El hook create_ecf_record usa ignore_permissions=True justificado por regla 12b
        (job de background avanza trabajo interno del sistema). Este test confirma que
        un Cajero de Company A encolando una venta genera ECF en Company A, nunca B.
        """
        frappe.set_user(self.user_a)  # Cajero de COMPANY_A

        # Asegurar secuencia E32 para Company A
        if not frappe.db.exists("Secuencia eNCF", f"{self.company_a}-E32"):
            frappe.get_doc({
                "doctype": "Secuencia eNCF",
                "company": self.company_a,
                "tipo_ecf": "E32",
                "desde": 1,
                "hasta": 999999,
                "siguiente": 1,
                "fecha_vencimiento": "2027-12-31",
            }).insert()

        # Crear Sales Invoice de prueba
        si = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": "_Test Customer KORVEXCIO Thermal",
            "company": self.company_a,
            "currency": "DOP",
            "conversion_rate": 1,
            "items": [{
                "item_code": "_Test Item KORVEXCIO Thermal",
                "qty": 1,
                "rate": 1000,
                "income_account": "Sales - _TCKA",
                "cost_center": "Main - _TCKA",
            }],
        })
        si.insert()
        si.submit()  # Esto dispara create_ecf_record via on_submit hook

        try:
            # Verificar que ECF se creó en Company A
            ecf = frappe.get_all(
                "ECF",
                filters={"reference_doctype": "Sales Invoice", "reference_name": si.name},
                fields=["name", "company", "estado"],
                limit=1
            )
            self.assertEqual(len(ecf), 1)
            self.assertEqual(ecf[0].company, self.company_a)
            self.assertEqual(ecf[0].estado, "Pendiente")

            # Verificar que NO hay ECF en Company B para esta factura
            ecf_b = frappe.get_all(
                "ECF",
                filters={"reference_doctype": "Sales Invoice", "reference_name": si.name, "company": self.company_b},
                pluck="name"
            )
            self.assertEqual(len(ecf_b), 0)

        finally:
            # Cleanup
            for ecf_name in frappe.get_all("ECF", filters={"reference_doctype": "Sales Invoice", "reference_name": si.name}, pluck="name"):
                ecf_doc = frappe.get_doc("ECF", ecf_name)
                if ecf_doc.docstatus == 1:
                    ecf_doc.cancel()
                frappe.delete_doc("ECF", ecf_name, force=True, ignore_permissions=True)

            if si.docstatus == 1:
                si.cancel()
            frappe.delete_doc("Sales Invoice", si.name, force=True, ignore_permissions=True)

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

    # --- 10. certificado digital: acotado, password nunca sale por API --
    # Cajero/Contador no tienen NINGUN permiso sobre este doctype (a
    # proposito -- ni deberian ver el .p12). Se prueba con Dueño acotado
    # a una sola Company, el unico rol con acceso ademas de System Manager.
    def test_scenario_10_certificate_scoped_and_password_never_exposed(self):
        frappe.set_user(self.owner_a)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("DGII Digital Certificate", self.cert_b)

        own = frappe.client.get("DGII Digital Certificate", self.cert_a)
        self.assertEqual(own["company"], COMPANY_A)
        self.assertNotIn("dummy-cert-password-isolation", str(own.get("password", "")))

        frappe.set_user("Administrator")
        stored = frappe.db.get_value("DGII Digital Certificate", self.cert_a, "password")
        self.assertNotEqual(stored, "dummy-cert-password-isolation")

    # --- 11-12: dependen de un provider real, todavia no existe ---------
    def test_scenario_11_to_12_deferred_to_s2_7(self):
        """Escenarios que necesitan un provider real conectado (S2.7):
        - emitir e-CF y confirmar que credencial se uso (no hay providers, S2.7)
        - metodos @frappe.whitelist propios de korvexcio/ecf (no existen aun)
        Se marcan como skip explicito, no como pasados de mentira."""
        self.skipTest("Requiere un provider real conectado - S2.7")

    # --- 13. ECF insert con ignore_permissions=True se queda en Company del cajero (SEC-A03) ---
    def test_scenario_13_ecf_created_by_cashier_stays_company_scoped(self):
        """Test de aislamiento dedicado para ecf.insert(ignore_permissions=True) en sales_invoice_hooks.py:122.

        El hook create_ecf_record usa ignore_permissions=True justificado por regla 12b
        (job de background avanza trabajo interno del sistema). Este test confirma que
        un Cajero de Company A encolando una venta genera ECF en Company A, nunca B.
        """
        frappe.set_user(self.user_a)  # Cajero de COMPANY_A

        # Asegurar secuencia E32 para Company A
        if not frappe.db.exists("Secuencia eNCF", f"{COMPANY_A}-E32"):
            frappe.get_doc({
                "doctype": "Secuencia eNCF",
                "company": COMPANY_A,
                "tipo_ecf": "E32",
                "desde": 1,
                "hasta": 999999,
                "siguiente": 1,
                "fecha_vencimiento": "2027-12-31",
            }).insert()

        # Crear Sales Invoice de prueba
        si = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": "_Test Customer KORVEXCIO Thermal",
            "company": COMPANY_A,
            "currency": "DOP",
            "conversion_rate": 1,
            "items": [{
                "item_code": "_Test Item KORVEXCIO Thermal",
                "qty": 1,
                "rate": 1000,
                "income_account": "Sales - _TCKA",
                "cost_center": "Main - _TCKA",
            }],
        })
        si.insert()
        si.submit()  # Esto dispara create_ecf_record via on_submit hook

        try:
            # Verificar que ECF se creó en Company A
            ecf = frappe.get_all(
                "ECF",
                filters={"reference_doctype": "Sales Invoice", "reference_name": si.name},
                fields=["name", "company", "estado"],
                limit=1
            )
            self.assertEqual(len(ecf), 1)
            self.assertEqual(ecf[0].company, COMPANY_A)
            self.assertEqual(ecf[0].estado, "Pendiente")

            # Verificar que NO hay ECF en Company B para esta factura
            ecf_b = frappe.get_all(
                "ECF",
                filters={"reference_doctype": "Sales Invoice", "reference_name": si.name, "company": COMPANY_B},
                pluck="name"
            )
            self.assertEqual(len(ecf_b), 0)

        finally:
            # Cleanup
            for ecf_name in frappe.get_all("ECF", filters={"reference_doctype": "Sales Invoice", "reference_name": si.name}, pluck="name"):
                ecf_doc = frappe.get_doc("ECF", ecf_name)
                if ecf_doc.docstatus == 1:
                    ecf_doc.cancel()
                frappe.delete_doc("ECF", ecf_name, force=True, ignore_permissions=True)

            if si.docstatus == 1:
                si.cancel()
            frappe.delete_doc("Sales Invoice", si.name, force=True, ignore_permissions=True)
