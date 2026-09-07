# PLAN DE FIXES — CODE REVIEW + SECURITY REVIEW

**Fecha:** 2026-09-05
**Objetivo:** Resolver todos los hallazgos accionables (no bloqueados por dependencias externas) de ambas auditorías
**Alcance:** 3 Altos + 12 Medios + 7 Bajos + 5 items de code review = **27 fixes aplicables ahora**
**Fuera de alcance (blockers externos):** Proveedor real e-CF (S2.7), XSD DGII, Hardware térmica, RNC/certificado cliente

---

## PRIORIZACIÓN Y ORDEN DE EJECUCIÓN

### FASE 1 — CRÍTICOS DE SEGURIDAD (3 Altos) — **Esta semana**
*Bloquean go-live con datos reales. Fixes quirúrgicos, bien localizados.*

| # | ID | Archivo:Línea | Acción | Test Requerido | Estimado |
|---|----|---------------|--------|----------------|----------|
| 1.1 | SEC-A01 | `korvexcio/roles.py:516-543` | Agregar check `frappe.has_permission("User", "write")` en `assign_role_to_user()` y `remove_role_from_user()`; restringir a `System Manager` + `Dueño` | Test: Cajero intenta escalar → `PermissionError` | 30 min |
| 1.2 | SEC-A02 | `korvexcio/roles.py:585-617` | Reescribir `validate_session_limits()`: usar `frappe.auth.get_active_sessions(user)` o filtrar `Session` por `sid` viva real, no `lastupdate > 24h` | Test: Login 2x rápido → no bloquear; sesión expirada real → no contar | 1 h |
| 1.3 | SEC-A03 | `korvexcio/ecf/sales_invoice_hooks.py:122` | Crear test dedicado `test_ecf_created_by_cashier_stays_company_scoped` en `tests/test_ecf_isolation.py` | Test: Cajero A encola venta → ECF creado en Company A, no B | 1 h |

---

### FASE 2 — DEUDA RAÍZ LEGAL (1 item) — **Inmediato (5 min)**

| # | ID | Archivo | Acción | Estimado |
|---|----|---------|--------|----------|
| 2.1 | SEC-L01 / CR-LICENSE | Root `LICENSE` | Cambiar `MIT` → `GPL-3.0` (app deriva de ERPNext GPLv3) | 5 min |

---

### FASE 3 — MEDIOS DE SEGURIDAD (6 items) — **Próximo sprint**

| # | ID | Archivo:Línea | Acción | Test Requerido | Estimado |
|---|----|---------------|--------|----------------|----------|
| 3.1 | SEC-M01 | `korvexcio/ecf/sales_invoice_hooks.py:137-144` + `tasks.py:228-262` | Mover encolado impresión a `poll_pending_status()` cuando `track_id` existe; agregar campo `has_qr` en `ECF Print Queue` | Test: Venta sin QR → no encola impresión; tras `poll` con QR → encola | 2 h |
| 3.2 | SEC-M02 | `korvexcio/ecf/tasks.py:216-225` | En `retry_pending_ecf()`: verificar jobs existentes en Redis queue (`rq`) antes de encolar duplicados | Test: Cron corre 2x → solo 1 job por ECF | 1 h |
| 3.3 | SEC-M03 | `korvexcio/ecf/tasks.py:228-262` | Agregar `limit=100` + paginación con cursor en `poll_pending_status()` | Test: 500 ECF con track_id → procesa en batches de 100 | 1 h |
| 3.4 | SEC-M04 | `korvexcio/tasks.py:216-262` + `hooks.py:215-221` | Agregar lock Redis `frappe.cache().lock("korvexcio:ecf:cron:{name}", timeout=300)` en `retry_pending_ecf` y `poll_pending_status` | Test: Cron solapado → segundo espera/skipea | 1 h |
| 3.5 | SEC-M07 | `korvexcio/retail/bulk_import.py:348-368` | En `_upsert_item_price()`: validar `frappe.db.exists("Price List", {"name": price_list, "company": company})` antes de insertar | Test: Price List inexistente → error claro, no price huérfano | 30 min |
| 3.6 | SEC-M06 | `korvexcio/roles.py:656-672` | `_check_password_expiry()`: decidir y documentar — **opción A**: bloquear con `frappe.throw` + redirect a change_password; **opción B**: mantener aviso pero documentar por qué no bloquea | Test: Password expirado → comportamiento según decisión | 30 min |

---

### FASE 4 — MEJORAS DE CALIDAD / ARQUITECTURA (8 items) — **Sprints de mantenimiento**

