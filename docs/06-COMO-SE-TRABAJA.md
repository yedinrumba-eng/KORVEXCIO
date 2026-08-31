# 06 — Cómo se trabaja sobre ERPNext

> Escrito el 2026-08-31 respondiendo a la pregunta correcta: *"¿clonamos un repo
> y lo adaptamos?"*
>
> **La respuesta es NO**, y entender por qué es la diferencia entre un producto
> mantenible y un fork muerto en tres meses.

---

## El error que mata proyectos de Frappe

El instinto es: *clono `frappe/erpnext`, le meto mano, y ya tengo el 90% hecho.*

**Lo que pasa si lo haces:** el día que salga un parche de seguridad de ERPNext,
o la v16, o un fix de contabilidad — **no lo puedes tomar.** Tu `git pull` es un
campo de conflictos contra tu propio código. Te quedas congelado en la versión
que clonaste, para siempre, manteniendo un ERP entero tú solo.

**No clonas Next.js para hacer una app de Next.js.** Haces `npm install next` y
escribes tu código encima. Frappe funciona igual.

---

## Los tres niveles

```
┌─ NIVEL 1 · UPSTREAM — NO SE TOCA ─────────────────────────────┐
│  frappe · erpnext · posnext                                    │
│  Se instalan desde su repo oficial, con branch fijado.         │
│  Se actualizan con git pull / rebuild de imagen.               │
│  Cero commits tuyos aquí.                                      │
└────────────────────────────────────────────────────────────────┘
                            ▲  extiende
┌─ NIVEL 2 · TU CÓDIGO ─────┴────────────────────────────────────┐
│  github.com/yedinrumba-eng/KORVEXCIO.git                       │
│  Una app de Frappe + el docker + los scripts + estos docs.     │
│  Es lo ÚNICO que tú versionas y mantienes.                     │
└────────────────────────────────────────────────────────────────┘
                            ▲  configura
┌─ NIVEL 3 · POR TENANT — NO ES CÓDIGO ──┴───────────────────────┐
│  sites/vapeland.korvexdev.cc/  · sites/cliente2.korvexdev.cc/  │
│  Cada uno su base de datos. VAPELAND es CONFIGURACIÓN.         │
│  Un cliente nuevo NUNCA es un fork.                            │
└────────────────────────────────────────────────────────────────┘
```

---

## Qué vive en `KORVEXCIO.git`

```
KORVEXCIO/                              ← tu repo, lo único que mantienes
├── korvexcio/                          ← LA app de Frappe
│   ├── hooks.py                        ← el enganche con ERPNext
│   ├── modules.txt                     ← "ECF" y "Retail"
│   ├── fixtures/                       ← custom fields exportados, versionados
│   ├── ecf/                            ← módulo fiscal
│   │   ├── doctype/
│   │   │   ├── ecf_settings/           ← RNC, certificado, ambiente, proveedor
│   │   │   ├── ecf_sequence/           ← rangos e-NCF + alerta de agotamiento
│   │   │   └── ecf_document/           ← cola: pendiente→enviado→aceptado
│   │   ├── providers/
│   │   │   ├── base.py                 ← emitir · consultar · anular
│   │   │   ├── ssd.py                  ← ECF SSD vía ecf-dgii (MIT)
│   │   │   └── alanube.py
│   │   └── print_format/               ← Representación Impresa con QR
│   └── retail/                         ← módulo vertical
│       ├── item_attributes.py          ← Sabor · Nicotina · Tamaño · Ohmiaje
│       ├── age_verification.py
│       ├── fefo.py                     ← lotes y vencimiento
│       └── report/                     ← stock muerto · margen · rotación
├── apps.json                           ← qué upstream se instala y en qué branch
├── docker/                             ← compose y Containerfile
├── scripts/                            ← alta de tenant, seeds, catálogo
├── docs/                               ← lo que ya escribimos
└── HANDOFF.md · CLAUDE.md · PRD.md · TECH_STACK.md · PROGRESO.md
```

**El upstream NO está en tu repo.** `apps.json` dice de dónde sale:

```json
[
  { "url": "https://github.com/frappe/erpnext",           "branch": "version-15" },
  { "url": "https://github.com/DeeloaSociety/posnext",    "branch": "main" },
  { "url": "https://github.com/yedinrumba-eng/KORVEXCIO", "branch": "main" }
]
```

Ese archivo se le pasa al build como secreto de BuildKit y sale una imagen
propia:

