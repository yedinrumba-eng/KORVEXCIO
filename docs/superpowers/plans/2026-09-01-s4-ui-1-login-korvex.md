# Korvex POS Login Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir el acceso existente de POSNext en el login de Korvex POS aprobado, conservando intactos autenticación, CSRF y apertura de turno.

**Architecture:** `Login.vue` conserva su script de negocio y reemplaza estructura semántica y estilos visuales (CSS scoped en dos archivos para mantener el componente pequeño). Vitest monta el componente real y sustituye recursos de sesión, router, stores, Web Worker y diálogo de turno. `vite.config.js` contiene los ajustes mínimos necesarios para poder compilar y verificar en Windows, sin dependencias nuevas.

**Tech Stack:** Vue 3.5, Tailwind CSS 3.4, frappe-ui, Vitest 2.1, Vue Test Utils 2.4, Inter self-hosted.

**Spec:** `docs/15-DISENO-POS-KORVEX.md`

## Global Constraints

- Trabajar en el fork `yedinrumba-eng/posnext`, rama derivada de `korvex@92b5c93`.
- No cambiar autenticación, CSRF, navegación ni apertura de turno.
- Todo texto visible pasa por `__()`.
- No agregar dependencias.
- Movimiento decorativo desactivado con `prefers-reduced-motion: reduce`.
- La tarjeta de acceso es la única superficie de cristal visible.
- No hacer push sin autorización explícita de Yedin.

---

### Task 1: Contrato observable del login Korvex

**Files:**
- Create: `POS/src/pages/Login.test.js`
- Modify: `POS/src/pages/Login.vue`
- Create: `POS/src/styles/login.css`, `POS/src/styles/login-scene.css`
- Modify: `POS/vite.config.js`, `POS/vitest.config.js`

**Interfaces:**
- Consumes: `session.login.submit({ email, password })`, `session.login.loading`, `session.login.error`.
- Produces: formulario accesible con encabezado `Korvex POS`, campos `Usuario o correo` y `Contraseña`, alerta de error y botón `Iniciar sesión`.

- [x] **Step 1: Write the failing component test**

Montar `Login.vue` real y sustituir sesión, stores, router,
Web Worker y diálogo de turno. Verificar por etiquetas accesibles que aparecen la
marca, el formulario y sus dos campos; completar ambos valores, enviar el
formulario y comprobar que `session.login.submit` recibe el correo recortado y
la contraseña intacta.

- [x] **Step 2: Run the test to verify RED**

Run: `npm run test:run -- src/pages/Login.test.js`

Expected: FAIL porque el componente actual muestra `Sign in to POS Next` y no
expone el contrato visible de Korvex POS en español.

- [x] **Step 3: Implement the approved TMS-style login**

Reemplazar el template visual de `Login.vue` por una composición nocturna con
órbitas decorativas, tarjeta de cristal, marca `Korvex POS`, descriptor `Punto
de venta`, formulario accesible y pie de acceso autorizado. Mantener sin cambios
las funciones `submit`, `handleShiftOpened`, `handleDialogClosed` y los watchers
de sesión. Usar estilos scoped para halos, foco, fallback de transparencia y
movimiento reducido.

- [x] **Step 4: Run the focused test to verify GREEN**

Run: `npm run test:run -- src/pages/Login.test.js`

Expected: PASS sin errores ni warnings.

- [ ] **Step 5: Run frontend quality gates**

Run: `npm run lint`

Expected: exit 0.

Run: `npm run build`

Expected: exit 0 y bundle generado en `pos_next/public/pos`.

Resultado al 05/09: build exit 0 y Biome dirigido sobre seis archivos exit 0.
Lint global exit 1 (124 errores, 130 archivos revisados); queda pendiente la
aceptación explícita de esa deuda ajena al slice. No marcar este paso completo
como ocurrió en la entrada anterior.

### Task 2: Verificación visual responsive

**Files:**
- Verify: `POS/src/pages/Login.vue`
- Capture: evidencia temporal fuera de Git para 1440x900, 840x760 y 375x812.

**Interfaces:**
- Consumes: build local del Task 1.
- Produces: evidencia visual revisable de la composición aprobada.

- [x] **Step 1: Start the local frontend**

Run: `npm run dev -- --host 127.0.0.1`

Expected: Vite sirve la aplicación en `http://127.0.0.1:8080/pos/account/login`.

- [x] **Step 2: Capture the three approved viewports**

Abrir el login en 1440x900, 840x760 y 375x812. Confirmar que no existe scroll
horizontal, que la tarjeta cabe completa y que los campos conservan al menos
44 px de alto.

- [x] **Step 3a: Verify keyboard accessibility**

Navegar usuario, contraseña, mostrar contraseña y botón solo con teclado.
Comprobado en navegador: cuatro controles con `focusVisible: true`; Enter
alterna visibilidad de contraseña sin enviar el formulario.

- [ ] **Step 3b: Verify reduced motion**

Activar `prefers-reduced-motion: reduce` y confirmar que órbitas y halos dejan de
animarse.

- [ ] **Step 4: Commit the verified slice**

Run: `git status --short`

Confirmar que no entraron `.env`, `node_modules`, bundles o capturas temporales.

Run: `git add POS/src/pages/Login.vue POS/src/pages/Login.test.js POS/src/styles/login.css POS/src/styles/login-scene.css POS/vite.config.js POS/vitest.config.js`

Run: `git commit -m "feat: brand POS login for Korvex"`

## Estado de reanudación — 2026-09-02

Task 1 quedó implementado. El test focalizado pasa 1/1 con Node 24.19.0 y
Biome dirigido pasa sobre los cinco archivos del slice. El lint global no pasa:
trae 185 errores heredados en 127 archivos fuera de este trabajo. El build local
se abortó sin output ni artefacto (Node 25 >8 min, Node 24 >4 min); falta
ejecutarlo en Linux.

Task 2 queda pendiente: el navegador integrado no está disponible (`No browser
is available`, lista `[]`). Faltan las tres capturas, teclado y reduced motion.
No hay commit local ni push autorizado en `feat/korvex-ui-s4`.

Expected: habilitar navegador, verificar build Linux, cerrar los gates y hacer
un commit local; ningún push sin autorización explícita.

## Reanudación real — 2026-09-05

Los dos bloqueos técnicos anteriores quedaron resueltos. No era un problema
de versión de Node: el auto-proxy de `frappe-ui` tiene un bucle infinito al
buscar el bench en Windows. La configuración evita ese descubrimiento solo
allí y mantiene Linux intacto. El build productivo Windows ya termina con
bundle, rutas públicas correctas, plantilla Jinja y PWA. No hace falta Linux
para este gate local; el despliegue no se ha ejecutado.

Vitest pasa 8/8; Biome dirigido pasa 6/6 archivos. El navegador disponible
permitió medir y capturar 1440×900, 840×760 y 375×812, sin overflow ni tarjeta
recortada. Comandos, salidas y ruta de capturas en la entrada del 05/09 de
`PROGRESO.md`.

**Estado PARCIAL:** falta la prueba real de movimiento reducido y aceptar la
deuda del lint global. Se pidió a Yedin desactivar temporalmente los efectos
de animación de Windows porque este navegador no ofrece emulación de esa
preferencia. La lectura real sigue siendo `false`. No se sustituye por un mock.
No se han probado login contra Frappe, impresora ni contingencia del local;
no hubo commit, push ni cambios en el servidor. Cerrar antes de S4.2b.
