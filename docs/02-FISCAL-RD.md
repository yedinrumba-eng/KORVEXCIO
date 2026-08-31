# 02 — Fiscal República Dominicana

> Investigado 2026-08-31 contra fuentes DGII y prensa especializada. Los
> enlaces están al final. **Nada de esto sustituye a un contador dominicano** —
> es el mapa para que el desarrollo no se construya sobre supuestos.

---

## 1. El reloj: calendario de obligatoriedad del e-CF

Ley **32-23** de Facturación Electrónica. Implementación escalonada:

| Categoría de contribuyente | Obligatorio desde |
|---|---|
| Grandes contribuyentes nacionales | Mayo 2024 |
| Grandes locales y medianos | **1 de noviembre de 2026** (emisión exclusiva) |
| **Pequeños, micro y no clasificados** | **15 de noviembre de 2026** |

Dos detalles que importan:

- Los comprobantes **no electrónicos tipo "B" dejan de ser válidos el 31 de
  octubre de 2026**, salvo declaratoria formal de contingencia.
- El plazo del 15/11/2026 para pequeños **ya es una prórroga**, otorgada el
  6 de mayo de 2026. No conviene apostar a otra.

**VAPELAND cae en la última fila.** Del 31/08/2026 al 15/11/2026 hay **76 días**.

**Sanción por incumplir:** 5 a 50 salarios mínimos (aprox. RD$100,000–600,000
según la gravedad).

---

## 2. Qué es un e-CF

Un documento **XML firmado digitalmente**, transmitido a la DGII para
validación **en línea al momento de emitirse**. Sustituye al NCF en papel.

### Los tipos que importan para este proyecto

| Tipo | Nombre | Cuándo se usa aquí |
|---|---|---|
| **E32** | Factura de consumo | **El 95% de las ventas del POS.** Consumidor final |
| **E31** | Factura de crédito fiscal | Cuando el cliente da RNC para deducir ITBIS |
| **E34** | Nota de crédito | Devoluciones y anulaciones |
| **E33** | Nota de débito | Ajustes al alza |
| **E41** | Comprobante de compras | Compras a proveedores informales |
| E43 / E44 / E45 / E46 / E47 | Gastos menores · regímenes especiales · gubernamentales · exportaciones · pagos al exterior | Fuera de alcance |

### La regla E31 vs E32 que el POS tiene que automatizar

> ¿El cliente pidió factura "para deducir el ITBIS" o dio su RNC de empresa?
> → **E31.** Si no → **E32.**

| Monto del E32 | ¿RNC del comprador obligatorio? |
|---|---|
| < RD$250,000 | **No** |
| ≥ RD$250,000 | **Sí** (Norma 05-19) |

👉 **Requisito de producto:** el POS debe **exigir el RNC automáticamente**
cuando el total cruza los RD$250,000. No dejarlo al criterio del cajero.
(En este negocio va a pasar poco, pero una venta de mayoreo de hookahs lo
cruza sin avisar.)

### RFCE — Resumen de Factura de Consumo Electrónica

Para los E32 **menores a RD$250,000**, la DGII no recibe factura por factura:
se acumulan y se envía un **resumen** a un endpoint distinto
(`fc.dgii.gov.do/recepcionfc`).

👉 **Esto es lo que hace viable un POS de alto volumen.** Si el software no
soporta RFCE, cada venta de RD$300 sería una transmisión individual.
**Verificar que el proveedor que se elija lo soporte antes de firmar nada.**

---

## 3. Reglas operativas (de las FAQ oficiales de la DGII)

