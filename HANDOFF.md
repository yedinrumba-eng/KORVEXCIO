# HANDOFF — KORVEXCIO (cliente 1: VAPELAND)

> **Estado vigente — 2026-09-07 (actualizado post security-review follow-up):**
>
> ### ✅ FASES 1-4 COMPLETAS (excepto S4.4 hardware, S4.6 local real)
> - **Fase 0** (S0.1-S0.12): Cerrada (S0.9/S0.3 deuda técnica por D20)
> - **Fase 1** (S1.1-S1.8): Cerrada 31/08
> - **Fase 2** (S2.1-S2.15): Estructura completa, 91 tests, auditada — **gate real bloqueado en S2.7** (proveedor real necesita RNC+certificado)
> - **Fase 3** (S3.1-S3.6): Cerrada 01/09, 108 tests — 3 bugs críticos corregidos (permisos Sales Invoice, fuga datos reportes, BOM sin company)
> - **Fase 4** (S4.1-S4.5): Cerrada en remoto — **S4.4 hardware / S4.6 local real bloqueados**
>
> ### ✅ POSNext fork (`yedinrumba-eng/posnext`, rama `korvex`)
> - **S4.UI.1**: Login visual KORVEXCIO commitado (`819fd2f`) — 8 tests Vitest, build Windows OK
> - **S4.2b**: Mensaje fiscal real en POSNext commitado (`8acd1a6`) — detecta "Norma 05-19"/"RNC del comprador" → "RNC Requerido" con retry
> - **S4.1**: POS Profile por Company — 111/111 tests
> - **S4.2**: Fork instalado, venta real E32 generada, umbral RD$250k probado en pantalla
> - **S4.3**: Escáner keyboard-wedge nativo — 0 código, 0 config
> - **S4.5**: Turno de caja / arqueo — 118/118 tests
> - **S4.4/S4.6**: Bloqueados (hardware físico + local real del cliente)
>
> ### ✅ CODE REVIEW + SECURITY REVIEW COMPLETADOS (2026-09-05)
> **18 fixes aplicados** (commits `3d4f11b` a `9c0f7eb`):
>
> **🔴 3 CRÍTICOS (SEC-A01, A02, A03):**
> - `3d4f11b` SEC-A01: `assign_role_to_user/remove_role_from_user` validan permisos (write en User + privilegio Dueño/Contador)
> - `43d6c6b` SEC-A02: `validate_session_limits()` usa `get_active_sessions()` — no cuenta sesiones expiradas
> - `67764fa` SEC-A03: Test aislamiento `ecf.insert(ignore_permissions=True)` → `test_scenario_13`
>
> **🟡 1 LEGAL:**
> - `dba0166` LICENSE MIT → GPL-3.0 (app deriva de ERPNext GPLv3)
>
> **🟡 6 MEDIOS SEGURIDAD (SEC-M01 a M07):**
> - `e588567` SEC-M01-M04: Cola impresión en `poll_pending_status()` (cuando hay QR), locks Redis en crons, paginación batch=100, verifica jobs existentes
> - `04d1328` SEC-M07: `_upsert_item_price()` valida Price List existe para company
> - `6897927` SEC-M06: `_check_password_expiry()` decisión documentada: solo avisa, no bloquea
>
> **⚪ 8 BAJOS/CODE REVIEW:**
> - `9c0f7eb` SEC-M08: `pyserial` en pyproject.toml
> - `8d8ebc4` SEC-L07: `resolve_provider()` loggea error si proveedor sin implementación
> - `b596603` SEC-L02: Eliminar `test_thermal_print()` falso → `_dev_test_thermal_print()`
> - `4769169` SEC-L05: Emails únicos en tests con `frappe.generate_hash()`
> - `c243f3f` CR-31: Documentar timeout max 300s en DGII Settings
> - `7f49e60` CR-34: `get_pending_prints(include_failed=True)` para UI requeue
> - `4769169` SEC-L05: Emails únicos en `test_roles_permissions` con `generate_hash()`
> - `b596603` SEC-L02: Renombrar test falso a `_dev_test_thermal_print()`
>
> **Tests totales:** 148+ integration + unit verdes, 0 regresiones
> **Semgrep:** 0 hallazgos nuevos (2 justificados desde S2.10)
> **Ruff:** 6 deuda vieja (DTZ011×5, BLE001×1), 0 nuevos
> **`ignore_permissions`/SQL crudo sin justificar:** 0
>
> ---
>
> **Siguiente inmediato: S5.4 (Certificación DGII 2 RNC) — BLOQUEADO por RNC+certificado real.**
> Cuando Yedin tenga RNC + certificado: S5.4 → S2.7 (proveedor real) → Fase 6 (go-live local).
> S4.4 (impresora física) y S4.6 (contingencia local real) esperan hardware/local.
>
> **Actualización 2026-09-07 — SECURITY REVIEW FOLLOW-UP COMPLETADO:**
> **10 broad exceptions (BLE001/DTZ011) fixados en código no-test** (commit `a03a52a`):
> - `tasks.py:167` — `except Exception` → `except ElementTree.ParseError`
> - `validate_ecf_xsd.py:38,67,101` — 4 broad except → específicos
> - `print_queue_offline.py:122` — `except Exception` → específicos
> - `roles_audit.py:193` — `except Exception` → `# noqa: BLE001` con comentario
> - `bulk_import_cli.py:67,101` — 2 broad except → específicos
> - `tasks.py:32` — Import `ElementTree` agregado
>
> **Total: 10 broad exceptions eliminados en código no-test**
>
> **Actualización 2026-09-08 — FASE 5.3 COMPLETADA:**
> Migración de fixtures a setUp/tearDown aisladas con `generate_hash(8)` en 9 tests — **TODOS COMMITEADOS** (`a2f9f42`):
> 1. `test_roles_permissions.py` — **COMPLETADO** (prioridad 1)
> 2. `test_fefo.py` — **COMPLETADO** (prioridad 2)
> 3. `test_age_verification.py` — **COMPLETADO** (prioridad 3)
> 4. `test_item_attributes.py` — **COMPLETADO** (prioridad 4)
> 5. `test_bulk_import.py` — **COMPLETADO** (prioridad 5)
> 6. `test_isolation.py` — **COMPLETADO + COMMITEADO** `eceafd3` (prioridad 6)
> 7. `test_sales_invoice_hooks.py` — **COMPLETADO + COMMITEADO** `eceafd3` (prioridad 7)
> 8. `test_print_format.py` — **COMPLETADO + COMMITEADO** `a2f9f42` (prioridad 8)
> 9. `test_tasks.py` — **COMPLETADO + COMMITEADO** `a2f9f42` (prioridad 9)
>
> **Patrón validado en `test_thermal_print.py`:** `setUp` con `generate_hash(8)` + `tearDown` completo + cleanup orden inverso + except específicos `(frappe.DoesNotExistError, frappe.ValidationError)`.

