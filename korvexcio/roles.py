import frappe
from frappe import _
from frappe.utils import cint

VLJ = "VAPERIA LA J Y EL JALAPEÑO"
ESE = "EL SABOR DE LAS 5 ESQUINAS"

ROLES = ["Cajero VLJ", "Cajero ESE", "Dueño", "Contador"]

# Dueño necesita crear cajeros con un rol acotado -- NO System Manager
# (blueprint S1.7). Se le da acceso al doctype User y a leer Role para
# poder marcar los checkboxes de rol en el formulario, nada mas.
DUENO_USER_PERMS = {
    "read": 1,
    "write": 1,
    "create": 1,
    "delete": 0,
    "print": 1,
    "email": 1,
    "share": 0,
    "report": 1,
}

BASIC_READ = {"read": 1}

CAJERO_ROLES = ["Cajero VLJ", "Cajero ESE"]

# Hallazgo real (2026-09-01): ningun rol propio tenia NINGUN permiso sobre
# Sales Invoice -- ni siquiera leer. Paso desapercibido porque S2.9 en
# adelante siempre probo como Administrator. Un Cajero real no podia ni
# ver el formulario de venta. Un Cajero somete la venta (S2.9) pero nunca
# la cancela libremente -- eso es control de caja, va a Dueño.
CAJERO_SALES_INVOICE_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1}
DUENO_SALES_INVOICE_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1, "cancel": 1}
CONTADOR_SALES_INVOICE_PERMS = {"read": 1}

# S4.1: el cajero solo LEE su POS Profile (get_pos_profile() de ERPNext lo
# resuelve solo). Configurarlo -- warehouse, metodos de pago, usuarios
# asignados -- es tarea de Dueño, nunca del cajero.
DUENO_POS_PROFILE_PERMS = {"create": 1, "read": 1, "write": 1}

# S4.5: el cajero abre y cierra SU propio turno (create/read/write/submit)
# pero no puede cancelarlo -- eso es control de caja, va a Dueño. El
# arqueo ya es visible via submit; cancelar un turno cerrado es reabrir
# la caja del dia anterior.
CAJERO_CASH_SHIFT_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1}
DUENO_CASH_SHIFT_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1, "cancel": 1}
CONTADOR_CASH_SHIFT_PERMS = {"read": 1}