```bash
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --secret=id=apps_json,src=apps.json \
  --tag=korvexcio:15 \
  --file=images/layered/Containerfile .
```

---

## Una app o dos — decisión revisada

Los documentos anteriores hablaban de **dos** apps (`korvex_ecf` y
`korvex_retail`). **Se corrige a UNA app, `korvexcio`, con dos módulos
internos.**

**Por qué:** `apps.json` instala *un repo = una app*. Dos apps serían dos repos
que versionar, dos builds que coordinar y dos `bench install-app` en cada alta
de tenant — para separar algo que hoy nadie te está pidiendo separado.

Frappe ya tiene **módulos** dentro de una app (`modules.txt`). Te da la
separación de carpetas y de permisos sin pagar el costo operativo.

**La salida, si algún día hace falta:** vender el módulo fiscal solo, a alguien
que no usa tu vertical. Ese día, sacar `ecf/` a su propia app es un refactor de
días, no una reescritura. Mismo criterio de `KORVIS/docs/research/12-antipatrones.md`:
no resolver hoy un problema que el proyecto no tiene.

---

## Cómo se extiende ERPNext sin tocarlo

Cuatro mecanismos, en orden de preferencia:

### 1. DocTypes propios
Entidades que ERPNext no tiene. `ECF Settings`, `ECF Sequence`, `ECF Document`.
Se crean en la UI con `developer_mode 1` y **se escriben solos como JSON** en tu
repo.

```bash
bench --site vapeland.localhost set-config developer_mode 1
```

### 2. `hooks.py` — engancharse a los eventos de ERPNext
El corazón. Ejemplo real de este proyecto:

```python
doc_events = {
    "Sales Invoice": {
        "on_submit": "korvexcio.ecf.api.encolar_ecf",
    }
}
```

Se emite la factura → tu código encola el e-CF. **Cero líneas modificadas en
ERPNext.**

### 3. Custom Fields + fixtures
Agregarle campos a DocTypes de ERPNext: `rnc` en `Customer`, `ecf_trackid` y
`ecf_status` en `Sales Invoice`, `requiere_verificacion_edad` en `Item Group`.

Se hacen en **Customize Form** (UI) y se exportan a tu repo:

```bash
bench --site vapeland.localhost export-fixtures --app korvexcio
```

⚠️ **Sin exportar, esos campos viven solo en la base de datos del site y se
pierden en la próxima instalación.** Es el error más común.

### 4. Override de clases
Reemplazar una clase de ERPNext. **Último recurso**, solo si los tres de arriba
no alcanzan. Cada override es deuda que se paga en cada actualización.

---

## La excepción: POSNext SÍ se forkea

ERPNext está diseñado para extenderse desde afuera. **POSNext no.** Vas a
necesitar campos fiscales dominicanos en la pantalla de caja, y eso se toca por
dentro.

**Cómo se forkea bien:**

```bash
# fork en GitHub → yedinrumba-eng/posnext
git clone https://github.com/yedinrumba-eng/posnext
cd posnext
git remote add upstream https://github.com/DeeloaSociety/posnext
git checkout -b korvex          # tus cambios viven en SU rama, nunca en main
```

Para traer mejoras del original: `git fetch upstream && git rebase upstream/main`.
Los cambios propios quedan aislados en una rama y se re-aplican encima.

⚠️ **Antes de forkear:** intentar resolverlo con hooks y custom fields. Cada
línea que tocas dentro de POSNext es una línea que tú mantienes para siempre.

---

## De dónde sale la velocidad real

No sale de clonar el POS de otro. Sale de lo que ya existe y **no** tienes que
construir:

| Ya existe, gratis | Lo escribes tú |
|---|---|
| Inventario, variantes, lotes, multi-almacén | **Módulo e-CF completo** |
| Contabilidad de partida doble | Atributos del vertical (sabor, nicotina) |
| Compras, proveedores, órdenes | FEFO y alertas de vencimiento |
| Usuarios, roles, permisos | Verificación de edad |
| POS con escáner, turnos, offline | Reportes del rubro |
| Multi-tenant por site | Impresión con QR del e-CF |
| API REST completa | |

**Escribes quizá el 15% del sistema.** Ese 15% es el que ningún repo del mundo
te va a regalar, porque es de República Dominicana y de este rubro.

---

## La regla, en una línea

> **El upstream se instala. Tu código se escribe encima. El cliente se configura.**
> Si te encuentras editando un archivo dentro de `apps/erpnext/`, **para**: hay
> una forma correcta de hacer eso, y está en la lista de arriba.