| # | ID | Archivo:Línea | Acción | Estimado |
|---|----|---------------|--------|----------|
| 4.1 | SEC-M12 / CR-14 | `korvexcio/retail/reports.py` + `dashboard.py` | Crear decorator `@require_company_access` o mixin `CompanyScopedQuery` para centralizar `_assert_user_may_view_company()` | 2 h |
| 4.2 | SEC-M09 | `korvexcio/ecf/thermal_print.py:293-330` | Parametrizar comandos ESC/POS QR por `printer_model` en `POS Profile` (Epson/Star/Bixolon/Custom) | 4 h |
| 4.3 | SEC-M11 | `korvexcio/ecf/templates/ecf.xml` + `rfce.xml` | **Preparar validación XSD**: descargar XSD oficial DGII cuando Yedin tenga acceso; agregar script `validate_ecf_xsd.py` usando `lxml.etree.XMLSchema` | 2 h (cuando XSD disponible) |
| 4.4 | SEC-L03 | `korvexcio/ecf/thermal_print.py:17-23` | Mover constantes impresora a `ECF Print Settings` DocType o `POS Profile` (width_dots, char_width, char_height) | 1 h |
| 4.5 | SEC-L04 | `korvexcio/ecf/thermal_print.py:571-638` | Extraer `_get_ecf_data(invoice_name)` helper para eliminar duplicación entre `generate_thermal_receipt_html` y `generate_thermal_receipt_escpos` | 30 min |
| 4.6 | SEC-M08 | `korvexcio/ecf/print_queue.py:126-134` | Agregar `pyserial` a `pyproject.toml` + `try/except ImportError` con log claro en `_send_to_printer()` | 15 min |
| 4.7 | SEC-L07 | `korvexcio/ecf/providers/registry.py:17-23` | En `resolve_provider()`: si `provider_class is None` y `provider_name` configurado → `frappe.log_error` con contexto | 15 min |
| 4.8 | CR-25 a CR-28 | `thermal_print.py` (679), `print_queue.py` (294), `roles.py` (672), `bulk_import.py` (489) | **Separar god modules** en slices dedicados (ver tabla abajo) | 8-16 h total |

#### Sub-plan: Separación de God Modules (4.8)

| Archivo Actual | División Propuesta | Archivos Nuevos |
|----------------|-------------------|-----------------|
| `thermal_print.py` (679) | Builder + API + Test helpers | `thermal_receipt_builder.py`, `thermal_print_api.py`, `test_helpers.py` |
| `print_queue.py` (294) | Server queue + POS API + Offline sync | `print_queue_server.py`, `print_queue_pos_api.py`, `print_queue_offline.py` |
| `roles.py` (672) | Provisioning + Permissions + Audit + Sessions | `roles_provisioning.py`, `roles_permissions.py`, `roles_audit.py`, `roles_session.py` |
| `bulk_import.py` (489) | Parser + Builder + Defaults + CLI | `bulk_import_parser.py`, `bulk_import_builder.py`, `bulk_import_defaults.py`, `bulk_import_cli.py` |

---

### FASE 5 — TESTING / OBSERVABILIDAD (5 items) — **Paralelo a Fase 4**

| # | ID | Archivo:Línea | Acción | Estimado |
|---|----|---------------|--------|----------|
| 5.1 | SEC-L02 | `korvexcio/ecf/thermal_print.py:658-676` | Eliminar `test_thermal_print()` falso o mover a `test_thermal_print.py` como `IntegrationTestCase` real | 30 min |
| 5.2 | SEC-L05 | `korvexcio/tests/test_roles_permissions.py:30-33` | Generar emails únicos: `f"{role}_{frappe.generate_hash(8)}@korvexdev.cc"` en `setUp` | 30 min |
| 5.3 | SEC-L06 | `korvexcio/ecf/test_thermal_print.py:75-78` | Migrar fixtures a `setUp`/`tearDown` por test o usar `frappe.test_fixtures` | 1 h |
| 5.4 | CR-31 | `korvexcio/ecf/doctype/dgii_settings/dgii_settings.py` | Documentar por qué timeout max 300s (comentario en código) | 10 min |
| 5.5 | CR-34 | `korvexcio/ecf/doctype/ecf_print_queue/ecf_print_queue.py:27-28` | Agregar filtro opcional `include_failed` en `get_pending_prints()` | 15 min |

---

## DEPENDENCIAS ENTRE FIXES