| Tema | Regla |
|---|---|
| **Plazo de envío** | No hay un máximo explícito publicado. La DGII responde en **décimas de segundo**. Una vez emitido, se remite. |
| **Validez mientras espera respuesta** | El emisor **no tiene que esperar** la aceptación de la DGII. Basta obtener el **TrackID** para entregar el comprobante al receptor. |
| **Sin internet en el negocio** | Se declara **contingencia por la OFV**, se sigue facturando en **papel Serie B**, y al volver la conexión se envían los acumulados. Se notifica el fin de la contingencia por la OFV. |
| **DGII caída** | Se emite normal y se entrega al receptor; se transmite cuando el servicio vuelva. |
| **Dispositivos móviles** | Con autorización previa se pueden acumular por lote en **períodos menores a 24 horas**. |
| **Representación impresa (RI)** | Tiene **la misma validez** que el XML. Lleva **código QR abajo a la izquierda** para verificar autenticidad. |
| **Secuencias e-NCF** | Se solicitan por la OFV (Solicitudes → Trámites). Vigencia: desde la autorización hasta el **31 de diciembre del año siguiente**. |
| **Acuse de recibo** | Respuesta automática de recepción. **No** implica aceptación comercial. |
| **Aprobación comercial** | Opcional. Si se envía, va al emisor **y** a la DGII en XML. No enviarla no tiene implicaciones. |
| **Anulación** | Secuencias no usadas o emitidas-pero-no-enviadas se marcan como anuladas por web service. |

### Lo que esto significa para el diseño del POS

1. **El POS no puede bloquearse esperando a la DGII.** Vende, obtiene TrackID
   e imprime. La confirmación llega después, asíncrona.
2. **Modo contingencia obligatorio.** Un negocio en RD se queda sin internet.
   El POS necesita seguir vendiendo, marcar esas ventas como pendientes y
   drenar la cola al reconectar. Esto es requisito, no lujo.
3. **El QR va en el recibo térmico.** No es decorativo: es cómo se verifica.
4. **Control de secuencias e-NCF con alerta de agotamiento.** Quedarse sin
   secuencia un sábado a las 8 pm cierra la tienda.

---

## 4. Requisitos para poder emitir

Tres cosas, sin excepción:

1. **RNC activo** ⚠️ *el cliente no ha confirmado que lo tenga*
2. **Certificado digital** (persona jurídica o persona física autorizada)
3. **Software emisor certificado ante DGII**, o el Facturador Gratuito

### Certificado digital

| | |
|---|---|
| **Costo** | US$30 – US$70 al año |
| **Vigencia** | 1 año (renovable) |
| **Tiempo de emisión** | 3–10 días hábiles por la vía tradicional |
| **Requisitos** | RNC · cédula del representante legal · registro mercantil vigente · poder notarial si aplica |

**Entidades de certificación autorizadas por INDOTEL:**

1. AVANSI SRL — `info@avansi.com.do` · (809) 682-3928
2. Cámara de Comercio y Producción de Santo Domingo — `digifirma@camarasantodomingo.do` · (809) 682-2688
3. OGTIC — `ca.ogtic.gob.do`
4. Lleidanet Dominicana SRL
5. NOVOSIT SRL
6. Thomas Signe Copel S.A.S
7. Asociación de Bancos Múltiples (ABA) — `firmadigital.aba.org.do`

> La DGII llegó a ofrecer **30,000 certificados digitales gratuitos**, pero
> **exclusivos para el Facturador Gratuito**. Verificar si el programa sigue
> abierto y bajo qué condiciones antes de asumirlo.

---

## 5. Por qué el Facturador Gratuito de la DGII NO sirve aquí

Es real, es gratis, y para este negocio es una trampa:

| Límite | Impacto |
|---|---|
| **~150 comprobantes al mes** | Una tienda con 20 ventas diarias lo agota en 8 días |
| **Solo interfaz web, sin API** | Facturas capturadas una por una, a mano |
| **100% en línea, sin modo offline** | Sin internet, no factura |
| **Solo pesos dominicanos** | No factura en dólares |
| Sin inventario, sin caja, sin turnos | No es un POS |

Sirve para un profesional independiente que emite 20 facturas al mes. No para
un punto de venta.

---

## 6. La ruta elegida: proveedor certificado por API

Decisión #2 del `HANDOFF.md`.

### Opción principal — ECF SSD vía `ecf-dgii` (Python, MIT)

