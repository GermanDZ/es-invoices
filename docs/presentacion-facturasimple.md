# FacturaSimple

### Facturación electrónica simple y conforme a Verifactu para autónomos y pymes

---

## El problema

A partir de **2027**, la normativa española (Ley Crea y Crece / Verifactu) obliga a empresas
y autónomos a emitir facturas **inalterables, encadenadas mediante hash y reportables a la
AEAT**. Las sociedades quedan obligadas desde el **1 de enero de 2027** y los autónomos
desde el **1 de julio de 2027**. La mayoría del software actual es complejo, caro o está
pensado para gestorías, no para el profesional que solo necesita **emitir una factura
correcta en menos de 5 minutos**.

## La solución

**FacturaSimple** es una aplicación web que permite a autónomos y micro-empresas españolas
emitir facturas legalmente válidas y enviarlas directamente a la AEAT, sin conocimientos
técnicos. Todo el cumplimiento de Verifactu (firma, encadenado, envío) queda **oculto tras
una experiencia simple**, mientras la gestoría mantiene acceso a los registros fiscales.

- **Usuario principal:** autónomos y pymes que emiten facturas.
- **Contexto:** España, EUR, integración directa con la AEAT.
- **Pilar diferencial:** cumplimiento Verifactu de extremo a extremo, sin fricción.

---

## Funcionalidades

### 1. Cuentas y acceso
- Registro autoservicio por email y autenticación basada en sesión.
- Validadores de contraseña de Django; logout seguro (solo POST).
- Baja de cuenta autoservicio con **periodo de gracia de 30 días** (RGPD, art. 17).
- Purga automática de datos: facturas a los 5 años, cuentas tras la gracia.

### 2. Gestión de clientes
- Alta, edición y baja de clientes, **aislados por propietario** (sin fuga de datos).
- Clientes **B2B** (NIF/CIF obligatorio) y **B2C** (NIF/CIF opcional).
- Validación de identificadores fiscales españoles (DNI, NIE, CIF) con dígito de control.
- Los datos fiscales del receptor se **congelan en la factura** al emitir (inmutables).

### 3. Emisión de facturas
- Constructor multilínea: descripción, cantidad, precio, **IVA por línea** (0/4/10/21%).
- **IRPF opcional** a nivel de factura (1/2/3%) e identidad del emisor en línea.
- Cálculo de impuestos con precisión `Decimal`, agrupado por tipo de IVA.
- **Numeración secuencial sin huecos** por serie, con bloqueo de fila transaccional
  (`select_for_update`) y restricción única `(serie, número)` ante concurrencia.
- Emisión **atómica**: borrador, validación y emisión en una sola transacción; la factura
  queda inmutable en su identidad y genera su registro Verifactu automáticamente.
- Soporte de múltiples series (p. ej. serie estándar y serie "R" de rectificativas).

### 4. Cumplimiento Verifactu
- Generación de registros de **alta**, **anulación** y metadatos de **rectificativa**.
- Validación de campos legales (datos de emisor/receptor, tipo de factura F1/R1).
- **Cadena de hash por emisor**: cada huella SHA-256 incorpora la del registro anterior,
  haciendo detectable cualquier manipulación; serialización por bloqueo de fila.
- **Firma XAdES (XML-DSig)** con verificación; módulo de cumplimiento **versionado**
  y aislado para absorber futuros cambios normativos sin tocar el resto de la app.

### 5. Envío a la AEAT
- Integración **directa** vía **mTLS** con certificado cualificado (PKCS#12) y SOAP/XML
  validado contra los **XSD** oficiales; entornos de **preproducción y producción**.
- Gestión de certificados con **cifrado AES-256-GCM en reposo** y acceso de mínimo
  privilegio; validación de formato, contraseña y caducidad en la subida.
- Flujo de envío con reintentos acotados y captura de resultado: **aceptado** (con CSV),
  **rechazado** (con código de error AEAT) o **pendiente**; intentos registrados de forma
  append-only sin mutar la factura ni el registro.
- **Interruptor de seguridad** (`AEAT_SUBMISSION_LIVE`) que bloquea envíos reales en
  desarrollo/CI.
- **Código QR Verifactu** en el PDF para verificación de la factura ante la AEAT.

### 6. Facturas rectificativas y anulaciones
- **Rectificativa** (UC-004): corrige una factura válida en serie "R" propia, referenciando
  la original, por **sustitución** o **por diferencias**, con su registro y envío automático.
- **Anulación** (UC-005): genera registro de anulación sin crear nueva factura; consciente
  de envíos pendientes (cancela el intento en curso si procede) y se rechaza si ya existe
  una rectificativa.
- Botones **Rectificar** y **Anular** en el detalle, con confirmación de seguridad.

### 7. PDF y envío por email
- Generación de **PDF** con **WeasyPrint**, incluyendo todos los campos legales, resumen de
  impuestos, leyenda Verifactu y QR.
- Envío del PDF por **email** (backend configurable), con destinatario tomado del formulario
  o del cliente; marca de tiempo `sent_at` e instrumentación sin PII.

### 8. Seguimiento, listados y panel
- Estados de factura: **borrador → emitida → enviada**, con propiedad de estado derivada.
- Listado por propietario (solo emitidas y no anuladas) y **detalle** con insignia de estado
  de envío (sin registro / pendiente / enviada / aceptada / rechazada) e historial.
- Panel con navegación (Bootstrap 5), accesos rápidos y página de inicio autenticada.

---

## Arquitectura y calidad

- **Monolito modular** en Django 5 + PostgreSQL, dividido en módulos (cuentas, facturación,
  clientes, cumplimiento, envío, documentos, certificados).
- **Cumplimiento aislado y versionado** (AD-2) y **adaptador AEAT intercambiable** (AD-3):
  la integración directa por mTLS quedó probada en PoC, con fallback a pasarela externa.
- **Garantías clave:** numeración sin huecos, cadena de hash anti-manipulación e
  inmutabilidad posterior a la emisión (correcciones/anulaciones en campos separados).
- **RGPD por diseño:** residencia de datos en la UE, cifrado en tránsito (TLS/mTLS) y en
  reposo (AES-256-GCM), mínimo privilegio, retención y purga automatizada.
- **Calidad:** **231 pruebas** en verde (unitarias, de integración y de UI), runbook de
  despliegue y checklist RGPD documentados.

## Estado del proyecto

Fase de **Construcción completada** con decisión **GO** hacia Transición (beta): todas las
funcionalidades núcleo implementadas, probadas y documentadas. Métricas objetivo: primera
factura en **< 5 min**, **≥ 99%** de aceptación a la primera ante la AEAT y **≥ 50%** de
activación en la primera semana.