---

## 🔴 BLOQUEANTES REALES (requieren Yedin/hardware)

| Slice | Qué necesita | Quién |
|-------|--------------|-------|
| **S2.7** | Proveedor real (Alanube/ECF SSD) | Yedin → RNC + certificado |
| **S5.4** | Certificación DGII (2 RNC) | Yedin → RNC + certificado + CerteCF |
| **S4.4** | Impresora térmica + QZ Tray | Hardware en local |
| **S4.6** | Contingencia internet real local | Local cliente (gate Fase 6) |

---

## 🟡 TRABAJO INTERNO DISPONIBLE AHORA (sin blockers)

| Prioridad | Qué | Esfuerzo |
|-----------|-----|----------|
| **1** | **FASE 5.3** - Fixtures aisladas en 9 tests | ~3-4h |
| **2** | **S5.2** - Script `create_initial_stock_entries.py` | ~2h |
| **3** | **Ruff debt** - 6 hallazgos viejos (DTZ011×5, BLE001×1) | ~2h |
| **4** | **Docs XSD** - Documentar procedimiento XSD oficial | 30 min |

---

## 📋 PLAN RECOMENDADO PRÓXIMOS 2-3 DÍAS

| Día | Foco | Entregable |
|-----|------|------------|
| **1** | **FASE 5.3** - `test_roles_permissions.py` + `test_fefo.py` + `test_age_verification.py` | 3 tests con fixtures aisladas |
| **2** | **FASE 5.3** - `test_item_attributes.py` + `test_bulk_import.py` + `test_isolation.py` | 3 tests más |
| **3** | **FASE 5.3** - `test_sales_invoice_hooks.py` + `test_print_format.py` + `test_tasks.py` | 3 tests + **S5.2** script Stock Entry |
| **4** | Ruff debt (6 hallazgos viejos) + Docs XSD | Lint limpio + procedimiento XSD |

---

## 🎯 PRÓXIMO PASO INMEDIATO: FASE 5.3 — `test_roles_permissions.py`

