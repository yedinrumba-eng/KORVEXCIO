# 14 — Activación fiscal: qué se prueba hoy, qué falta, y el día que el cliente se registre

> Escrito 2026-09-01. Responde una pregunta directa de Yedin: sin RNC ni
> certificado del cliente, ¿cómo se prueba? Y confirma la estrategia ya
> seguida en Fase 2: dejar la base lista para activarse con datos reales,
> sin tocar código el día que lleguen.

---

## 1. Por qué no se puede simular la DGII sin RNC — no es una limitación nuestra

La DGII exige que **cada llamada a TesteCF (su propio ambiente de
pruebas) venga autenticada con el certificado digital de un RNC ya
inscrito como emisor electrónico**. No hay un "modo demo" público sin
identidad fiscal real detrás — ni para probar, ni para nosotros, ni para
ningún software del mercado. Por eso **S0.9 sigue sin TrackID real** y
por eso **S2.7 (el proveedor real) sigue bloqueado por D20**: no es que
falte código, es que la propia DGII no deja entrar sin RNC+certificado.

Esto aplica igual si se integra directo contra `fc.dgii.gov.do` (vía B
de S0.9) o contra un proveedor certificado (vía A) **que a su vez hable
con la DGII usando el certificado del cliente**.

## 2. Lo que SÍ se prueba hoy, sin esperar al cliente — y ya se prueba

Toda la Fase 2 (S2.1-S2.15) tiene **91 tests automatizados** que corren
en cada slice, sin tocar la DGII ni ningún proveedor real:

- Reserva atómica de secuencias eNCF, sin colisiones entre Companies.
- Aislamiento completo entre VAPERIA LA J Y EL JALAPEÑO y EL SABOR DE
  LAS 5 ESQUINAS (D19) — incluso a través del worker que procesa la cola.
- XML bien formado para E31/E32/E34 y RFCE, con caracteres especiales
  escapados correctamente.
- Máquina de estados completa de un e-CF: Pendiente → Enviando →
  Aceptado/Rechazado, con el `FiscalProvider` **simulado** (`FakeProvider`
  en los tests) devolviendo respuestas Ok/Err controladas.
- Contingencia (`ECF Contingencia`): nunca se puede borrar ni cancelar,
  aunque nunca haya salido a la DGII.
- Secretos nunca en texto plano (contraseña del certificado, tokens de
  proveedor en los logs).

Esto es exactamente el "smoke test" que se puede hacer sin RNC: prueba
que **el sistema hace lo correcto con la respuesta que sea** — no prueba
que la DGII vaya a aceptar el documento, porque eso no se puede probar
sin ser un emisor real.

## 3. Dos caminos que NO dependen uno del otro — y uno de los dos se puede empezar ya

Es fácil pensar que todo el fiscal está atado a "cuando el cliente se
registre". **No es así.** Hay dos cosas separadas:

### Camino A — elegir proveedor y probar contra su sandbox (NO depende del cliente)

Los proveedores de e-CF (Alanube, ECF SSD) certificados por la DGII
suelen dar **su propio ambiente de sandbox con un RNC/certificado de
prueba propios**, pensado exactamente para que el integrador (nosotros)
pruebe el flujo técnico completo antes de tener un cliente real
conectado. Esto **no necesita el RNC de VAPELAND ni de nadie** — es la
vía A que S0.9 ya proponía.

**Lo único que falta para empezar este camino: mandar los dos correos de
S0.3** (el texto ya está escrito, en `docs/08-BLUEPRINT.md` §6.1) a
Alanube y a ECF SSD, y confirmar en las respuestas si dan sandbox propio.
Si alguno lo da:

1. Implementar `FiscalProvider` real contra ese sandbox (S2.7, desbloqueado).
2. Correr el flujo completo con su RNC/certificado de prueba → TrackID
   real de TesteCF → **esto SÍ cierra el gate de Fase 2** que quedó
   pendiente.
3. Cuando el cliente real se registre, es un cambio de configuración
   (§4 abajo), no de código — el `FiscalProvider` ya está probado.

**Esta es la acción más barata que se puede tomar hoy para dejar de
estar 100% bloqueados.** No depende del cliente, depende de mandar dos
correos.

### Camino B — el cliente se registra con su RNC real (sí depende de él)

Esto es lo que activa la emisión REAL de VAPELAND en producción. No hay
atajo — la certificación como emisor (S5.4) siempre necesita:
- RNC del cliente confirmado.
- Certificado digital `.p12` emitido a nombre de ese RNC (3-10 días
  hábiles, US$30-70/año, **por cada RNC** — dos Companies pueden ser dos
  RNC, ver D13).
- El proveedor elegido (vía Camino A) con la cuenta del cliente activada.

## 4. Checklist de activación — el día que llegue el RNC + certificado real

Nada de esto es código nuevo. Es llenar formularios que ya existen desde
Fase 2, en este orden:

1. **`DGII Settings`** (S2.1) — un registro por Company, cambiar
   `ambiente` de `TesteCF` a `CerteCF` (o `eCF` si ya se certificó), y
   `provider` al que se haya activado en el Camino A.
2. **`DGII Digital Certificate`** (S2.2) — subir el `.p12` real como
   `Attach`, la contraseña (campo `Password`, nunca sale por la API), y
   `valid_until` real. Un registro por Company.
3. **`Secuencia eNCF`** (S2.3) — la DGII asigna los rangos reales (`desde`/
   `hasta`) al certificar; se cargan aquí, uno por Company y tipo
   (E31/E32/E34).
4. **Verificar el resolver de proveedor** (`korvexcio/ecf/tasks.py`,
   `_resolve_provider_for_company`) — ya lee `DGII Settings.provider` por
   Company en cada llamada (regla 10 del `CLAUDE.md`, D19); no hace falta
   tocarlo, solo confirmar que el registro de S0.1 (`providers/registry.py`)
   tiene la clase real registrada del Camino A.
5. **Un smoke test real**: una venta de prueba pequeña, confirmar que
   `ECF.estado` pasa de `Pendiente` a `Aceptado` con un `track_id` real, y
   que el print format (S2.12) muestra el QR real en vez del placeholder.
6. Recién ahí, **S5.4** (certificación formal ante la DGII para los dos
   RNC) y el resto de Fase 5.

## 5. Qué sigue siendo verdad, sin adornos

- Sin mandar los correos de S0.3, **ambos caminos siguen parados**. El
  Camino B siempre estuvo fuera de nuestro control; el Camino A no
  tenía por qué estarlo.
- Si ninguno de los dos proveedores da sandbox propio sin RNC real
  (posible — no está confirmado), entonces sí, no hay forma de probar
  contra la DGII real hasta que el cliente se registre. En ese caso, la
  Fase 2 se queda cerrada como estructura (como está hoy) hasta entonces,
  y eso es correcto: no se inventa una emisión falsa para simular que
  "funciona".
