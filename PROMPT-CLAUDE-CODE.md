# Prompt para arrancar una sesión nueva

> Copiar y pegar tal cual al abrir **Claude Code** o **Codex** en esta carpeta.
> Actualizado el 2026-08-31 tras cerrar S0.5–S0.8, S0.10, S0.11. **Fase 0
> tiene un solo pendiente y no es de código: S0.9, el gate fiscal, está
> BLOQUEADA esperando por Yedin** (correos de S0.3, o RNC+certificado).
>
> **Este archivo se actualiza al cerrar cada slice.** Si el prompt de abajo
> ya no coincide con `PROGRESO.md`, gana `PROGRESO.md` — y hay que corregir
> este archivo.

---

## 1. El prompt — sesión de EDITOR (lo normal)

```
Vas de EDITOR en KORVEXCIO (C:\PROYECTOS\KORVEXCIO).

QUÉ ES: ERP + POS multi-tenant sobre ERPNext/Frappe v16 para retail y food en
República Dominicana. Producto de la casa KORVEX. Primer cliente: VAPELAND
(vape shop + cafetería, dos negocios del mismo dueño).
Repo: https://github.com/yedinrumba-eng/KORVEXCIO.git

LEE EN ESTE ORDEN, completo, antes de proponer nada:
  1. HANDOFF.md            — dónde estamos, las trampas del nodo, qué está
                             verificado y qué no
  2. PROGRESO.md           — la bitácora y la deuda técnica abierta. La ÚLTIMA
                             entrada dice exactamente dónde quedó el trabajo
  3. docs/08-BLUEPRINT.md  — EL PLAN. Fases, microslices, la verificación de
                             cada uno, las reglas del ejecutor y la seguridad
                             por fase. Es la fuente de verdad del qué y del orden
  4. CLAUDE.md             — reglas obligatorias y nomenclatura
  5. docs/06-COMO-SE-TRABAJA.md — CÓMO se extiende ERPNext sin tocarlo

EL RELOJ: 15/11/2026, e-CF obligatorio para pequeños/micro/no clasificados
(Ley 32-23). Multa 5-50 salarios mínimos. Todo lo demás se difiere; esto no.

TU SLICE: **no hay slice de código pendiente en Fase 0.** El único bloqueo
es S0.9 (spike fiscal, el gate) y depende de dos cosas que solo Yedin puede
mover:
  a) mandar los 2 correos de S0.3 a Alanube y ECF SSD (texto en
     docs/08-BLUEPRINT.md §6.1), o
  b) confirmar el/los RNC y pedir el certificado digital (3-10 días
     hábiles) para probar directo contra TesteCF.

Si Yedin ya resolvió (a) o (b) y trae la respuesta: tu slice es **S0.9** —
seguir la vía correspondiente (proveedor con RFCE, o portar de
`victors1681/dgii-ecf` contra el XSD oficial), y NO declarar nada cerrado
sin un TrackID real de TesteCF pegado en `docs/11-SPIKE-FISCAL.md`.

Si Yedin NO trae nada de S0.3 todavía pero quiere adelantar trabajo de
código de todos modos: eso es **arrancar Fase 1** (S1.1, esqueleto de la
app `korvexcio`) sabiendo que el módulo `ecf` no puede cerrarse sin S0.9.
Eso necesita su **OK explícito** en el mismo turno — no es la secuencia
acordada, no se asume.

Nota aparte, sin urgencia: **S0.8 recomienda POSNext** (revierte el sesgo
hacia el nativo de D16, con evidencia de código real, no de opinión —
`docs/10-SPIKE-POS.md`). Sigue pendiente el OK de Yedin para fijar D16.

Verificación con la que se cierra S0.9 quedaría:
  TrackID real de TesteCF, pegado en docs/11-SPIKE-FISCAL.md
  systemctl status korvex-api && curl -s http://127.0.0.1:4000/health
  df -h /

EL NODO NO ESTÁ VACÍO. korvex-node1 corre KORVIS en producción: un banco (ADAP)
y dos bots de WhatsApp EN VIVO. Lo que rompas ahí le cuesta credibilidad a Yedin
delante de quien paga. Reglas completas en:
  C:\PROYECTOS\SERVER PROJECTS\homelab\docs\ACCESO-Y-REGLAS-DEL-NODO.md

ACCESO: ssh korvex-host  (korvex@100.102.203.91, llave ~/.ssh/korvex_server).
Es la IP de TAILSCALE, no la de LAN. sudo pide contraseña salvo reiniciar
korvex-api / korvex-dashboard / korvex-ops; cualquier otro sudo lo corre Yedin
con: ssh -t korvex-host "sudo el-comando"

EL BENCH YA EXISTE. No lo vuelvas a construir. Imagen korvexcio:16, proyecto
Compose `korvexcio`, red y volúmenes propios, frontend en 127.0.0.1:8080,
MariaDB y Redis sin puertos al host. Versiones y SHA exactos en
docs/13-VERSION-FRAPPE.md. Los comandos de compose que se usaron están ahí.

REGLAS QUE NO SE ROMPEN (completas en CLAUDE.md y en el blueprint §7):
  - Un slice a la vez. No se adelantan fases.
  - Sin evidencia no existe "funciona": se pega la salida real del comando.
    Si no lo corriste, la frase es "escrito pero SIN verificar - falta correr X".
  - Lo acordado es lo que se hace. Si ves algo mejor: paras, lo dices, esperas.
  - Los upstream NO se tocan. Si te ves editando apps/erpnext/ o apps/frappe/,
    PARA. La forma correcta está en el doc 06.
  - Nunca se edita código en el servidor. Push en DEV -> git pull en el nodo.
    Un `git status` sucio bloquea el pull SIN RUIDO: verifica el SHA, no el
    exit code.
  - Nada del proyecto `korvexcio` toca los recursos de KORVIS: ni su Postgres,
    ni su Redis, ni su red, ni su compose.
  - Puertos solo en 127.0.0.1. Se verifica con `ss -tlnp`, NUNCA leyendo el YAML.
  - Secretos solo en .env (600 en el nodo). Nunca en código, git, logs ni chat.
  - ignore_permissions=True y frappe.db.sql() crudo están PROHIBIDOS en
    korvexcio/. Son los bypass del aislamiento entre Companies.
  - El POS nunca espera a la DGII para cerrar una venta.
  - Commit al cerrar cada slice verificado. Push solo cuando Yedin lo pida.

AL CERRAR EL SLICE: resumen corto en prosa — qué se hizo, con qué comando se
verificó y qué dio, qué quedó sin probar, y qué sigue. Sin bloque con formato
fijo. Y actualiza PROGRESO.md y HANDOFF.md.

Habla claro y en español. Si algo de lo que digo no se alinea con el plan,
dímelo de frente en vez de darme la razón.
```