| | |
|---|---|
| **Paquete** | `ecf-dgii` en PyPI, v1.0.0 (7 mayo 2026) |
| **Licencia** | **MIT** |
| **Autor** | Smart Software Development SRL (RD) |
| **Repo** | `SSD-Smart-Software-Development-SRL/ecf_dgii` |
| **Qué hace** | Mandas JSON → ellos firman el XML con tu certificado, autentican por semilla ante DGII, envían, reintentan automáticamente |
| **Ambientes** | Test · Cert · Prod |
| **Tipos** | ⚠️ **NO VERIFICADO.** La página de PyPI **no documenta explícitamente E32 ni RFCE.** Una fuente secundaria menciona E31/E32; la primaria no lo confirma. |
| **Requiere** | Una **cuenta y API key (JWT Bearer) de ECF SSD** — no es una librería autónoma contra la DGII |

👉 **Es Python. Frappe es Python.** Encaja nativo en una app de Frappe sin
puentes ni microservicios. Es la razón principal por la que esta ruta es
coherente con la decisión de ERPNext.

### Alternativa — Alanube

- Proveedor certificado por DGII, modelo **BaaS** (API, sin interfaz).
- **Pago por emisión**, sin cuota adelantada.
- REST + **webhooks** para notificación de estado.
- Ambientes de certificación y producción separados.
- ⚠️ Soporte de E32/RFCE no confirmado en su página pública — **preguntarlo por
  escrito antes de comprometerse.**

### Otros del mercado local
Galileo · Axentra · ef2 · GyleERP · eCF MSeller · Alegra. Varios ofrecen plan
gratuito de 5–10 e-CF/mes para pruebas.

### Costos
La comparativa pública **no publica cifras por documento**. Los modelos son
suscripción fija (alto volumen o ilimitado) o pago por documento (bajo volumen).
👉 **Pedir cotización escrita a 2–3 proveedores** con: volumen estimado,
excedentes, almacenamiento de XML/RI, costo de API, SLA de soporte, y quién
absorbe los cambios normativos.

### El diseño que se construye

Sea cual sea el que se elija, `korvex_ecf` expone una **interfaz de proveedor**
con implementaciones intercambiables. Razón: un tenant futuro puede llegar con
su proveedor ya contratado, y cambiarlo no puede significar reescribir la app.

```
korvex_ecf/
  providers/
    base.py          # emitir(doc) -> TrackID · consultar(trackid) · anular(ncf)
    ssd.py           # ECF SSD vía ecf-dgii
    alanube.py       # Alanube REST
  doctype/
    ecf_settings/    # certificado, RNC, ambiente, credenciales del proveedor
    ecf_sequence/    # rangos e-NCF autorizados + alerta de agotamiento
    ecf_document/    # cola: pendiente → enviado → aceptado/rechazado
  hooks: Sales Invoice on_submit -> encolar e-CF
```

---

## 7. Impuestos que el POS tiene que calcular

### ITBIS
Tasa general **18%**. En ERPNext: **Item Tax Template** por categoría, no una
tasa global — porque no todo lo que vende esta tienda paga lo mismo.
⚠️ Confirmar con el contador qué categorías son exentas o tasa reducida
(algunos alimentos de la cafetería podrían serlo).

### ISC — Impuesto Selectivo al Consumo

#### Primero: la diferencia que confunde a todo el mundo

| | **ITBIS** (18%) | **ISC** (selectivo) |
|---|---|---|
| Dónde se cobra | Al final, en la caja | **Al principio**, cuando el producto entra al país |
| Quién lo paga | El cliente | **El importador o el fabricante** |
| ¿Sale en la factura? | Sí, línea aparte | **No.** Viene escondido dentro del precio |
| ¿Lo toca el POS? | **Sí** | **No** |

**La regla que decide el diseño del motor de impuestos:** el ISC lo declaran y
pagan **fabricantes, productores e importadores** — **no el detallista**.

#### Ley 30-26 — el 55% a los vapes

Promulgada el **18 de junio de 2026**. Ley *"de medidas pro-crecimiento
económico, simplificación fiscal y mitigación de la crisis internacional"*.

