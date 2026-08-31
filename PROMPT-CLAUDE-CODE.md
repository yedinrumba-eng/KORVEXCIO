# Prompt para arrancar en Claude Code

> Copiar y pegar tal cual en la primera sesión de Claude Code en esta carpeta.
> Actualizado el 2026-08-31 tras el barrido de arquitectura de referencia.

---

## El prompt

```
Proyecto KORVEXCIO — ERP + POS multi-tenant sobre ERPNext/Frappe para retail y
food en República Dominicana. Primer cliente: VAPELAND (tienda de vapes/hookah/
tabaco con cafetería en RD). Se vende después a más clientes.
Repo: https://github.com/yedinrumba-eng/KORVEXCIO.git

LEE EN ESTE ORDEN, completo, antes de proponer nada:
  1. HANDOFF.md                        — decisiones, riesgos, el reloj, y la
                                         tabla de qué está verificado y qué no
  2. docs/06-COMO-SE-TRABAJA.md        — CÓMO se extiende ERPNext sin tocarlo
  3. docs/07-ARQUITECTURA-REFERENCIA.md — el mapa de licencias, los repos de RD
                                         y la estructura de DocTypes ya destilada
  4. CLAUDE.md                         — reglas obligatorias y nomenclatura
  5. docs/02-FISCAL-RD.md              — el e-CF de la DGII, el camino crítico

⛔ NO se clona ni se modifica ERPNext. Se instala vía apps.json con branch
fijado, y todo lo nuestro va en UNA app de Frappe llamada `korvexcio`, con dos
módulos internos: `ecf` (fiscal DGII) y `retail` (vertical). Si te encuentras
editando un archivo dentro de apps/erpnext/ o apps/frappe/, PARA — hay una forma
correcta y está en el doc 06. Única excepción: POSNext sí se forkea, en rama
`korvex`, con `upstream` como remote.

EL RELOJ: 15/11/2026, e-CF obligatorio para pequeños/micro/no clasificados
(Ley 32-23). Multa 5-50 salarios mínimos. Todo lo demás se difiere; esto no.

Las 4 decisiones están tomadas y NO se re-discuten: ERPNext/Frappe · e-CF vía
proveedor certificado por API · MVP = POS + inventario + e-CF · producto
genérico retail+food con módulos. Si el spike fiscal falla, eso sí es
información nueva y se reabre la decisión del proveedor — nunca la base.

TU PRIMERA TAREA — Fase 0, en este orden, sin saltarte pasos:

  1. VERIFICAR los 4 repos marcados ⭐ en docs/07 (20 minutos):
       - wilmerm/alanube-python        → ¿MIT? ¿Python? ¿los 10 tipos? ¿vivo?
       - victors1681/dgii-ecf          → ¿MIT? ¿sendSummary y convertECF32ToRFCE?
       - platinum-place/laravel-dgii   → ¿MIT? ¿plantillas del XML e-CF y RFCE?
       - TI-Sin-Problemas/erpnext_mexico_compliance → ¿MIT de verdad?
     El doc 07 salió de un barrido automatizado que NO se pudo verificar de
     segunda mano. Confírmalo antes de construir encima, y corrige el doc con
     lo que encuentres.

  2. Levantar ERPNext v15 en Docker local (frappe_docker) con el site
     vapeland.localhost. Verifica si v16 instala POSNext y URY limpio; si sí,
     arrancamos en v16 y me lo dices.

  3. SPIKE FISCAL — timebox 2 días, no más:
     Emitir un e-CF tipo E32 de prueba contra el ambiente TesteCF de la DGII.
       Plan A: wilmerm/alanube-python (MIT, Python, reporta los 10 tipos)
       Plan B: ecf-dgii / ECF SSD
       Plan C: portar de victors1681/dgii-ecf (MIT, TypeScript, tiene RFCE)
     Lo que hay que responder, sí o no:
       - ¿E32 (factura de consumo)?
       - ¿RFCE (resumen de facturas < RD$250,000)?
       - ¿Qué se necesita exactamente para autenticar?
     ⚠️ E32 + RFCE son el 95% de las ventas de este POS. Si ninguno de los tres
     planes los cubre, PARA y dímelo.

  4. Probar POSNext y POS Awesome con un catálogo real de prueba (variantes de
     sabor y nicotina). Decidir cuál, con razones.

  5. Modelar el catálogo: 500-1,000 SKUs con Item Variant + Item Attribute.

  6. Conectar esta carpeta al repo (ya existe):
       git init && git remote add origin https://github.com/yedinrumba-eng/KORVEXCIO.git
     Revisa el .gitignore ANTES del primer push. Nunca commitear .env ni el .p12.

  7. Recién ahí: scaffold de la app `korvexcio`, usando la estructura de
     DocTypes de docs/07 §4 — ya está destilada de tres localizaciones fiscales
     de Frappe en producción, no la rediseñes.

No escribas código de producto hasta cerrar los pasos 1 a 4. Son para reducir
riesgo, y el 3 es el que decide si el proyecto mantiene su forma.

REGLAS QUE NO SE ROMPEN (completas en CLAUDE.md):
  - Los upstream NO se tocan. Todo va en `korvexcio` vía DocTypes propios,
    hooks.py y el directorio custom/*.json (patrón KSA, mejor que fixtures).
  - doc_events en hooks.py, NUNCA override_doctype_class (solo una app puede
    reclamar cada DocType — es el error de la localización de México).
  - frappe.enqueue con enqueue_after_commit=True. Sin eso encolas e-CF de
    facturas que nunca hicieron commit.
  - El POS nunca espera a la DGII para cerrar una venta.
  - Sin internet, el negocio sigue vendiendo. Ninguna venta se pierde en
    silencio.
  - Secretos con fieldtype Password, nunca Data. El .p12 como Attach. El signer
    en memoria, jamás cachear la clave desencriptada.
  - Una factura con e-CF aceptado NO se cancela: se anula con un e-CF de
    anulación. El before_cancel lo impide.
  - Ningún default del código compartido puede servirle a un solo tenant.
  - No se puede usar "ERPNext" ni "Frappe" en el nombre del producto ni en el
    dominio (marca registrada de Frappe Technologies).
  - Licencias: MIT/Apache se puede copiar. AGPL (ksa_compliance, posnext) se
    lee, no se copia. CC BY-NC-ND (Chile) ni se abre. Sin licencia = inusable.

Habla claro y en español. Si algo de lo que digo no se alinea con el plan,
dímelo de frente en vez de darme la razón.
```

---

## Versión corta

```
Lee HANDOFF.md, docs/06-COMO-SE-TRABAJA.md y docs/07-ARQUITECTURA-REFERENCIA.md
antes de proponer nada.

Proyecto KORVEXCIO: ERP+POS multi-tenant sobre ERPNext/Frappe para retail y food
en RD. Repo: github.com/yedinrumba-eng/KORVEXCIO. Primer cliente VAPELAND.
Deadline duro: e-CF de la DGII obligatorio el 15/11/2026.

NO se clona ni se modifica ERPNext: se instala vía apps.json y todo lo nuestro
va en la app `korvexcio` (módulos `ecf` y `retail`).

Arranca por la Fase 0 del HANDOFF:
  1. Verifica los 4 repos ⭐ del doc 07 (salieron de un barrido sin verificar).
  2. ERPNext en Docker local.
  3. Spike fiscal contra TesteCF, timebox 2 días — plan A/B/C en el doc 07.
     Si ninguno da E32 + RFCE, para y dime.

Cero código de producto hasta cerrar los pasos 1 a 4.
```