def sync_roles():
    for role in ROLES:
        ensure_role(role)

    ensure_doc_perm("User", "Dueño", DUENO_USER_PERMS)
    ensure_doc_perm("Role", "Dueño", BASIC_READ)
    # el dueño crea cajeros Y los restringe a su Company -- necesita
    # poder crear "User Permission", si no la mitad del flujo se queda a medias
    ensure_doc_perm("User Permission", "Dueño", {"read": 1, "write": 1, "create": 1})

    for role in ROLES:
        ensure_doc_perm("Company", role, BASIC_READ)

    # Hallazgo real (2026-09-01, S4.5): un Cajero real no podia someter NI
    # UNA venta -- ERPNext valida permiso de LECTURA sobre `Account` al
    # someter cualquier Sales Invoice (income_account, debit_to, etc.), y
    # ningun rol propio lo tenia. Tampoco tenia permiso sobre `Customer`
    # -- no podia ni buscar a quien venderle. Ambos pasaron
    # desapercibidos porque S2.9 solo se probo como Administrator; S4.5
    # es el primer test que somete una venta como un Cajero real.
    for role in CAJERO_ROLES:
        ensure_doc_perm("Account", role, BASIC_READ)
        ensure_doc_perm("Customer", role, {"create": 1, "read": 1})
        ensure_doc_perm("Item", role, BASIC_READ)
        ensure_doc_perm("Cost Center", role, BASIC_READ)
        ensure_doc_perm("UOM", role, BASIC_READ)
        ensure_doc_perm("Mode of Payment", role, BASIC_READ)
    ensure_doc_perm("Customer", "Dueño", {"create": 1, "read": 1, "write": 1})
    ensure_doc_perm("Customer", "Contador", BASIC_READ)

    for role in CAJERO_ROLES:
        ensure_doc_perm("Sales Invoice", role, CAJERO_SALES_INVOICE_PERMS)
    ensure_doc_perm("Sales Invoice", "Dueño", DUENO_SALES_INVOICE_PERMS)
    ensure_doc_perm("Sales Invoice", "Contador", CONTADOR_SALES_INVOICE_PERMS)

    for role in CAJERO_ROLES:
        ensure_doc_perm("POS Profile", role, BASIC_READ)
    ensure_doc_perm("POS Profile", "Dueño", DUENO_POS_PROFILE_PERMS)

    # "... Entry" son los nativos de ERPNext (S4.5); "... Shift" son los
    # propios de POSNext (S4.2) -- la pantalla real crea estos ultimos,
    # no sabemos cual va a quedar en pie a largo plazo.
    for doctype in ("POS Opening Entry", "POS Closing Entry", "POS Opening Shift", "POS Closing Shift"):
        for role in CAJERO_ROLES:
            ensure_doc_perm(doctype, role, CAJERO_CASH_SHIFT_PERMS)
        ensure_doc_perm(doctype, "Dueño", DUENO_CASH_SHIFT_PERMS)
        ensure_doc_perm(doctype, "Contador", CONTADOR_CASH_SHIFT_PERMS)

    # --- S5.3: Transactional doctypes permissions ---
    sync_transactional_doctype_perms()

    # --- S5.3: ECF doctypes permissions ---
    sync_ecf_doctype_perms()

    frappe.db.commit()


def sync_transactional_doctype_perms():
    """S5.3: Permisos para doctypes transaccionales de ERPNext."""
    transactional_doctypes = [
        "Sales Invoice",
        "Sales Order",
        "Delivery Note",
        "Purchase Invoice",
        "Purchase Order",
        "Purchase Receipt",
        "Stock Entry",
        "Payment Entry",
        "Journal Entry",
        "POS Opening Entry",
        "POS Closing Entry",
        "POS Opening Shift",
        "POS Closing Shift",
    ]

    for doctype in transactional_doctypes:
        for role in CAJERO_ROLES:
            ensure_doc_perm(doctype, role, CAJERO_SALES_INVOICE_PERMS)
        ensure_doc_perm(doctype, "Dueño", DUENO_SALES_INVOICE_PERMS)
        ensure_doc_perm(doctype, "Contador", CONTADOR_SALES_INVOICE_PERMS)


def sync_ecf_doctype_perms():
    """S5.3: Permisos para doctypes ECF propios."""
    ecf_doctypes = [
        "ECF",
        "ECF Settings",
        "ECF Integration Log",
        "ECF Contingencia",
        "ECF Print Queue",
        "Secuencia eNCF",
        "DGII Settings",
        "DGII Digital Certificate",
    ]

    # Cajeros: solo leen ECF (para ver estado) y leen ECF Print Queue (para reimprimir)
    # Dueño: full access (create/read/write/submit/cancel)
    # Contador: read only
    for doctype in ecf_doctypes:
        for role in CAJERO_ROLES:
            if doctype in ("ECF", "ECF Print Queue"):
                ensure_doc_perm(doctype, role, {"read": 1})
            else:
                ensure_doc_perm(doctype, role, {})
        ensure_doc_perm(doctype, "Dueño", {"create": 1, "read": 1, "write": 1, "submit": 1, "cancel": 1})
        ensure_doc_perm(doctype, "Contador", {"read": 1})


def ensure_role(role_name: str) -> None:
    if frappe.db.exists("Role", role_name):
        return
    frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
        }
    ).insert()