| | |
|---|---|
| **Tasa** | **55% ad-valorem** |
| **Base imponible** | El **precio de venta al por menor** — el precio final al consumidor, con todos sus componentes. La ley **prohíbe deducciones o fraccionamientos** del precio |
| **Norma** | Párrafo XI al artículo 375 del Código Tributario |
| **Productos** | Cigarrillos electrónicos personales · dispositivos de vaporización eléctricos · preparaciones líquidas **con o sin nicotina** usadas como carga o relleno |
| **Partidas arancelarias** | `8543.40.11` · `8543.40.12` · `2404.12.11` · `3824.99.94` (art. 379) |
| **Requisito extra** | El **artículo 44** exige a fabricantes e importadores **registro previo, fianza y licencia oficial** ante la Administración Tributaria |
| **Vigencia** | ⚠️ Desde la promulgación según PwC, **pero ninguna fuente pública lo confirma explícitamente**. Los calendarios de vigencia de prensa listan casinos, cheques y seguros — **no mencionan los vapes** |

**Lo contraintuitivo:** el 55% **no** se calcula sobre lo que el importador pagó
afuera, sino sobre **el precio al que se va a vender en la tienda**. El estado
mira hacia adelante, al precio final, pero cobra al principio de la cadena.

> *Es como si compras un celular en RD$5,000 para revenderlo en RD$12,000, y te
> cobran el impuesto sobre los RD$12,000 que vas a cobrar tú, no sobre los
> RD$5,000 que pagaste.*

#### Qué significa para VAPELAND — y para el POS

Al detallista le llega **dentro del costo de compra**. Compra el vape más caro
al importador, y ya.

👉 **En la factura al consumidor va UNA sola línea de impuesto: ITBIS 18%.**
No dos. El ISC ya viene adentro del precio del producto. **Esto simplifica el
motor de impuestos del POS** — no hay que calcular ISC por línea.

⚠️ **Confirmar con el contador antes de codificar.** Que la base sea el precio
minorista abre la pregunta de si en algún punto se le exige data al detallista.
Es exactamente el tipo de detalle que un contador dominicano sabe y que no se
puede asumir.

#### El impacto de negocio (esto es para el cliente, no para el código)

Ilustrativo — la forma del problema, no la fórmula exacta de liquidación:

| Un vape que se vende en RD$1,000 | Antes | Después de la 30-26 |
|---|---|---|
| Precio al público | RD$1,000 | RD$1,000 |
| ISC dentro del precio | RD$0 | **RD$550** |
| Queda para costo + margen de **toda** la cadena | RD$1,000 | **RD$450** |

**Los números no dan.** O el precio al público sube fuerte, o el margen
desaparece. **El cliente tiene que rehacer sus números antes de comprar
inventario, no después.** Es la conversación más valiosa que se puede tener con
él esta semana, y no tiene nada que ver con software.

#### Tabaco

| Concepto | Tasa |
|---|---|
| ISC de tabaco (marco general DGII) | **20% del PVP + monto específico por cajetilla** |
| Montos específicos jul–sep 2026 | RD$64.65 (cajetilla de 20) · RD$32.33 (cajetilla de 10) |
| ⚠️ Ley 30-26, art. 375 | PwC reporta un **20% ad-valorem adicional** sobre precio minorista |

⚠️ **El "adicional" no está claro en fuentes públicas** — puede ser un gravamen
nuevo o una reformulación del que ya existía. **Preguntárselo al contador**, no
resolverlo leyendo prensa.

### Propina legal
Si la cafetería llega a tener servicio de mesa, aplica el **10% de ley** sobre
consumo — línea separada en la factura, no incluida en el ITBIS.
⚠️ Confirmar si aplica al formato que va a montar.

---

## 8. Régimen Simplificado de Tributación (RST)

Puede convenirle al cliente. Tras la Ley 30-26 los umbrales suben
**a partir de 2027**:

| Perfil | Umbral nuevo | Umbral anterior |
|---|---|---|
| Personas jurídicas y unipersonales (servicios/producción) | RD$30,000,000 | RD$12,068,181.09 |
| **Comercio de bienes (por compras)** | **RD$60,000,000** | RD$55,485,890.09 |
| Profesionales independientes | RD$15,000,000 | — |

- Simplifica la determinación de **ISR e ITBIS**. En la modalidad de compras,
  el ITBIS se liquida sobre el **margen bruto estimado del sector**.
- Se solicita por la Oficina Virtual, módulo RNC. Respuesta en **15 días
  hábiles**, y hay que someterlo al menos **60 días antes** de la fecha límite
  de declaración de febrero del año fiscal.