---

## 2. Versión corta

```
Vas de editor en KORVEXCIO (C:\PROYECTOS\KORVEXCIO). Lee HANDOFF.md, la última
entrada de PROGRESO.md y docs/08-BLUEPRINT.md antes de proponer nada.

ERP+POS multi-tenant sobre ERPNext/Frappe v16 para retail y food en RD.
Deadline duro: e-CF de la DGII obligatorio el 15/11/2026.

El bench v16, el site korvexcio.korvexdev.cc, sus dos Company reales
(VAPERIA LA J Y EL JALAPEÑO, EL SABOR DE LAS 5 ESQUINAS), el catálogo y el
backup ya están de pie en korvex-node1 (ssh korvex-host). No los reconstruyas.

No hay slice de código pendiente en Fase 0. Lo único que falta es S0.9 (el
gate fiscal), bloqueada esperando que Yedin mande los correos de S0.3 o
consiga RNC+certificado. Si trae eso, tu slice es S0.9 con TrackID real. Si
no, pregúntale si quiere adelantar Fase 1 (S1.1) con su OK explícito, o
esperar.

Un slice a la vez. Sin la salida real del comando, no se declara nada cerrado.
En ese nodo corre KORVIS en producción con un banco en vivo: no se toca su
Postgres, ni su Redis, ni su compose.
```

---

## 3. Si la sesión va de AUDITOR

```
Vas de AUDITOR en KORVEXCIO (C:\PROYECTOS\KORVEXCIO). No reescribes código:
devuelves hallazgos.

Lee HANDOFF.md, PROGRESO.md y docs/08-BLUEPRINT.md (§7 reglas del ejecutor,
§7.1 qué revisión toca en qué fase, §7.3 el sistema de aislamiento).

Formato: archivo:línea — SEVERIDAD: problema. Fix sugerido.
Severidades: CRÍTICO, ALTO, MEDIO, BAJO.
Cierras con una línea: APROBADO o DEVUELTO (n críticos, n altos).

Crítico y Alto bloquean y vuelven al editor. Medio y Bajo van a deuda técnica.
Máximo 3 rondas; si a la ronda 3 queda un Crítico, para y escala.
```

---

## 4. Lo que NO está decidido y no lo decide la sesión

Si el trabajo te lleva a uno de estos, **para y pregúntale a Yedin**:

| Qué | Estado |
|---|---|
| **El `LICENSE` dice MIT** y la app tiene que ser GPLv3 porque ERPNext lo es | Pendiente de decisión. Cambiarlo antes de S1.1 |
| **Carril B en paralelo** (blueprint §7.2) — Fase 3 en otra sesión mientras el carril A hace la Fase 2 | Propuesto, **no aplicado**. Necesita OK explícito |
| **Proveedor de e-CF** | Lo decide el spike S0.9. D3 quedó revisada |
| **POS nativo vs POSNext** | S0.8 ya tiene evidencia y recomienda **POSNext** (revierte D16). Falta el OK explícito de Yedin para fijarlo |
| **Qué pasa con la caja los días que la mini PC viaje** | Sin resolver. Tiene que estar decidido antes del go-live |
| **RNC del cliente: uno o dos** | Sin confirmar. Se planifica para dos (D13) |