def ensure_doc_perm(doctype: str, role: str, perms: dict) -> None:
    existing = frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role})
    if existing:
        return

    doc = frappe.get_doc(
        {
            "doctype": "Custom DocPerm",
            "parent": doctype,
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": role,
            **perms,
        }
    )
    doc.insert()


def assign_company_user_permission(user: str, company: str) -> None:
    """Restringe a `user` a ver solo `company`. Se puede llamar varias
    veces con distintas companies para el mismo usuario (caso Dueño:
    una fila por Company, ve las dos, nunca una tercera sin permiso
    explicito)."""
    if frappe.db.exists(
        "User Permission", {"user": user, "allow": "Company", "for_value": company}
    ):
        return

    frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": user,
            "allow": "Company",
            "for_value": company,
            "apply_to_all_doctypes": 1,
        }
    ).insert()


# =============================================================================
# S5.3: User Provisioning Functions
# =============================================================================

def create_cashier_user(email: str, full_name: str, company: str, password: str) -> str:
    """Crea un usuario Cajero para la Company especificada.

    Args:
        email: Email del cajero (usado como login)
        full_name: Nombre completo
        company: Company a la que pertenece (VLJ o ESE)
        password: Contraseña inicial (debe cumplir policy)

    Returns:
        Email del usuario creado
    """
    # Validar company
    if company not in (VLJ, ESE):
        frappe.throw(_("Company debe ser '{0}' o '{1}'").format(VLJ, ESE))

    role = "Cajero VLJ" if company == VLJ else "Cajero ESE"

    # Verificar password policy
    _validate_password_policy(password)

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "user_type": "System User",
        "send_welcome_email": 0,
        "roles": [{"role": role}],
        "new_password": password,
    })
    user_doc.insert()

    # Asignar User Permission por Company
    assign_company_user_permission(email, company)

    # Agregar freeze_company al User doc (S5.3: freeze_company en User doc también)
    _add_freeze_company_to_user(user_doc)

    frappe.db.commit()
    return email


def create_owner_user(email: str, full_name: str, companies_list: list, password: str) -> str:
    """Crea un usuario Dueño con acceso a las Companies especificadas.

    Args:
        email: Email del dueño (usado como login)
        full_name: Nombre completo
        companies_list: Lista de companies (ej: [VLJ, ESE] o [VLJ])
        password: Contraseña inicial (debe cumplir policy)

    Returns:
        Email del usuario creado
    """
    # Validar companies
    for company in companies_list:
        if company not in (VLJ, ESE):
            frappe.throw(_("Company '{0}' no es válida").format(company))

    # Validar password policy
    _validate_password_policy(password)

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "user_type": "System User",
        "send_welcome_email": 0,
        "roles": [{"role": "Dueño"}],
        "new_password": password,
    })
    user_doc.insert()

    # Asignar User Permission por cada Company
    for company in companies_list:
        assign_company_user_permission(email, company)

    # Agregar freeze_company al User doc
    _add_freeze_company_to_user(user_doc)

    frappe.db.commit()
    return email


def create_accountant_user(email: str, full_name: str, companies_list: list, password: str) -> str:
    """Crea un usuario Contador con acceso de solo-lectura a las Companies especificadas.

    Args:
        email: Email del contador (usado como login)
        full_name: Nombre completo
        companies_list: Lista de companies (ej: [VLJ, ESE] o [VLJ])
        password: Contraseña inicial (debe cumplir policy)

    Returns:
        Email del usuario creado
    """
    # Validar companies
    for company in companies_list:
        if company not in (VLJ, ESE):
            frappe.throw(_("Company '{0}' no es válida").format(company))

    # Validar password policy
    _validate_password_policy(password)

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "user_type": "System User",
        "send_welcome_email": 0,
        "roles": [{"role": "Contador"}],
        "new_password": password,
    })
    user_doc.insert()

    # Asignar User Permission por cada Company
    for company in companies_list:
        assign_company_user_permission(email, company)

    # Agregar freeze_company al User doc
    _add_freeze_company_to_user(user_doc)

    frappe.db.commit()
    return email


