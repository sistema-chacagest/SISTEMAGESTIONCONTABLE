# 🏢 Sistema de Gestión Empresarial — Streamlit

## Estructura del Proyecto

```
gestion_app/
├── app.py                  ← Punto de entrada principal
├── requirements.txt
├── data/                   ← Datos en JSON (auto-creada)
├── utils/
│   └── database.py         ← Funciones de persistencia y constantes
└── pages/
    ├── inicio.py           ← Dashboard principal
    ├── ventas.py           ← Módulo Ventas (Clientes, Facturación, CC)
    ├── compras.py          ← Módulo Compras (Proveedores, Gastos, CC)
    ├── tesoreria.py        ← Módulo Tesorería (Pagos, Cobranzas, Cheques)
    ├── bancos.py           ← Módulo Bancos (Movimientos, Cheques)
    └── reportes.py         ← Reportes y Balance General
```

## Módulos incluidos

### 💰 Ventas
- ABM de Clientes (razón social, CUIT, IVA, dirección, email)
- Emisión de comprobantes (Fact. A/B) con IVA al 21%, 10.5%, 27% o Exento
- Conexión AFIP (punto de venta configurable)
- Cuenta Corriente individual por cliente
- Cuenta Corriente General (solo saldos distintos de cero)

### 🛒 Compras
- ABM de Proveedores con cuenta de gastos asignada
- Carga de facturas de compra con desglose por alícuota
- Manejo de Monotributistas/Consumidor Final (exento automático)
- Retenciones de IVA, IIBB e Impuestos Internos
- Cuenta Corriente individual y general de proveedores

### 🏦 Tesorería
- Órdenes de Pago: selección de proveedor + facturas a cancelar
- Formas de pago: Transferencia bancaria, Efectivo, Cheque Propio, Cheque de Tercero
- Visualización de cheques en cartera al pagar con cheque de tercero
- Emisión de cheques propios con formulario completo
- Cobranzas de facturas de venta, registro de cheques recibidos

### 🏧 Bancos
- Movimientos de todos los bancos (Galicia, Provincia, Santander, Supervielle, Nación, Comafi, Mercado Pago)
- Ingreso manual de movimientos
- Saldos por banco en tiempo real
- Cheques en cartera (de terceros) con días para el vencimiento
- Cheques diferidos emitidos con opción de Conciliar (débito automático)

### 📊 Reportes
- Ingresos vs Egresos con posición IVA
- Egresos por cuenta de gastos (con barras de porcentaje)
- Movimientos bancarios filtrados por período y banco
- Balance General del período con resultado neto

## Cómo desplegar en Streamlit Cloud

1. Subir el contenido de `gestion_app/` a un repositorio GitHub
2. Ir a https://share.streamlit.io
3. Conectar el repo y seleccionar `app.py` como punto de entrada
4. Hacer click en **Deploy**

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notas AFIP
Para emitir comprobantes electrónicos válidos ante AFIP, se requiere:
- Certificado digital AFIP (.crt y .key)
- CUIT del emisor habilitado
- Integración con el web service WSFE de AFIP

Esta versión genera los registros contables internos. La integración AFIP
puede implementarse usando la librería `pyafipws` o similar.