**Patrón ya validado en `test_thermal_print.py`:**
- `setUp` con `generate_hash(8)` para sufijo único por test
- `tearDown` completo con cleanup orden inverso (ECF → Sales Invoice → Print Queue → Customer → Item)
- Except específicos: `(frappe.DoesNotExistError, frappe.ValidationError)`
- Datos únicos por test: `customer_name = f"_Test Customer {self.test_hash}"`, `item_code = f"_Test Item {self.test_hash}"`
- Cleanup en orden inverso de dependencias
- Except específicos: `(frappe.DoesNotExistError, frappe.ValidationError)`

---

## 📁 ARCHIVOS CLAVE A TOCAR PRÓXIMO

| Archivo | Qué hacer |
|---------|-----------|
| `korvexcio/tests/test_roles_permissions.py` | **EN PROGRESO** - Migrar `setUpClass` → `setUp` con `generate_hash(8)` |
| `korvexcio/retail/test_fefo.py` | Migrar fixtures |
| `korvexcio/retail/test_age_verification.py` | Migrar fixtures |
| `korvexcio/retail/test_item_attributes.py` | Migrar fixtures |
| `korvexcio/retail/test_bulk_import.py` | Migrar fixtures |
| `korvexcio/tests/test_isolation.py` | Migrar fixtures (usa `before_tests()`) |
| `korvexcio/ecf/test_sales_invoice_hooks.py` | Migrar fixtures |
| `korvexcio/ecf/test_print_format.py` | Migrar fixtures |
| `korvexcio/ecf/test_tasks.py` | Migrar fixtures |
| **NUEVO** `korvexcio/retail/stock_initial.py` | Script S5.2: Stock Entry por almacén (idempotente, rollback) |

---

## 🔑 PATRÓN YA VALIDADO (test_thermal_print.py)

```python
def setUp(self):
    frappe.set_user("Administrator")
    if not frappe.local.lang:
        frappe.local.lang = "en"
    from korvexcio.install import before_tests
    before_tests()
    
    # Sufijo único por test
    self.test_hash = frappe.generate_hash(8)
    self.company = "_Test Company KORVEXCIO A"
    self.abbr = "_TCKA"
    self.customer_name = f"_Test Customer {self.test_hash}"
    self.item_code = f"_Test Item {self.test_hash}"
    
    # Crear customer único
    self.customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": self.customer_name,
        "customer_group": "Commercial",
        "territory": "All Territories",
    }).insert()

    # Crear item único
    self.item = frappe.get_doc({
        "doctype": "Item",
        "item_code": self.item_code,
        "item_name": self.item_code,
        "item_group": "All Item Groups",
        "is_stock_item": 0,
        "stock_uom": "Nos",
    }).insert()

    # Asegurar secuencia E32 para company
    seq_name = f"{self.company}-E32"
    if not frappe.db.exists("Secuencia eNCF", seq_name):
        frappe.get_doc({
            "doctype": "Secuencia eNCF",
            "company": self.company,
            "tipo_ecf": "E32",
            "desde": 1,
            "hasta": 999999,
            "siguiente": 1,
            "fecha_vencimiento": "2027-12-31",
        }).insert()

def tearDown(self):
    frappe.set_user("Administrator")
    # Cleanup en orden inverso de dependencias
    try:
        # ECFs
        for ecf_name in frappe.get_all("ECF", filters={"reference_doctype": "Sales Invoice"}, pluck="name"):
            try:
                doc = frappe.get_doc("ECF", ecf_name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("ECF", ecf_name, force=True, ignore_permissions=True)
            except (frappe.DoesNotExistError, frappe.ValidationError):
                pass
        # ... resto cleanup orden inverso
    except (frappe.DoesNotExistError, frappe.ValidationError):
        pass
```

---

## 📍 Punto exacto para reanudar

**Rama:** `feat/ecf` (17 commits ahead de `origin/feat/ecf`)
**Último commit:** `a03a52a` — Security review follow-up BLE001/DTZ011 fixes
**Estado FASE 5.3:** `test_roles_permissions.py` **EN PROGRESO** — migrar `setUpClass` → `setUp` con `generate_hash(8)`

**Para reanudar:**
1. Leer `korvexcio/tests/test_roles_permissions.py` (actual, usa `setUpClass`)
2. Aplicar patrón `setUp`/`tearDown` con `generate_hash(8)` como en `test_thermal_print.py`
3. Verificar sintaxis: `python -m py_compile korvexcio/tests/test_roles_permissions.py`
4. Commit: `test: FASE 5.3 - fixtures aisladas test_roles_permissions`