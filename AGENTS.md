# AGENTS.md — Reglas de seguridad para vibe coding (Cursor / Copilot / Codex / Windsurf)

> Copia este archivo a la raíz del proyecto que vas a construir o auditar. Los editores con
> agentes (Cursor, GitHub Copilot, Codex, Windsurf, y otros que siguen la convención `AGENTS.md`)
> lo cargan automáticamente y aplican estas reglas mientras generan código.
>
> **Prevención > detección.** Las reglas de abajo evitan que el bug se escriba.
> Fuente de verdad detallada: `docs/vulnerabilidades/0X-*.md` de este toolkit
> (la carpeta raíz del repo). Para auditoría final corre `/secure-vibe`.
>
> ¿Claude Code? Usa `plantillas/CLAUDE.md` (contenido equivalente).

---

## Cómo cargar este archivo por editor

<details>
<summary>Cursor / Codex / Windsurf (auto)</summary>

Coloca este `AGENTS.md` en la raíz del proyecto. El agente lo lee al iniciar la sesión.
En Cursor: Settings → Rules for AI también acepta el contenido (pero el archivo es lo estándar).
En Codex: `AGENTS.md` se carga automáticamente desde la raíz.

</details>

<details>
<summary>GitHub Copilot</summary>

Coloca `AGENTS.md` en la raíz del repo. Copilot Chat y Copilot Workspace lo respetan
como instrucciones de repositorio. Alternativa: `.github/copilot-instructions.md` con el
mismo contenido.

</details>

<details>
<summary>Claude Code</summary>

Usa `CLAUDE.md` en la raíz del proyecto (Claude Code lo carga por defecto). Este
`AGENTS.md` es la versión multi-editor del mismo contenido.

</details>

---

## Esencia (memoriza antes de escribir una línea)

1. **El servidor es la verdad. El frontend no es seguridad.** Toda validación, authn,
   authz, RLS, billing, rate limit y firma de webhooks viven **en el backend**. Rechaza
   cualquier `feature flag`, `isPremium` o `isAdmin` que venga del cliente.
2. **Default-deny.** Toda ruta, política RLS, permiso, CORS, tool call arranca **cerrado**.
   Se abre solo con evidencia explícita y justificada.
3. **Input hostil hasta que se prueba lo contrario.** Cualquier dato del cliente se
   valida con schema (`zod`/`joi`/`pydantic`), allow-list, tamaño/longitud acotados.
4. **No ejecutes texto.** SQL(input), shell(input), HTML render(input del LLM incluido),
   `eval`, `dangerouslySetInnerHTML` crudo = prohibido.

---

## MUST (patrón seguro por defecto — escribe así)

### Secrets (doc 01)
- Cargar toda credencial desde `process.env` / secret manager. Nunca hardcodear.
- `.env` en `.gitignore`; commitear `.env.example` sin valores reales.
- service-role / admin keys **solo en servidor**. Nunca en código de cliente ni bundle.

### Input validation (doc 02)
- Validar `body`/`query`/`params` con schema antes de usarlo (`safeParse`).
- Allow-list de enum, formato, longitud, rango. Rechazar lo no listado.
- Mass assignment: `update` con DTO explícito (campos permitidos), nunca `req.body` crudo.
- Canonicalizar antes de validar (URL-decode, normalize unicode, resolve paths).

### Inyección (doc 03)
- SQL: queries **parametrizadas** / ORM bindings. Sin concatenar `${input}`.
- Shell: sin `exec(input)`. Sin `child_process.exec` con strings del usuario.
- Path: confinar a dir base canonizado; rechazar `..` y nul bytes.
- Fetch del usuario: allow-list de dominios (mitiga SSRF; bloquea `169.254.169.254`, `localhost`).

### AuthN / AuthZ / IDOR (doc 04)
- Cada ruta protegida exige middleware de authn **en el backend**. Sin excepciones.
- AuthZ function-level: roles del servidor, no del body/header.
- Recursos por `id`: scope con `userId`/`tenantId` en la query. Cambiar el ID en la URL
  **no** debe dar acceso ajeno.
- Passwords: `argon2id`/`bcrypt`. Errores timing-comparable (sin "user not found" revelador).
- JWT: verificar `alg`≠`none`, `iss`/`aud`, expiración corta, rotación.

### RLS / tenant (doc 05)
- Cada tabla con datos de user/tenant: `ENABLE ROW LEVEL SECURITY` + `FORCE` + policy
  `USING`/`WITH CHECK` filtrando por `tenant_id`/`auth.uid()`.
- Funciones `SECURITY DEFINER`: auditar que no bypassean RLS.
- Usuario de runtime: no superuser, sin `BYPASSRLS`.

### Rate limiting (doc 06)
- Endpoints sensibles (login/reset/OTP/checkout/AI) con limiter por **IP y usuario**
  (y por tenant en SaaS). Respuesta `429` + `Retry-After`.
- AI endpoints: cota por **tokens** además de requests.
- Detrás de proxy: `trust proxy` fijado a número de hops (no `true`).

### LLM / prompt injection (doc 07)
- System prompt: **constante**, sin `${userInput}`. Datos del usuario/recuperado van
  delimitados (`<user_input>`, `<context>`) **después** de las instrucciones.
- RAG filtrada por `tenantId`/ACL (metadata filter en cada query).
- Outputs del LLM: **no ejecutar**. Si se renderiza HTML, `DOMPurify.sanitize`.
- Tool calls: allow-list + scope por rol/tenant + `requireHumanApprove` para destructivas.
  El `user`/`tenantId` viene de la sesión del servidor, no de args del modelo.
