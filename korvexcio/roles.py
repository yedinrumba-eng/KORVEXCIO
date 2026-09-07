"""korvexcio.roles - User provisioning, permissions, audit trail, session limits.

FASE 4.8: Este archivo ahora es solo un re-export del módulo dividido.
Los módulos reales están en:
- roles_provisioning.py: User provisioning (create_cashier_user, create_owner_user, create_accountant_user, password policy, session limits config)
- roles_permissions.py: Roles/permissions sync (sync_roles, ensure_role, ensure_doc_perm, assign_company_user_permission)
- roles_audit.py: Audit trail + role management (log_user_activity, get_user_activity_log, assign_role_to_user, remove_role_from_user, freeze_user_company)
- roles_session.py: Session limits + auth hooks (validate_session_limits, on_login, on_logout, on_login_failed, extend_bootinfo, _check_password_expiry)
"""

from __future__ import annotations

# Provisioning
from .roles_provisioning import (
    create_cashier_user,
    create_owner_user,
    create_accountant_user,
    _validate_password_policy,
    _get_password_policy,
    set_password_policy,
    configure_session_limits,
)

# Permissions
from .roles_permissions import (
    VLJ,
    ESE,
    ROLES,
    CAJERO_ROLES,
    DUENO_USER_PERMS,
    BASIC_READ,
    CAJERO_SALES_INVOICE_PERMS,
    DUENO_SALES_INVOICE_PERMS,
    CONTADOR_SALES_INVOICE_PERMS,
    DUENO_POS_PROFILE_PERMS,
    CAJERO_CASH_SHIFT_PERMS,
    DUENO_CASH_SHIFT_PERMS,
    CONTADOR_CASH_SHIFT_PERMS,
    sync_roles,
    sync_transactional_doctype_perms,
    sync_ecf_doctype_perms,
    ensure_role,
    ensure_doc_perm,
    assign_company_user_permission,
)

# Audit + Role management
from .roles_audit import (
    PRIVILEGED_ROLES,
    _check_role_management_permission,
    assign_role_to_user,
    remove_role_from_user,
    get_users_by_role,
    freeze_user_company,
    log_user_activity,
    get_user_activity_log,
)

# Session + Auth hooks
from .roles_session import (
    validate_session_limits,
    on_login,
    on_logout,
    on_login_failed,
    extend_bootinfo,
    _check_password_expiry,
)

__all__ = [
    # Provisioning
    "create_cashier_user",
    "create_owner_user",
    "create_accountant_user",
    "_validate_password_policy",
    "_get_password_policy",
    "set_password_policy",
    "configure_session_limits",
    # Permissions
    "VLJ",
    "ESE",
    "ROLES",
    "CAJERO_ROLES",
    "DUENO_USER_PERMS",
    "BASIC_READ",
    "CAJERO_SALES_INVOICE_PERMS",
    "DUENO_SALES_INVOICE_PERMS",
    "CONTADOR_SALES_INVOICE_PERMS",
    "DUENO_POS_PROFILE_PERMS",
    "CAJERO_CASH_SHIFT_PERMS",
    "DUENO_CASH_SHIFT_PERMS",
    "CONTADOR_CASH_SHIFT_PERMS",
    "sync_roles",
    "sync_transactional_doctype_perms",
    "sync_ecf_doctype_perms",
    "ensure_role",
    "ensure_doc_perm",
    "assign_company_user_permission",
    # Audit + Role management
    "PRIVILEGED_ROLES",
    "_check_role_management_permission",
    "assign_role_to_user",
    "remove_role_from_user",
    "get_users_by_role",
    "freeze_user_company",
    "log_user_activity",
    "get_user_activity_log",
    # Session + Auth hooks
    "validate_session_limits",
    "on_login",
    "on_logout",
    "on_login_failed",
    "extend_bootinfo",
    "_check_password_expiry",
]