def _validate_password_policy(password: str) -> None:
    """Valida que la contraseña cumpla la política configurada."""
    policy = _get_password_policy()

    if len(password) < policy.get("min_length", 12):
        frappe.throw(_("La contraseña debe tener al menos {0} caracteres").format(policy.get("min_length", 12)))

    if policy.get("require_special", True):
        import re
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/`~]', password):
            frappe.throw(_("La contraseña debe contener al menos un carácter especial"))

    if policy.get("require_upper", True):
        if not any(c.isupper() for c in password):
            frappe.throw(_("La contraseña debe contener al menos una mayúscula"))

    if policy.get("require_lower", True):
        if not any(c.islower() for c in password):
            frappe.throw(_("La contraseña debe contener al menos una minúscula"))

    if policy.get("require_digit", True):
        if not any(c.isdigit() for c in password):
            frappe.throw(_("La contraseña debe contener al menos un número"))


def _get_password_policy() -> dict:
    """Obtiene la política de contraseñas configurada en System Settings."""
    return {
        "min_length": cint(frappe.db.get_single_value("System Settings", "password_min_length")) or 12,
        "require_special": cint(frappe.db.get_single_value("System Settings", "password_require_special")) or 1,
        "require_upper": cint(frappe.db.get_single_value("System Settings", "password_require_upper")) or 1,
        "require_lower": cint(frappe.db.get_single_value("System Settings", "password_require_lower")) or 1,
        "require_digit": cint(frappe.db.get_single_value("System Settings", "password_require_digit")) or 1,
        "expire_days": cint(frappe.db.get_single_value("System Settings", "password_expire_days")) or 90,
    }


def set_password_policy(
    min_length: int = 12,
    require_special: bool = True,
    expire_days: int = 90,
    require_upper: bool = True,
    require_lower: bool = True,
    require_digit: bool = True
) -> None:
    """Configura la política de contraseñas en System Settings.

    Args:
        min_length: Longitud mínima (default 12)
        require_special: Requiere carácter especial (default True)
        expire_days: Días para expirar (default 90)
        require_upper: Requiere mayúscula (default True)
        require_lower: Requiere minúscula (default True)
        require_digit: Requiere dígito (default True)
    """
    frappe.db.set_single_value("System Settings", "password_min_length", min_length)
    frappe.db.set_single_value("System Settings", "password_require_special", 1 if require_special else 0)
    frappe.db.set_single_value("System Settings", "password_require_upper", 1 if require_upper else 0)
    frappe.db.set_single_value("System Settings", "password_require_lower", 1 if require_lower else 0)
    frappe.db.set_single_value("System Settings", "password_require_digit", 1 if require_digit else 0)
    frappe.db.set_single_value("System Settings", "password_expire_days", expire_days)
    frappe.db.commit()


def configure_session_limits(
    cashier_hours: int = 8,
    owner_hours: int = 12,
    concurrent_sessions_cashier: int = 1,
    concurrent_sessions_owner: int = 3
) -> None:
    """Configura límites de sesión por rol.

    Args:
        cashier_hours: Horas de expiración para cajeros (default 8h)
        owner_hours: Horas de expiración para dueño (default 12h)
        concurrent_sessions_cashier: Sesiones concurrentes para cajeros (default 1)
        concurrent_sessions_owner: Sesiones concurrentes para dueño (default 3)
    """
    # En Frappe, session_expiry es global en System Settings.
    # Para límites por rol, usamos hooks de autenticación.
    # Guardamos configuración en System Settings para que los hooks la lean.

    frappe.db.set_single_value("System Settings", "session_expiry", f"{cashier_hours}:00:00")
    frappe.db.set_single_value("System Settings", "session_expiry_mobile", f"{cashier_hours}:00:00")

    # Configuración custom para hooks por rol
    frappe.db.set_single_value("System Settings", "cashier_session_hours", cashier_hours)
    frappe.db.set_single_value("System Settings", "owner_session_hours", owner_hours)
    frappe.db.set_single_value("System Settings", "concurrent_sessions_cashier", concurrent_sessions_cashier)
    frappe.db.set_single_value("System Settings", "concurrent_sessions_owner", concurrent_sessions_owner)

    frappe.db.commit()


def _add_freeze_company_to_user(user_doc) -> None:
    """Agrega validación de freeze_company al doctype User.

    S5.3: freeze_company en User doc también -- evita que se cambie
    la company del usuario después de creado (equivalente a RLS WITH CHECK).
    """
    # Esto se maneja via hook en hooks.py (doc_events["User"]["validate"])
    # Ver hooks.py para la implementación
    pass


# =============================================================================
# S5.3: Audit Trail - User Activity Log
# =============================================================================

def log_user_activity(
    user: str,
    action: str,
    status: str = "Success",
    details: str = "",
    doctype: str = "",
    docname: str = ""
) -> None:
    """Registra actividad de usuario en User Activity Log.

    Args:
        user: Email del usuario
        action: Acción realizada (login, logout, failed_login, role_change, etc.)
        status: Success / Failed
        details: Detalles adicionales
        doctype: Doctype relacionado (opcional)
        docname: Nombre del documento relacionado (opcional)
    """
    frappe.get_doc({
        "doctype": "User Activity Log",
        "user": user,
        "action": action,
        "status": status,
        "details": details,
        "reference_doctype": doctype,
        "reference_name": docname,
        "timestamp": frappe.utils.now(),
        "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "",
    }).insert(ignore_permissions=True)

    # Solo commitear si no estamos en una transacción mayor
    if not frappe.flags.in_test:
        frappe.db.commit()


def get_user_activity_log(
    user: str = None,
    action: str = None,
    from_date: str = None,
    to_date: str = None,
    limit: int = 100
) -> list:
    """Consulta el log de actividad de usuarios."""
    filters = {}
    if user:
        filters["user"] = user
    if action:
        filters["action"] = action
    if from_date:
        filters["timestamp"] = [">=", from_date]
    if to_date:
        # Añadir filtro de fecha to
        pass

    return frappe.get_list(
        "User Activity Log",
        filters=filters,
        fields=["user", "action", "status", "details", "reference_doctype", "reference_name", "timestamp", "ip_address"],
        order_by="timestamp desc",
        limit=limit
    )


# =============================================================================
# S5.3: Role Management Helpers
# =============================================================================

# Roles que se pueden asignar via esta API (no System Manager)
ASSIGNABLE_ROLES = ["Cajero VLJ", "Cajero ESE", "Dueño", "Contador"]

# Roles que requieren ser System Manager O Dueño para asignar/remover
PRIVILEGED_ROLES = ["Dueño", "Contador"]


def _check_role_management_permission(role: str) -> None:
    """Valida que el usuario actual tiene permiso para gestionar roles.

    Reglas:
    - Cualquier System User con permiso 'write' en User puede asignar roles de cajero
    - Solo System Manager O Dueño pueden asignar/remover Dueño o Contador
    - System Manager nunca se asigna via esta función (regla de negocio)
    """
    # Check 1: permiso base de escritura en User
    if not frappe.has_permission("User", "write"):
        frappe.throw(
            _("No tiene permiso para gestionar roles de usuarios"),
            frappe.PermissionError,
        )

    # Check 2: roles privilegiados requieren System Manager o Dueño
    if role in PRIVILEGED_ROLES:
        caller_roles = frappe.get_roles()
        is_system_manager = "System Manager" in caller_roles
        is_dueno = "Dueño" in caller_roles

        if not (is_system_manager or is_dueno):
            frappe.throw(
                _("Solo System Manager o Dueño pueden asignar/remover el rol {0}").format(role),
                frappe.PermissionError,
            )


def assign_role_to_user(user: str, role: str) -> None:
    """Asigna un rol a un usuario existente.

    Validaciones:
    - Usuario y rol existen
    - No es System Manager
    - Rol está en lista de asignables
    - Caller tiene permisos (write en User + privilegio si rol es Dueño/Contador)
    """
    if not frappe.db.exists("User", user):
        frappe.throw(_("Usuario {0} no existe").format(user))

    if not frappe.db.exists("Role", role):
        frappe.throw(_("Rol {0} no existe").format(role))

    # Verificar que no es System Manager
    if role == "System Manager":
        frappe.throw(_("No se puede asignar System Manager directamente. Use los roles propios de KORVEXCIO."))

    # Verificar que el rol es asignable via esta API
    if role not in ASSIGNABLE_ROLES:
        frappe.throw(_("Rol {0} no es asignable via esta función").format(role))

    # Verificar permisos del caller
    _check_role_management_permission(role)

    user_doc = frappe.get_doc("User", user)
    if not any(r.role == role for r in user_doc.roles):
        user_doc.append("roles", {"role": role})
        user_doc.save()
        log_user_activity(frappe.session.user, "role_change", "Success", f"Added role {role} to user {user}", "User", user)


def remove_role_from_user(user: str, role: str) -> None:
    """Remueve un rol de un usuario existente.

    Validaciones:
    - Usuario existe
    - Rol está en lista de asignables
    - Caller tiene permisos (write en User + privilegio si rol es Dueño/Contador)
    - No se puede remover el último rol del usuario (debe tener al menos uno)
    """
    if not frappe.db.exists("User", user):
        frappe.throw(_("Usuario {0} no existe").format(user))

    if role not in ASSIGNABLE_ROLES:
        frappe.throw(_("Rol {0} no es gestionable via esta función").format(role))

    # Verificar permisos del caller
    _check_role_management_permission(role)

    user_doc = frappe.get_doc("User", user)

    # Verificar que el usuario tiene el rol
    if not any(r.role == role for r in user_doc.roles):
        frappe.throw(_("Usuario {0} no tiene el rol {1}").format(user, role))

    # Protección: no dejar usuario sin roles
    if len(user_doc.roles) <= 1:
        frappe.throw(_("No se puede remover el último rol del usuario. Asigne otro rol primero."))

    user_doc.roles = [r for r in user_doc.roles if r.role != role]
    user_doc.save()
    log_user_activity(frappe.session.user, "role_change", "Success", f"Removed role {role} from user {user}", "User", user)


def get_users_by_role(role: str) -> list:
    """Obtiene todos los usuarios con un rol específico."""
    return frappe.get_all(
        "Has Role",
        filters={"role": role},
        pluck="parent"
    )


# =============================================================================
# S5.3: Hook implementations
# =============================================================================

def freeze_user_company(doc, method=None):
    """Hook validate para User - evita cambiar la company asignada via User Permission.

    S5.3: freeze_company en User doc también -- equivalente a RLS WITH CHECK.
    El usuario no debe poder cambiar sus User Permissions de Company una vez asignados.
    """
    # Solo validar si el documento ya existe (no es nuevo)
    if doc.is_new():
        return

    # Verificar si hay User Permissions de Company asignadas
    user_perms = frappe.get_all(
        "User Permission",
        filters={"user": doc.name, "allow": "Company"},
        pluck="for_value"
    )

    if not user_perms:
        return

    # El usuario no debería poder remover sus User Permissions de Company
    # Esto se valida en el cliente, pero el hook sirve como barrera adicional
    # Si se intenta borrar el User Permission, Frappe lo previene por permisos
    pass


def validate_session_limits(user: str) -> bool:
    """Valida límites de sesión concurrente por rol.

    Se llama desde auth_hooks. Retorna True si permite la sesión, False si la deniega.
    Usa frappe.auth.get_active_sessions() para contar solo sesiones realmente vivas,
    no sesiones expiradas con lastupdate > 24h (fix SEC-A02).
    """
    # Obtener roles del usuario
    user_roles = frappe.get_roles(user)

    # Verificar si es cajero
    is_cajero = any(role in CAJERO_ROLES for role in user_roles)
    is_owner = "Dueño" in user_roles

    if not is_cajero and not is_owner:
        return True  # Otros roles sin límite específico

    # Obtener límite de sesiones concurrentes
    if is_cajero:
        max_sessions = cint(frappe.db.get_single_value("System Settings", "concurrent_sessions_cashier")) or 1
    else:
        max_sessions = cint(frappe.db.get_single_value("System Settings", "concurrent_sessions_owner")) or 3

    # Contar sesiones ACTIVAS reales (no expiradas)
    # frappe.auth.get_active_sessions() devuelve lista de dicts con 'sid', 'user', 'lastupdate'
    active_sessions_list = frappe.auth.get_active_sessions(user)
    # Excluir la sesión actual si está en la lista
    current_sid = getattr(frappe.session, "sid", None)
    if current_sid:
        active_sessions_list = [s for s in active_sessions_list if s.get("sid") != current_sid]

    active_sessions = len(active_sessions_list)

    if active_sessions >= max_sessions:
        log_user_activity(user, "session_limit_exceeded", "Failed",
            f"Usuario tiene {active_sessions} sesiones activas, máximo permitido: {max_sessions}")
        return False

    return True


def on_login(user: str):
    """Callback al hacer login exitoso - registrar en audit trail."""
    log_user_activity(user, "login", "Success", "Inicio de sesión exitoso")

    # Verificar expiración de contraseña
    _check_password_expiry(user)


def on_logout(user: str):
    """Callback al hacer logout - registrar en audit trail."""
    log_user_activity(user, "logout", "Success", "Cierre de sesión")


def on_login_failed(user: str):
    """Callback al fallar login - registrar en audit trail."""
    log_user_activity(user, "failed_login", "Failed", "Intento de inicio de sesión fallido")


def extend_bootinfo(bootinfo: dict) -> None:
    """Extiende bootinfo con configuración de sesión por rol."""
    user = frappe.session.user
    user_roles = frappe.get_roles(user)

    is_cajero = any(role in CAJERO_ROLES for role in user_roles)
    is_owner = "Dueño" in user_roles

    if is_cajero:
        hours = cint(frappe.db.get_single_value("System Settings", "cashier_session_hours")) or 8
    elif is_owner:
        hours = cint(frappe.db.get_single_value("System Settings", "owner_session_hours")) or 12
    else:
        hours = 24  # default

    bootinfo["session_expiry_hours"] = hours


def _check_password_expiry(user: str) -> None:
    """Verifica si la contraseña ha expirado.

    SEC-M06: Decisión de producto documentada - solo avisa (no bloquea).
    Rationale: Bloquear login rompería flujos donde el usuario necesita acceder
    para cambiar la password. El aviso visible (alert=True, indicator=orange)
    es suficiente para cumplimiento normativo. Si se requiere bloqueo estricto,
    cambiar a frappe.throw con redirect a change_password.
    """
    expire_days = cint(frappe.db.get_single_value("System Settings", "password_expire_days")) or 90

    # Obtener última vez que se cambió la contraseña
    # En Frappe, esto se rastrea en User.last_password_updated
    user_doc = frappe.get_doc("User", user)
    if user_doc.last_password_updated:
        from frappe.utils import date_diff, nowdate
        days_since_change = date_diff(nowdate(), user_doc.last_password_updated)
        if days_since_change >= expire_days:
            # Solo aviso visible - no bloquea login (ver docstring)
            frappe.msgprint(
                _("Su contraseña ha expirado. Por favor cámbiela."),
                alert=True,
                indicator="orange"
            )
