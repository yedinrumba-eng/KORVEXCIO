"""S5.3 - Tests for user provisioning, roles, permissions, password policy, session limits, audit trail.

Tests run as real users (frappe.set_user), not Administrator.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime, nowdate
from korvexcio.roles import (
    create_cashier_user,
    create_owner_user,
    create_accountant_user,
    set_password_policy,
    configure_session_limits,
    log_user_activity,
    get_user_activity_log,
    assign_company_user_permission,
    sync_roles,
    CAJERO_SALES_INVOICE_PERMS,
    DUENO_SALES_INVOICE_PERMS,
    CONTADOR_SALES_INVOICE_PERMS,
    VLJ,
    ESE,
    ROLES,
)

COMPANY_A = VLJ
COMPANY_B = ESE

TEST_CASHIER_A = "_test.cashier.a@korvexdev.cc"
TEST_CASHIER_B = "_test.cashier.b@korvexdev.cc"
TEST_OWNER = "_test.owner@korvexdev.cc"
TEST_ACCOUNTANT = "_test.accountant@korvexdev.cc"


class TestRolesPermissions(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        before_tests()
        sync_roles()

        # Configurar password policy para tests
        set_password_policy(min_length=8, require_special=False, expire_days=90)
        configure_session_limits(cashier_hours=8, owner_hours=12, concurrent_sessions_cashier=1, concurrent_sessions_owner=3)

        # Limpiar usuarios de test previos
        for email in [TEST_CASHIER_A, TEST_CASHIER_B, TEST_OWNER, TEST_ACCOUNTANT]:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)

        # Crear usuarios de test usando las funciones de provisión
        cls.cashier_a = create_cashier_user(TEST_CASHIER_A, "Cajero Test A", COMPANY_A, "TestPass123")
        cls.cashier_b = create_cashier_user(TEST_CASHIER_B, "Cajero Test B", COMPANY_B, "TestPass123")
        cls.owner = create_owner_user(TEST_OWNER, "Owner Test", [COMPANY_A, COMPANY_B], "TestPass123")
        cls.accountant = create_accountant_user(TEST_ACCOUNTANT, "Accountant Test", [COMPANY_A, COMPANY_B], "TestPass123")

        # Setup básico de datos
        cls.warehouse_a = cls._ensure_warehouse("_Test WH Roles A", COMPANY_A)
        cls.warehouse_b = cls._ensure_warehouse("_Test WH Roles B", COMPANY_B)
        cls.customer_a = cls._ensure_customer("_Test Customer A", COMPANY_A)
        cls.customer_b = cls._ensure_customer("_Test Customer B", COMPANY_B)
        cls.item = cls._ensure_item("_Test Item Roles")

    @classmethod
    def tearDownClass(cls):
        # Limpiar usuarios de test
        for email in [TEST_CASHIER_A, TEST_CASHIER_B, TEST_OWNER, TEST_ACCOUNTANT]:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)
        super().tearDownClass()

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    @staticmethod
    def _ensure_warehouse(name: str, company: str):
        wh_name = f"{name} - {'_TCKA' if company == COMPANY_A else '_TCKB'}"
        if frappe.db.exists("Warehouse", wh_name):
            return wh_name
        frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": name,
            "company": company,
        }).insert()
        return wh_name

    @staticmethod
    def _ensure_customer(name: str, company: str):
        if frappe.db.exists("Customer", name):
            return name
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": name,
            "customer_group": "Commercial",
            "territory": "Dominican Republic",
        }).insert()
        return name

    @staticmethod
    def _ensure_item(name: str):
        if frappe.db.exists("Item", name):
            return name
        frappe.get_doc({
            "doctype": "Item",
            "item_code": name,
            "item_name": name,
            "item_group": "Products",
            "stock_uom": "Nos",
            "is_stock_item": 1,
        }).insert()
        return name

    # =========================================================================
    # User Provisioning Tests
    # =========================================================================

    def test_create_cashier_user(self):
        """Test crear cajero para VLJ."""
        email = "_test.cashier.new.a@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        result = create_cashier_user(email, "Nuevo Cajero A", COMPANY_A, "TestPass123")
        self.assertEqual(result, email)

        # Verificar rol
        user = frappe.get_doc("User", email)
        roles = [r.role for r in user.roles]
        self.assertIn("Cajero VLJ", roles)

        # Verificar User Permission
        perms = frappe.get_all("User Permission", filters={"user": email, "allow": "Company"}, pluck="for_value")
        self.assertIn(COMPANY_A, perms)
        self.assertNotIn(COMPANY_B, perms)

        frappe.delete_doc("User", email, force=True)

    def test_create_cashier_user_invalid_company(self):
        """Test crear cajero con company inválida falla."""
        email = "_test.cashier.invalid@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        with self.assertRaises(frappe.ValidationError):
            create_cashier_user(email, "Invalid Company", "INVALID_COMPANY", "TestPass123")

        # Verificar que no se creó
        self.assertFalse(frappe.db.exists("User", email))

    def test_create_owner_user(self):
        """Test crear dueño con acceso a ambas companies."""
        email = "_test.owner.new@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        result = create_owner_user(email, "Nuevo Dueño", [COMPANY_A, COMPANY_B], "TestPass123")
        self.assertEqual(result, email)

        user = frappe.get_doc("User", email)
        roles = [r.role for r in user.roles]
        self.assertIn("Dueño", roles)

        # Verificar User Permissions para ambas companies
        perms = frappe.get_all("User Permission", filters={"user": email, "allow": "Company"}, pluck="for_value")
        self.assertIn(COMPANY_A, perms)
        self.assertIn(COMPANY_B, perms)

        frappe.delete_doc("User", email, force=True)

    def test_create_owner_user_single_company(self):
        """Test crear dueño con acceso a una sola company."""
        email = "_test.owner.single@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        result = create_owner_user(email, "Dueño Single", [COMPANY_A], "TestPass123")
        self.assertEqual(result, email)

        perms = frappe.get_all("User Permission", filters={"user": email, "allow": "Company"}, pluck="for_value")
        self.assertIn(COMPANY_A, perms)
        self.assertNotIn(COMPANY_B, perms)

        frappe.delete_doc("User", email, force=True)

    def test_create_accountant_user(self):
        """Test crear contador con acceso de solo-lectura."""
        email = "_test.accountant.new@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        result = create_accountant_user(email, "Nuevo Contador", [COMPANY_A, COMPANY_B], "TestPass123")
        self.assertEqual(result, email)

        user = frappe.get_doc("User", email)
        roles = [r.role for r in user.roles]
        self.assertIn("Contador", roles)

        perms = frappe.get_all("User Permission", filters={"user": email, "allow": "Company"}, pluck="for_value")
        self.assertIn(COMPANY_A, perms)
        self.assertIn(COMPANY_B, perms)

        frappe.delete_doc("User", email, force=True)

    def test_password_policy_enforced(self):
        """Test que la password policy se valida al crear usuario."""
        email = "_test.cashier.weak@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        # Contraseña muy corta
        with self.assertRaises(frappe.ValidationError):
            create_cashier_user(email, "Weak Pass", COMPANY_A, "123")

        # Sin mayúscula
        with self.assertRaises(frappe.ValidationError):
            create_cashier_user(email, "No Upper", COMPANY_A, "testpass123")

        # Sin minúscula
        with self.assertRaises(frappe.ValidationError):
            create_cashier_user(email, "No Lower", COMPANY_A, "TESTPASS123")

        # Sin dígito
        with self.assertRaises(frappe.ValidationError):
            create_cashier_user(email, "No Digit", COMPANY_A, "TestPass")

    def test_set_password_policy(self):
        """Test configurar password policy."""
        set_password_policy(min_length=10, require_special=True, expire_days=60)

        self.assertEqual(frappe.db.get_single_value("System Settings", "password_min_length"), 10)
        self.assertEqual(frappe.db.get_single_value("System Settings", "password_require_special"), 1)
        self.assertEqual(frappe.db.get_single_value("System Settings", "password_expire_days"), 60)

    def test_configure_session_limits(self):
        """Test configurar límites de sesión."""
        configure_session_limits(cashier_hours=6, owner_hours=10, concurrent_sessions_cashier=1, concurrent_sessions_owner=2)

        self.assertEqual(frappe.db.get_single_value("System Settings", "cashier_session_hours"), 6)
        self.assertEqual(frappe.db.get_single_value("System Settings", "owner_session_hours"), 10)
        self.assertEqual(frappe.db.get_single_value("System Settings", "concurrent_sessions_cashier"), 1)
        self.assertEqual(frappe.db.get_single_value("System Settings", "concurrent_sessions_owner"), 2)

    # =========================================================================
    # Permissions Tests (using real users via frappe.set_user)
    # =========================================================================

    def test_cajero_can_read_own_company_warehouse(self):
        """Cajero VLJ puede leer warehouse de su company."""
        frappe.set_user(self.cashier_a)
        warehouse = frappe.get_doc("Warehouse", self.warehouse_a)
        self.assertEqual(warehouse.company, COMPANY_A)

    def test_cajero_cannot_read_other_company_warehouse(self):
        """Cajero VLJ NO puede leer warehouse de otra company."""
        frappe.set_user(self.cashier_a)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("Warehouse", self.warehouse_b)

    def test_cajero_can_create_sales_invoice_own_company(self):
        """Cajero VLJ puede crear Sales Invoice en su company."""
        frappe.set_user(self.cashier_a)
        si = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": self.customer_a,
            "company": COMPANY_A,
            "items": [{
                "item_code": self.item,
                "qty": 1,
                "rate": 100,
            }],
        })
        si.insert()
        self.assertEqual(si.company, COMPANY_A)
        si.submit()
        self.assertEqual(si.docstatus, 1)

    def test_cajero_cannot_create_sales_invoice_other_company(self):
        """Cajero VLJ NO puede crear Sales Invoice en otra company."""
        frappe.set_user(self.cashier_a)
        with self.assertRaises(frappe.PermissionError):
            si = frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": self.customer_b,
                "company": COMPANY_B,
                "items": [{
                    "item_code": self.item,
                    "qty": 1,
                    "rate": 100,
                }],
            })
            si.insert()

    def test_cajero_cannot_cancel_sales_invoice(self):
        """Cajero NO puede cancelar Sales Invoice (solo Dueño)."""
        frappe.set_user(self.cashier_a)
        si = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": self.customer_a,
            "company": COMPANY_A,
            "items": [{
                "item_code": self.item,
                "qty": 1,
                "rate": 100,
            }],
        })
        si.insert()
        si.submit()

        with self.assertRaises(frappe.PermissionError):
            si.cancel()

    def test_dueno_can_cancel_sales_invoice(self):
        """Dueño PUEDE cancelar Sales Invoice de ambas companies."""
        # Crear invoice como cajero A
        frappe.set_user(self.cashier_a)
        si = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": self.customer_a,
            "company": COMPANY_A,
            "items": [{
                "item_code": self.item,
                "qty": 1,
                "rate": 100,
            }],
        })
        si.insert()
        si.submit()
        si_name = si.name

        # Cancelar como dueño
        frappe.set_user(self.owner)
        si = frappe.get_doc("Sales Invoice", si_name)
        si.cancel()
        self.assertEqual(si.docstatus, 2)

    def test_dueno_can_read_both_companies(self):
        """Dueño ve warehouses de ambas companies."""
        frappe.set_user(self.owner)
        warehouses = frappe.get_list("Warehouse", pluck="name")
        self.assertIn(self.warehouse_a, warehouses)
        self.assertIn(self.warehouse_b, warehouses)

    def test_dueno_can_create_sales_invoice_both_companies(self):
        """Dueño puede crear Sales Invoice en ambas companies."""
        frappe.set_user(self.owner)

        si_a = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": self.customer_a,
            "company": COMPANY_A,
            "items": [{"item_code": self.item, "qty": 1, "rate": 100}],
        })
        si_a.insert()
        self.assertEqual(si_a.company, COMPANY_A)

        si_b = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": self.customer_b,
            "company": COMPANY_B,
            "items": [{"item_code": self.item, "qty": 1, "rate": 100}],
        })
        si_b.insert()
        self.assertEqual(si_b.company, COMPANY_B)

    def test_contador_read_only_both_companies(self):
        """Contador solo-lectura en ambas companies."""
        frappe.set_user(self.accountant)

        # Puede leer
        warehouses = frappe.get_list("Warehouse", pluck="name")
        self.assertIn(self.warehouse_a, warehouses)
        self.assertIn(self.warehouse_b, warehouses)

        # NO puede crear
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": "_Test WH Contador",
                "company": COMPANY_A,
            }).insert()

        # NO puede crear Sales Invoice
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": self.customer_a,
                "company": COMPANY_A,
                "items": [{"item_code": self.item, "qty": 1, "rate": 100}],
            }).insert()

    def test_cajero_can_manage_own_pos_shifts(self):
        """Cajero puede crear/leer/editar/submit sus turnos POS."""
        frappe.set_user(self.cashier_a)

        # Crear POS Opening Shift
        shift = frappe.get_doc({
            "doctype": "POS Opening Shift",
            "company": COMPANY_A,
            "pos_profile": "_Test POS Profile VLJ",
            "opening_amount": 1000,
        })
        shift.insert()
        self.assertEqual(shift.company, COMPANY_A)

        # Submit
        shift.submit()
        self.assertEqual(shift.docstatus, 1)

        # NO puede cancelar
        with self.assertRaises(frappe.PermissionError):
            shift.cancel()

    def test_dueno_can_cancel_pos_shifts(self):
        """Dueño puede cancelar turnos POS."""
        frappe.set_user(self.cashier_a)
        shift = frappe.get_doc({
            "doctype": "POS Opening Shift",
            "company": COMPANY_A,
            "pos_profile": "_Test POS Profile VLJ",
            "opening_amount": 1000,
        })
        shift.insert()
        shift.submit()
        shift_name = shift.name

        frappe.set_user(self.owner)
        shift = frappe.get_doc("POS Opening Shift", shift_name)
        shift.cancel()
        self.assertEqual(shift.docstatus, 2)

    # =========================================================================
    # ECF Doctypes Permissions Tests
    # =========================================================================

    def test_cajero_can_read_ecf(self):
        """Cajero puede leer ECF (para ver estado)."""
        frappe.set_user(self.cashier_a)
        # ECF no existe aún pero el permiso debería estar configurado
        perms = frappe.get_all("Custom DocPerm", filters={"parent": "ECF", "role": "Cajero VLJ"}, fields=["read"])
        self.assertTrue(any(p.read for p in perms))

    def test_cajero_can_read_ecf_print_queue(self):
        """Cajero puede leer ECF Print Queue (para reimprimir)."""
        frappe.set_user(self.cashier_a)
        perms = frappe.get_all("Custom DocPerm", filters={"parent": "ECF Print Queue", "role": "Cajero VLJ"}, fields=["read"])
        self.assertTrue(any(p.read for p in perms))

    def test_dueno_full_access_ecf(self):
        """Dueño full access a todos los doctypes ECF."""
        frappe.set_user(self.owner)
        for doctype in ["ECF", "ECF Settings", "ECF Integration Log", "ECF Contingencia", "ECF Print Queue", "Secuencia eNCF"]:
            perms = frappe.get_all("Custom DocPerm", filters={"parent": doctype, "role": "Dueño"}, fields=["create", "read", "write", "submit", "cancel"])
            self.assertTrue(any(p.create and p.read and p.write for p in perms))

    def test_contador_read_only_ecf(self):
        """Contador solo-lectura en todos los doctypes ECF."""
        frappe.set_user(self.accountant)
        for doctype in ["ECF", "ECF Settings", "ECF Integration Log", "ECF Contingencia", "ECF Print Queue", "Secuencia eNCF"]:
            perms = frappe.get_all("Custom DocPerm", filters={"parent": doctype, "role": "Contador"}, fields=["read"])
            self.assertTrue(any(p.read for p in perms))

    # =========================================================================
    # Audit Trail Tests
    # =========================================================================

    def test_log_user_activity(self):
        """Test registrar actividad de usuario."""
        log_user_activity(self.cashier_a, "login", "Success", "Test login", "User", self.cashier_a)

        logs = get_user_activity_log(user=self.cashier_a, limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "login")
        self.assertEqual(logs[0].status, "Success")

    def test_get_user_activity_log_filtered(self):
        """Test filtrar log de actividad."""
        log_user_activity(self.cashier_a, "login", "Success", "Test 1")
        log_user_activity(self.cashier_a, "logout", "Success", "Test 2")
        log_user_activity(self.cashier_b, "login", "Success", "Test 3")

        logs = get_user_activity_log(user=self.cashier_a, limit=10)
        self.assertEqual(len([l for l in logs if l.user == self.cashier_a]), 2)

        logs = get_user_activity_log(action="login", limit=10)
        self.assertEqual(len(logs), 2)

    def test_audit_trail_on_role_change(self):
        """Test que cambio de rol se audita."""
        from korvexcio.roles import assign_role_to_user, remove_role_from_user

        email = "_test.audit.role@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        # Crear usuario base
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Audit Test",
            "user_type": "System User",
            "send_welcome_email": 0,
            "roles": [{"role": "Cajero VLJ"}],
        })
        user.insert()

        # Asignar rol - debería loggear
        frappe.set_user("Administrator")
        assign_role_to_user(email, "Contador")

        logs = get_user_activity_log(user="Administrator", action="role_change", limit=5)
        self.assertTrue(any("Contador" in l.details for l in logs))

        # Remover rol - debería loggear
        remove_role_from_user(email, "Contador")

        logs = get_user_activity_log(user="Administrator", action="role_change", limit=5)
        self.assertTrue(any("Removed role Contador" in l.details for l in logs))

        frappe.delete_doc("User", email, force=True)

    # =========================================================================
    # Role Management Permission Tests (SEC-A01)
    # =========================================================================

    def test_cajero_cannot_assign_privileged_roles(self):
        """Cajero NO puede asignar Dueño o Contador."""
        from korvexcio.roles import assign_role_to_user

        email = "_test.cajero.priv@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        # Crear usuario base sin roles
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Test Priv",
            "user_type": "System User",
            "send_welcome_email": 0,
            "roles": [],
        })
        user.insert()

        # Como cajero VLJ, intentar asignar Dueño -> debe fallar
        frappe.set_user(self.cashier_a)
        with self.assertRaises(frappe.PermissionError):
            assign_role_to_user(email, "Dueño")

        with self.assertRaises(frappe.PermissionError):
            assign_role_to_user(email, "Contador")

        # Como cajero VLJ, asignar Cajero ESE -> debe funcionar (rol de cajero)
        assign_role_to_user(email, "Cajero ESE")
        user_doc = frappe.get_doc("User", email)
        self.assertIn("Cajero ESE", [r.role for r in user_doc.roles])

        frappe.delete_doc("User", email, force=True)

    def test_dueno_can_assign_privileged_roles(self):
        """Dueño PUEDE asignar Dueño y Contador."""
        from korvexcio.roles import assign_role_to_user

        email = "_test.dueno.priv@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Test Dueño Priv",
            "user_type": "System User",
            "send_welcome_email": 0,
            "roles": [],
        })
        user.insert()

        # Como Dueño, asignar Contador -> debe funcionar
        frappe.set_user(self.owner)
        assign_role_to_user(email, "Contador")
        user_doc = frappe.get_doc("User", email)
        self.assertIn("Contador", [r.role for r in user_doc.roles])

        # Como Dueño, asignar Dueño -> debe funcionar
        assign_role_to_user(email, "Dueño")
        user_doc = frappe.get_doc("User", email)
        self.assertIn("Dueño", [r.role for r in user_doc.roles])

        frappe.delete_doc("User", email, force=True)

    def test_user_without_write_permission_cannot_assign_roles(self):
        """Usuario sin permiso 'write' en User NO puede asignar roles."""
        from korvexcio.roles import assign_role_to_user

        # Crear usuario con solo rol "Contador" (solo read en User)
        email = "_test.no.write@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "No Write",
            "user_type": "System User",
            "send_welcome_email": 0,
            "roles": [{"role": "Contador"}],
        })
        user.insert()

        # Asignar User Permission para Company A
        from korvexcio.roles import assign_company_user_permission
        assign_company_user_permission(email, COMPANY_A)

        # Como Contador (sin write en User), intentar asignar rol -> debe fallar
        frappe.set_user(email)
        with self.assertRaises(frappe.PermissionError):
            assign_role_to_user(self.cashier_a, "Cajero ESE")

        frappe.delete_doc("User", email, force=True)

    def test_remove_role_prevents_last_role(self):
        """No se puede remover el último rol del usuario."""
        from korvexcio.roles import remove_role_from_user

        email = "_test.last.role@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        # Usuario con solo un rol
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Last Role",
            "user_type": "System User",
            "send_welcome_email": 0,
            "roles": [{"role": "Cajero VLJ"}],
        })
        user.insert()

        frappe.set_user("Administrator")
        with self.assertRaises(frappe.ValidationError):
            remove_role_from_user(email, "Cajero VLJ")

        # Agregar segundo rol y remover el primero -> debe funcionar
        from korvexcio.roles import assign_role_to_user
        assign_role_to_user(email, "Cajero ESE")
        remove_role_from_user(email, "Cajero VLJ")

        user_doc = frappe.get_doc("User", email)
        self.assertEqual(len(user_doc.roles), 1)
        self.assertIn("Cajero ESE", [r.role for r in user_doc.roles])

        frappe.delete_doc("User", email, force=True)

    def test_remove_role_requires_privilege_for_contador_dueno(self):
        """Remover Contador/Dueño requiere privilegio (System Manager o Dueño)."""
        from korvexcio.roles import assign_role_to_user, remove_role_from_user

        email = "_test.remove.priv@korvexdev.cc"
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True)

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Remove Priv",
            "user_type": "System User",
            "send_welcome_email": 0,
            "roles": [{"role": "Contador"}],
        })
        user.insert()

        # Como cajero, intentar remover Contador -> debe fallar
        frappe.set_user(self.cashier_a)
        with self.assertRaises(frappe.PermissionError):
            remove_role_from_user(email, "Contador")

        # Como Dueño, remover Contador -> debe funcionar
        frappe.set_user(self.owner)
        remove_role_from_user(email, "Contador")
        user_doc = frappe.get_doc("User", email)
        self.assertNotIn("Contador", [r.role for r in user_doc.roles])

        frappe.delete_doc("User", email, force=True)

    def test_assign_role_invalid_role_rejected(self):
        """Rol no asignable via API es rechazado."""
        from korvexcio.roles import assign_role_to_user

        frappe.set_user("Administrator")
        with self.assertRaises(frappe.ValidationError):
            assign_role_to_user(self.cashier_a, "System Manager")

        with self.assertRaises(frappe.ValidationError):
            assign_role_to_user(self.cashier_a, "Rol Inexistente")

    # =========================================================================
    # freeze_company on User Tests
    # =========================================================================

    def test_user_company_freeze_via_user_permission(self):
        """User Permission de Company actúa como freeze_company en User."""
        frappe.set_user(self.cashier_a)

        # El usuario no debería poder modificar sus propios User Permissions
        # (no tiene permiso write en User Permission)
        perms = frappe.get_all("User Permission", filters={"user": self.cashier_a, "allow": "Company"})
        self.assertEqual(len(perms), 1)

        # Intentar crear otro User Permission para otra company debería fallar
        # porque Cajero no tiene permiso create en User Permission
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({
                "doctype": "User Permission",
                "user": self.cashier_a,
                "allow": "Company",
                "for_value": COMPANY_B,
                "apply_to_all_doctypes": 1,
            }).insert()

    # =========================================================================
    # System Manager NOT assigned to Dueño (S1.7 verified)
    # =========================================================================

    def test_dueno_not_system_manager(self):
        """Dueño NO tiene rol System Manager."""
        user = frappe.get_doc("User", self.owner)
        roles = [r.role for r in user.roles]
        self.assertNotIn("System Manager", roles)
        self.assertIn("Dueño", roles)

    def test_cajero_not_system_manager(self):
        """Cajero NO tiene rol System Manager."""
        user = frappe.get_doc("User", self.cashier_a)
        roles = [r.role for r in user.roles]
        self.assertNotIn("System Manager", roles)
        self.assertIn("Cajero VLJ", roles)

    def test_all_roles_exist(self):
        """Todos los roles definidos existen."""
        for role in ROLES:
            self.assertTrue(frappe.db.exists("Role", role))

    def test_custom_docperms_exist(self):
        """Custom DocPerms existen para doctypes clave."""
        key_doctypes = ["Sales Invoice", "POS Opening Shift", "POS Closing Shift", "Customer", "Item"]

        for doctype in key_doctypes:
            for role in ROLES:
                exists = frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role})
                self.assertTrue(exists, f"Missing Custom DocPerm for {doctype} / {role}")