- ⚠️ **Estar en RST NO exime del e-CF.** La reglamentación operativa de la
  Ley 30-26 seguía pendiente de la DGII al cierre de esta investigación —
  confirmar con el contador.

---

## Fuentes

- [DGII — Documentación sobre e-CF](https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx)
- [DGII — Preguntas frecuentes e-CF (PDF)](https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Preguntas%20frecuentes/Generales/Preguntas%20Frecuentes%20e-CF%20Generales%20.pdf)
- [DGII — Informe Técnico e-CF v1.0 (PDF)](https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Documentacin%20sobre%20eCF/Informe%20y%20Descripci%C3%B3n%20T%C3%A9cnica/Informe%20T%C3%A9cnico%20e-CF%20v1.0.pdf)
- [DGII — Formato e-CF v1.0 (PDF)](https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Documentacin%20sobre%20eCF/Formatos%20XML/Formato%20Comprobante%20Fiscal%20Electr%C3%B3nico%20(e-CF)%20v1.0.pdf)
- [DGII — Formato Resumen Factura Consumo (RFCE) (PDF)](https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Documentacin%20sobre%20eCF/Formatos%20XML/Formato%20Resumen%20Factura%20Consumo%20Electr%C3%B3nica%20v1.0.pdf)
- [DGII — Impuesto Selectivo al Consumo](https://dgii.gov.do/cicloContribuyente/obligacionesTributarias/principalesImpuestos/Paginas/impuestoSelectivoConsumo.aspx)
- [DGII — Facturador Gratuito](https://fg.dgii.gov.do/ecf/PortalFG/facturador)
- [INDOTEL — Entidades de Certificación](https://indotel.gob.do/firma-digital/entidades-de-certificacion/)
- [Alegra — Obligatoriedad de factura electrónica: fechas límite](https://blog.alegra.com/republica-dominicana/obligatoriedad-de-factura-electronica/)
- [Galileo — Facturación electrónica e-CF 2026, guía completa](https://galileocontabilidad.com/facturacion-electronica/)
- [Axentra — E31 o E32: cómo decidir qué comprobante emitir](https://axentra.com.do/blog/e31-o-e32-como-decidir-comprobante-emitir/)
- [El Nacional — Ley 30-26 establece impuesto del 55% a cigarrillos electrónicos](https://elnacional.com.do/economia/vape-nueva-ley-establece-impuesto-55-cigarrillos-electronicos_573815.html)
- [elDinero — Ley 30-26 redefine el sistema tributario](https://eldinero.com.do/370481/ley-30-26-redefine-el-sistema-tributario-ajustes-clave-con-impacto-directo-en-empresas-y-contribuyentes/)
- [PwC — Modificaciones introducidas por la Ley 30-26 (PDF)](https://www.pwc.com/ia/es/publicaciones/Noticias-Tax-Legal/Tax-and-legal-2026/modificaciones-Ley-30-26.pdf)
- [Deloitte — Ley tributaria: cambios en ISR, ITBIS y fiscalidad internacional](https://www.deloitte.com/latam/es/services/tax/perspectives/do-3jul26-ley-tributaria-cambios-isr-itbis-fiscalidad.html)
- [El Caribe — Calendario de entrada en vigencia de la Ley 30-26](https://www.elcaribe.com.do/panorama/dinero/calendario-entrada-vigencia-cambios-impositivos-ley-30-26/)
- [Ministerio de Hacienda — Ley No. 30-26](https://www.hacienda.gob.do/marco-legal/ley-no-30-26/)
- [Siempre al Día — Régimen Simplificado de Tributación (RST) y Ley 30-26](https://siemprealdia.co/republica-dominicana/impuestos/regimen-simplificado-de-tributacion-rst/)
- [Siempre al Día — Cómo obtener el certificado digital](https://siemprealdia.co/republica-dominicana/impuestos/como-obtener-el-certificado-digital/)
- [gestionDO — Facturador Gratuito DGII: requisitos y límites](https://gestiondo.com.do/finanzas-legalidad/facturador-gratuito-dgii-republica-dominicana/)
- [Alanube — API de facturación electrónica DGII](https://www.alanube.co/rd/)
- [ecf-dgii en PyPI](https://libraries.io/pypi/ecf-dgii)