```
FASE 1 (Sec-A01, Sec-A02, Sec-A03)
    ↓ (independientes, pueden paralelizarse)
FASE 2 (License)
    ↓ (independiente)
FASE 3 (Sec-M01 a Sec-M06)
    ├── Sec-M01 requiere FASE 1.3 (test aislamiento ECF) ✓
    ├── Sec-M02, Sec-M03, Sec-M04 independientes entre sí
    └── Sec-M07 independiente
    ↓
FASE 4 (Calidad/Arquitectura)
    ├── 4.1 (decorator) ayuda a 4.8 (roles_permissions.py)
    └── 4.8 (separación) facilita 4.2, 4.4, 4.5
    ↓
FASE 5 (Testing) - puede ir en paralelo desde FASE 3
```

---

## COMANDOS DE VERIFICACIÓN POST-CADA-FIX

```bash
# Después de CADA fix individual:
cd /home/korvex/frappe_docker-korvexcio-s05  # en nodo
git fetch && git reset --hard origin/feat/ecf
docker compose -p korvexcio restart backend queue-short queue-long scheduler websocket
bench --site korvexcio.korvexdev.cc migrate
bench --site korvexcio.korvexdev.cc run-tests --app korvexcio --test-category all
# → Debe dar OK (skipped=1) sin regresiones

# Verificaciones específicas por fase:
# FASE 1: bench run-tests --module korvexcio.tests.test_roles_permissions
# FASE 1.3: bench run-tests --module korvexcio.tests.test_ecf_isolation
# FASE 3.1: bench run-tests --module korvexcio.ecf.test_thermal_print
# FASE 3.4: Verificar que crons no solapan (logs /home/korvex/frappe-bench/logs/scheduler.log)
```

---

## CHECKLIST DE EJECUCIÓN

### FASE 1 — Seguridad Crítica
- [ ] 1.1 Fix `assign_role_to_user()` permisos
- [ ] 1.2 Fix `validate_session_limits()` sesiones reales
- [ ] 1.3 Test aislamiento `ecf.insert(ignore_permissions=True)`

### FASE 2 — Legal
- [ ] 2.1 `LICENSE` → `GPL-3.0`

### FASE 3 — Medios Seguridad
- [ ] 3.1 Mover encolado impresión a `poll_pending_status()`
- [ ] 3.2 `retry_pending_ecf()` verificar jobs existentes
- [ ] 3.3 `poll_pending_status()` paginación + limit
- [ ] 3.4 Lock Redis en crons
- [ ] 3.5 Validar Price List en bulk_import
- [ ] 3.6 Decidir/documentar `_check_password_expiry()`

### FASE 4 — Calidad/Arquitectura
- [ ] 4.1 Decorator `@require_company_access`
- [ ] 4.2 Parametrizar ESC/POS por modelo impresora
- [ ] 4.3 Preparar validación XSD (esperar XSD)
- [ ] 4.4 Constantes impresora en DocType
- [ ] 4.5 Helper `_get_ecf_data()`
- [ ] 4.6 `pyserial` en pyproject.toml
- [ ] 4.7 Log error en `resolve_provider()`
- [ ] 4.8 Separar god modules (4 sub-slices)

### FASE 5 — Testing/Observabilidad
- [ ] 5.1 Fix/eliminar `test_thermal_print()` falso
- [ ] 5.2 Emails únicos en test_roles_permissions
- [ ] 5.3 Fixtures aisladas en test_thermal_print
- [ ] 5.4 Documentar timeout 300s en dgii_settings
- [ ] 5.5 Filtro `include_failed` en get_pending_prints

---

## MÉTRICAS DE ÉXITO

| Métrica | Target |
|---------|--------|
| **Tests totales** | ≥ 150 (actual 148) sin regresiones |
| **Semgrep hallazgos nuevos** | 0 |
| **Ruff hallazgos nuevos** | 0 (solo los 6 deuda vieja) |
| **`ignore_permissions=True` sin justificar** | 0 |
| **`frappe.db.sql()` crudo** | 0 |
| **Cobertura aislamiento D19** | 12/12 escenarios (actual 8/12 + 4 skip) |
| **Tiempo crons** | < 30s cada uno (actual puede solaparse) |
| **God modules** | 0 archivos > 300 líneas (actual 4) |

---

## NOTAS DE EJECUCIÓN

1. **Un fix por commit** — mensaje convencional: `fix: <área> — <descripción corta>`
2. **Push a `origin/feat/ecf`** — no a `main` (regla blueprint: merge solo en gates de fase)
3. **Verificar en nodo real** — Windows no tiene Frappe, tests locales no aplican
4. **KORVIS debe seguir sano** — `curl http://127.0.0.1:4000/health` después de cada deploy
5. **Documentar en PROGRESO.md** — cada fix cerrado con salida real de verificación

---

## PRÓXIMO PASO INMEDIATO

**Empezar con FASE 1.1** — `assign_role_to_user()` permisos. Es el fix de mayor impacto/riesgo y toma 30 min.

¿Arrancamos con ese?
