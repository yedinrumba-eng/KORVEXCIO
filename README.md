# VAPELAND — KORVEXCIO

ERP + POS para tienda de vapes/hookah/tabaco con cafetería adjunta en República
Dominicana, construido sobre ERPNext/Frappe, multi-tenant, para revenderse como
producto KORVEX a otros negocios de retail + food.

**Cliente:** VAPELAND (RD) · **Producto:** KORVEXCIO
**Estado:** ⚪ Semilla — descubrimiento hecho, cero código
**Carpeta:** `C:\PROYECTOS\KORVEXCIO` ⏳ *pendiente de renombrar desde `VAPELAND`*
**Repo:** [`yedinrumba-eng/KORVEXCIO`](https://github.com/yedinrumba-eng/KORVEXCIO.git) ✅ *creado 31/08/2026*

---

## Nomenclatura — la familia de marcas

Decidido el 2026-08-31. Los tres nombres cumplen §1 de `CONVENCIONES.md`
(carpeta = producto = repo).

| Nombre | Qué es |
|---|---|
| **KORVEX** | La casa. La empresa: Korvex Dev · `korvexdev.cc` |
| **KORVEXCIO** | **Este producto.** ERP + POS + inventario + e-CF para retail y food. Juego con *comerCIO* |
| **KORVIS** | *The AI Assistant by Korvex* — el asistente conversacional de WhatsApp. **Producto de KORVEX, marca propia** |
| **VAPELAND** | **Un cliente**, no un producto. Primer tenant de KORVEXCIO |
| **ADAP** | **Un cliente** de KORVIS (banco RD), no el nombre del producto |

⚠️ **Sin guion: `KORVEXCIO`, no `KORVEX-CIO`.** El guion parte la palabra y mata
el juego con *comercio*.

⚠️ **En disco, la carpeta de KORVIS todavía se llama `C:\PROYECTOS\ADAP`.** Las
rutas de este documento apuntan al nombre real de hoy, no al que debería tener
(ver `_KORVEX-OPS/MUDANZA.md`).

---

## Empezar aquí

1. **`HANDOFF.md`** — lo primero que se lee. Decisiones tomadas, el reloj de
   76 días, las tres facturas de elegir ERPNext, y qué se hace primero.
2. **`docs/05-PREGUNTAS-CLIENTE.md`** — lo que falta confirmar. Llevarlo a la
   reunión.

## Los archivos

| Archivo | Qué contiene |
|---|---|
| `HANDOFF.md` | Estado, decisiones, riesgos, primeros pasos |
| `PROMPT-CLAUDE-CODE.md` | **El prompt listo para pegar** en la primera sesión de Claude Code |
| `PRD.md` | Qué se acordó (y qué no) |
| `TECH_STACK.md` | Decisiones técnicas y por qué |
| `CLAUDE.md` | Reglas obligatorias para trabajar en este repo |
| `PROGRESO.md` | Bitácora del proyecto. Se marca al cerrar un slice |
| `docs/01-DESCUBRIMIENTO.md` | El negocio, los dos rubros, el inventario de un vape shop |
| `docs/02-FISCAL-RD.md` | e-CF, ISC, ITBIS, RST, certificado digital, contingencia |
| `docs/03-BENCHMARK-OPENSOURCE.md` | Repos evaluados, con licencia y veredicto |
| `docs/04-ARQUITECTURA.md` | Multi-tenancy, hosting, apps, seguridad, modelo de producto |
| `docs/05-PREGUNTAS-CLIENTE.md` | Lo que falta confirmar |
| `docs/06-COMO-SE-TRABAJA.md` | **Cómo se extiende ERPNext sin tocarlo.** El modelo de trabajo |
| `docs/07-ARQUITECTURA-REFERENCIA.md` | **Barrido de ~45 repos de RD + 9 localizaciones fiscales de Frappe.** El mapa de licencias y la estructura de DocTypes ya destilada |

## La fecha que manda

**15 de noviembre de 2026** — facturación electrónica obligatoria para
pequeños, micro y no clasificados en RD (Ley 32-23). Multa por incumplir:
5 a 50 salarios mínimos.