- Sin secrets ni datos ajenos en el contexto del modelo.

### Headers / CORS / CSRF / cookies (doc 08)
- CORS: allow-list de orígenes explícitos. **Nunca `*` con `credentials:true`**. No reflejar `Origin` crudo.
- Cookies: `HttpOnly` + `Secure` + `SameSite`. Prefijo `__Host-` cuando aplica.
- CSRF: `SameSite` + token sincronizador/double-submit para rutas con cookies.
- Headers: `CSP` estricta (sin `unsafe-inline`/`eval`), `HSTS` (`includeSubDomains`),
  `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors`.

### File uploads (doc 09)
- Validar **magic bytes** (no Content-Type del cliente). Renombrar a UUID + ext validada.
- Size limit hard. Bucket privado + aislamiento por tenant (`tenants/{id}/...`).
- Served como `attachment`/`octet-stream`. Sin path traversal (`originalname` no es nombre guardado).

### Dependencias / supply chain (doc 10)
- Lockfile commiteado. Versiones pinned (no `^`/`~` en prod, no `:latest` Docker).
- Sin `postinstall` sospechosos. Pasar `npm audit`/`pip-audit`/`osv-scanner`.

### CI/CD / containers (doc 11)
- Branch protection + required checks en `main` (aplica a admins).
- Workflows: `permissions: contents: read` por defecto. **No `pull_request_target` con secrets**.
- `uses:` pinnados por SHA, no `@main`/`@vN` mutable. OIDC vs long-lived keys.
- Imagen: pinned por digest, `USER` non-root, `--read-only`, `--cap-drop ALL`, sin `--privileged`.
- Sin `COPY .env` al Dockerfile.

### Logging / errors (doc 12)
- Logger estructurado con redacción de `password`/`token`/`Authorization`/cookies/prompts.
- Errores: genéricos al cliente + `traceId`. Stack/queries solo en el log del servidor.
- Debug/verbose apagados en prod (`NODE_ENV=production` forzado). Log injection (CRLF) sanitizado.
- Audit log de eventos de seguridad (login fail, cambio de rol, webhooks) ≥90 días.
- Transcripts LLM con PII: cifrados + retención definida.

### SaaS billing / webhooks (doc 13, si aplica)
- **Price/plan desde el servidor**, nunca del body. El cliente solo manda `planKey`.
- Webhook: firma verificada (doc 04) + **idempotencia** (`event.id`/`Idempotency-Key`) +
  **reconciliación** con DB/Stripe.
- Plan limits enforced server-side al crear recurso (seats/storage/AI calls).
- Race conditions: advisory lock por tenant + `UNIQUE` constraint + transacción.
- Trial: 1 por identidad, downgrade automático al expirar. Dunning sin regalar servicio.
- Metering: el servidor cuenta el consumo, no el cliente.

---

## MUST NOT (no escribas esto — genera bug automático)

- ❌ `query(`SELECT ... WHERE id = ${req.body.id}`)` → SQLi. Parámetros bindings siempre.
- ❌ `eval(input)`, `new Function(input)`, `exec(input)`, `child_process.exec(input)`.
- ❌ `<div dangerouslySetInnerHTML={{ __html: userInput }} />` sin `DOMPurify.sanitize`.
- ❌ `fetch(req.body.url)` sin allow-list de dominios → SSRF.
- ❌ `User.update(req.body)` → mass assignment (escala `role`).
- ❌ `service_role` / `SUPABASE_SERVICE_ROLE` en cualquier `.client.*` o carpeta de navegador.
- ❌ Cookie de sesión sin `HttpOnly`/`Secure`/`SameSite`.
- ❌ `Access-Control-Allow-Origin: *` con `credentials: true`, o reflejar `Origin` sin validar.
- ❌ System prompt con `${userInput}`. ❌ Outputs del LLM a `innerHTML` sin sanitizer.
- ❌ Tool call destructiva sin `requireHumanApprove` y scope por usuario/tenant.
- ❌ Webhook de pago sin verificar firma + sin idempotencia.
- ❌ `amount`/`price`/`plan` tomados del `req.body`. ❌ Logs con `password`/`token`/prompts completos.
- ❌ `console.log(e.stack)` al cliente. ❌ `DEBUG=true` hardcodeado. ❌ `:latest` en Dockerfile.
- ❌ `uses: org/action@main` (sin pin SHA). ❌ `pull_request_target` con checkout del PR + secrets.
- ❌ Nombre de archivo guardado = `req.file.originalname`. ❌ Validar tipo por `Content-Type`.
- ❌ Trust en `req.ip` con `trust proxy: true` sin número de hops.

---

## Antes de declarar "listo" cualquier feature

1. ¿Authn + authz en el backend? ¿IDOR cubierto (test A→B)?
2. ¿Input validado con schema? ¿Allow-list? ¿Mass assignment bloqueado?
3. ¿Output del LLM/usuario renderizado sin ejecución?
4. ¿Secrets solo en env/secret manager? ¿fuera de bundles y git?
5. ¿Rate limit en endpoints sensibles? ¿Logs sin secrets?
6. Si toca datos reales, pagos, salud o niños → recomienda pentest profesional.

> Si dudas, abre el doc `0X` correspondiente en `docs/vulnerabilidades/` antes de decidir
> el patrón. No inventes; verifica.
