# Diseño visual de Korvex POS

## Estado

Dirección aprobada por Yedin el 2026-09-01. La pantalla de acceso toma como
referencia directa el login de Korvex TMS. El área de caja combina la densidad
operativa de Korvex TMS con la identidad visual de Korvex Survey.

## Referencias aprobadas

- Korvex TMS, rama `integration/waves-3-8`: estructura operativa, login,
  contraste, densidad y estados.
- Korvex Survey: azul Korvex, superficies de cristal, halos, profundidad y
  movimiento reducido.
- POSNext, rama `korvex`: estructura y comportamiento existentes del POS. El
  rediseño no puede romper autenticación, apertura de turno, venta ni trabajo
  offline.

## Dirección visual

La plataforma se identifica como **KORVEXCIO** y esta pantalla usa
**Punto de venta** como descriptor del módulo. Los colores del cliente solo pueden
aparecer como acentos configurables dentro de su contenido; el chrome del
producto siempre conserva la marca Korvex.

| Uso | Valor |
|---|---|
| Fondo principal | `#0f0f0f` |
| Fondo profundo | `#080a11` |
| Panel | `#181818` |
| Panel elevado | `#171a24` |
| Azul Korvex | `#2f43ea` |
| Azul hover | `#4557f5` |
| Texto principal | `#f4f6fd` |
| Texto secundario | `#a8b0cf` |
| Éxito | `#34d8a4` |
| Advertencia | `#ef9f27` |
| Error o bloqueo | `#ff6b6f` |

- Tipografía: Inter self-hosted, peso 400 para contenido y 500/600 para
  controles y encabezados.
- Dinero, NCF, TrackID, fechas y totales: números tabulares o monoespaciados.
- Radios: 10 px en controles, 14 px en paneles y 20 px solo en superficies de
  acceso o modales importantes.
- Objetivos táctiles: mínimo 44 px; acción primaria de caja, mínimo 48 px.
- Cristal: máximo dos superficies visibles. Nunca cristal sobre cristal.
- Movimiento: decorativo y lento únicamente en acceso y estados vacíos. Debe
  desaparecer con `prefers-reduced-motion: reduce`.
- Transparencia: debe existir fallback sólido con
  `prefers-reduced-transparency: reduce`.

## Acceso

La pantalla de acceso replica la composición del TMS:

1. Fondo nocturno con halos azul, cian y verde muy tenues.
2. Órbitas concéntricas decorativas detrás de una única tarjeta de cristal.
3. Símbolo K compacto, título `KORVEXCIO` y descriptor `Punto de venta`.
4. Título `Iniciar sesión` y explicación corta en español.
5. Usuario y contraseña con etiquetas persistentes, contraste AA y estados de
   foco visibles.
6. Botón azul de ancho completo y estado de carga sin cambiar el ancho.
7. Error dentro de la tarjeta, con `role="alert"`; nunca depender solo del
   color.
8. Pie `Acceso autorizado para personal Korvex`.

La autenticación, manejo de CSRF y apertura de turno existentes se conservan
sin cambios de comportamiento.

## Caja

- Barra superior de estado de 4 px: verde operativo, azul sincronizando,
  ámbar contingencia y rojo bloqueo fiscal.
- Navegación y catálogo mantienen la densidad de Korvex TMS.
- Carrito y totales usan paneles planos; el cristal se reserva para pago,
  apertura/cierre de turno y errores fiscales.
- La advertencia de RD$250,000 vive dentro del carrito y explica que el RNC es
  obligatorio antes de cobrar.
- El recibo fiscal permanece blanco y negro. La decoración de la aplicación no
  entra a la representación impresa.

## Verificación visual

Cada slice visual requiere:

1. prueba de componente para preservar el comportamiento observable;
2. `npm run lint` y `npm run build`;
3. smoke visual en 1440x900, 840x760 y 375x812;
4. prueba de navegación con teclado, foco visible y `prefers-reduced-motion`;
5. captura real del resultado para revisión de Yedin.
