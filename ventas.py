import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.database import (
    load_data, save_data, get_next_id, now_str, date_str,
    CONDICIONES_IVA, ALICUOTAS_IVA
)

def show():
    st.markdown("## 💰 Módulo de Ventas")

    tab = st.tabs(["👥 Clientes", "🧾 Emisión de Factura", "📋 Cuenta Corriente", "📊 Cuentas Corrientes Gral."])

    with tab[0]:
        show_clientes()
    with tab[1]:
        show_facturacion()
    with tab[2]:
        show_cc_individual()
    with tab[3]:
        show_cc_general()


# ─── CLIENTES ────────────────────────────────────────────────
def show_clientes():
    st.markdown("### 👥 Gestión de Clientes")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-header"><h3>➕ Nuevo Cliente</h3></div>', unsafe_allow_html=True)
        with st.form("form_cliente", clear_on_submit=True):
            razon_social = st.text_input("Razón Social *")
            cuit = st.text_input("CUIT *", placeholder="XX-XXXXXXXX-X")
            direccion = st.text_input("Dirección")
            email = st.text_input("Email")
            cond_iva = st.selectbox("Condición IVA *", CONDICIONES_IVA)
            telefono = st.text_input("Teléfono")

            submitted = st.form_submit_button("💾 Guardar Cliente", use_container_width=True)
            if submitted:
                if not razon_social or not cuit:
                    st.error("Razón Social y CUIT son obligatorios.")
                else:
                    clientes = load_data("clientes")
                    # Check duplicate CUIT
                    if any(c["cuit"] == cuit for c in clientes):
                        st.error("Ya existe un cliente con ese CUIT.")
                    else:
                        nuevo = {
                            "id": get_next_id("clientes"),
                            "razon_social": razon_social.upper(),
                            "cuit": cuit,
                            "direccion": direccion,
                            "email": email,
                            "condicion_iva": cond_iva,
                            "telefono": telefono,
                            "fecha_alta": date_str(),
                        }
                        clientes.append(nuevo)
                        save_data("clientes", clientes)
                        st.success(f"✅ Cliente '{razon_social.upper()}' guardado correctamente.")
                        st.rerun()

    with col2:
        st.markdown('<div class="section-header"><h3>📋 Lista de Clientes</h3></div>', unsafe_allow_html=True)
        clientes = load_data("clientes")
        if clientes:
            buscar = st.text_input("🔍 Buscar cliente", key="buscar_cliente")
            filtered = [c for c in clientes if buscar.lower() in c["razon_social"].lower() or buscar in c["cuit"]] if buscar else clientes

            for c in filtered:
                badge_map = {
                    "Responsable Inscripto": "badge-info",
                    "Monotributista": "badge-success",
                    "Exento en IVA": "badge-neutral",
                    "Consumidor Final": "badge-warning",
                }
                badge = badge_map.get(c["condicion_iva"], "badge-neutral")
                st.markdown(f"""
                <div style='background:white;border:1px solid #e8eaf6;border-radius:8px;padding:12px;margin:6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.05)'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                        <div>
                            <strong style='color:#1a237e;font-size:0.95rem'>{c['razon_social']}</strong>
                            <br><small style='color:#666'>CUIT: {c['cuit']} · {c.get('email','-')}</small>
                            <br><small style='color:#888'>{c.get('direccion','-')}</small>
                        </div>
                        <span class="{badge}">{c['condicion_iva']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay clientes registrados aún.")


# ─── FACTURACIÓN ─────────────────────────────────────────────
def show_facturacion():
    st.markdown("### 🧾 Emisión de Factura")

    clientes = load_data("clientes")
    if not clientes:
        st.warning("⚠️ No hay clientes cargados. Por favor, agregue clientes primero.")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-header"><h3>Datos de la Factura</h3></div>', unsafe_allow_html=True)

        opciones_clientes = {f"{c['razon_social']} — CUIT: {c['cuit']}": c for c in clientes}
        cliente_sel = st.selectbox("Cliente *", list(opciones_clientes.keys()))
        cliente = opciones_clientes[cliente_sel]

        st.markdown(f"""
        <div class='info-box'>
            <strong>Condición IVA:</strong> {cliente['condicion_iva']}<br>
            <strong>Dirección:</strong> {cliente.get('direccion','-')}<br>
            <strong>Email:</strong> {cliente.get('email','-')}
        </div>
        """, unsafe_allow_html=True)

        # Tipo comprobante según condición IVA
        cond = cliente["condicion_iva"]
        if cond == "Responsable Inscripto":
            tipo_comprobante = st.selectbox("Tipo Comprobante", ["Factura A", "Nota de Crédito A", "Nota de Débito A"])
        else:
            tipo_comprobante = st.selectbox("Tipo Comprobante", ["Factura B", "Nota de Crédito B", "Nota de Débito B"])

        numero_comprobante = st.text_input("N° Comprobante", value=f"0001-{get_next_id('facturas_venta'):08d}")
        fecha_factura = st.date_input("Fecha", value=date.today())
        fecha_vto = st.date_input("Fecha Vencimiento")
        concepto = st.text_area("Concepto / Descripción")

    with col2:
        st.markdown('<div class="section-header"><h3>Importes</h3></div>', unsafe_allow_html=True)

        # Alícuotas disponibles según condición IVA
        cond = cliente["condicion_iva"]
        if cond in ["Responsable Inscripto"]:
            alicuotas_disp = ["21%", "10.5%", "27%", "Exento"]
        else:
            alicuotas_disp = ["Exento"]

        alicuota_sel = st.selectbox("Alícuota IVA", alicuotas_disp)
        neto = st.number_input("Importe Neto ($)", min_value=0.0, step=0.01, format="%.2f")

        tasa = ALICUOTAS_IVA.get(alicuota_sel, 0)
        iva_monto = round(neto * tasa, 2)
        total = round(neto + iva_monto, 2)

        st.markdown(f"""
        <div style='background:#f8f9ff;border:1px solid #c5cae9;border-radius:10px;padding:16px;margin-top:10px'>
            <div style='display:flex;justify-content:space-between;margin-bottom:8px'>
                <span style='color:#555'>Neto:</span>
                <strong>${neto:,.2f}</strong>
            </div>
            <div style='display:flex;justify-content:space-between;margin-bottom:8px'>
                <span style='color:#555'>IVA ({alicuota_sel}):</span>
                <strong>${iva_monto:,.2f}</strong>
            </div>
            <hr style='margin:8px 0;border-color:#e8eaf6'>
            <div style='display:flex;justify-content:space-between'>
                <span style='color:#1a237e;font-weight:700;font-size:1.1rem'>TOTAL:</span>
                <strong style='color:#1a237e;font-size:1.1rem'>${total:,.2f}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**AFIP — Punto de Venta**")
        punto_venta = st.text_input("Punto de Venta", value="0001")
        st.markdown("""
        <div class='warning-box'>
            <small>⚠️ <strong>AFIP:</strong> Para emitir comprobantes electrónicos válidos conecte su certificado digital AFIP en la sección Configuración. Esta vista genera el registro contable interno.</small>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🖨️ Emitir Factura", use_container_width=True, type="primary"):
            if neto <= 0:
                st.error("El importe neto debe ser mayor a 0.")
            else:
                facturas = load_data("facturas_venta")
                nueva = {
                    "id": get_next_id("facturas_venta"),
                    "numero_comprobante": numero_comprobante,
                    "tipo_comprobante": tipo_comprobante,
                    "punto_venta": punto_venta,
                    "fecha": str(fecha_factura),
                    "fecha_vencimiento": str(fecha_vto),
                    "cliente_id": cliente["id"],
                    "cliente_razon_social": cliente["razon_social"],
                    "cliente_cuit": cliente["cuit"],
                    "condicion_iva": cond,
                    "concepto": concepto,
                    "alicuota": alicuota_sel,
                    "neto": neto,
                    "iva": iva_monto,
                    "total": total,
                    "saldo_pendiente": total,
                    "estado": "Pendiente",
                    "fecha_emision": now_str(),
                }
                facturas.append(nueva)
                save_data("facturas_venta", facturas)
                st.success(f"✅ Factura {numero_comprobante} emitida. Total: ${total:,.2f}")
                st.balloons()


# ─── CUENTA CORRIENTE INDIVIDUAL ─────────────────────────────
def show_cc_individual():
    st.markdown("### 📋 Cuenta Corriente por Cliente")

    clientes = load_data("clientes")
    if not clientes:
        st.info("No hay clientes registrados.")
        return

    opciones = {f"{c['razon_social']} — CUIT: {c['cuit']}": c for c in clientes}
    sel = st.selectbox("Seleccionar Cliente", list(opciones.keys()), key="cc_cliente_sel")
    cliente = opciones[sel]

    facturas = [f for f in load_data("facturas_venta") if f["cliente_id"] == cliente["id"]]
    cobranzas = [c for c in load_data("cobranzas") if c.get("cliente_id") == cliente["id"]]

    # Construir movimientos
    movs = []
    for f in facturas:
        movs.append({
            "Fecha": f["fecha"],
            "Tipo": f["tipo_comprobante"],
            "Comprobante": f["numero_comprobante"],
            "Concepto": f.get("concepto", "-"),
            "Debe": f["total"],
            "Haber": 0,
            "Saldo": 0,
        })
    for c in cobranzas:
        movs.append({
            "Fecha": c["fecha"],
            "Tipo": "Cobranza",
            "Comprobante": c.get("referencia", "-"),
            "Concepto": c.get("forma_pago", "-"),
            "Debe": 0,
            "Haber": c["importe"],
            "Saldo": 0,
        })

    movs.sort(key=lambda x: x["Fecha"])

    # Calcular saldo acumulado
    saldo = 0
    for m in movs:
        saldo += m["Debe"] - m["Haber"]
        m["Saldo"] = saldo

    # KPIs
    total_facturado = sum(f["total"] for f in facturas)
    total_cobrado = sum(c["importe"] for c in cobranzas)
    saldo_final = total_facturado - total_cobrado

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Facturado", f"${total_facturado:,.2f}")
    col2.metric("Total Cobrado", f"${total_cobrado:,.2f}")
    col3.metric("Saldo Pendiente", f"${saldo_final:,.2f}", delta=f"-${total_cobrado:,.2f}" if total_cobrado else None)

    st.markdown(f"""
    <div class='info-box'>
        <strong>{cliente['razon_social']}</strong> · CUIT: {cliente['cuit']} · {cliente['condicion_iva']}<br>
        {cliente.get('email','')} · {cliente.get('direccion','')}
    </div>
    """, unsafe_allow_html=True)

    if movs:
        df = pd.DataFrame(movs)
        df["Debe"] = df["Debe"].apply(lambda x: f"${x:,.2f}" if x else "-")
        df["Haber"] = df["Haber"].apply(lambda x: f"${x:,.2f}" if x else "-")
        df["Saldo"] = df["Saldo"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay movimientos para este cliente.")


# ─── CUENTA CORRIENTE GENERAL ────────────────────────────────
def show_cc_general():
    st.markdown("### 📊 Resumen Cuentas Corrientes — Todos los Clientes")

    clientes = load_data("clientes")
    facturas = load_data("facturas_venta")
    cobranzas = load_data("cobranzas")

    resumen = []
    for c in clientes:
        total_f = sum(f["total"] for f in facturas if f["cliente_id"] == c["id"])
        total_c = sum(co["importe"] for co in cobranzas if co.get("cliente_id") == c["id"])
        saldo = total_f - total_c
        if saldo != 0:
            resumen.append({
                "Cliente": c["razon_social"],
                "CUIT": c["cuit"],
                "Condición IVA": c["condicion_iva"],
                "Total Facturado": total_f,
                "Total Cobrado": total_c,
                "Saldo": saldo,
            })

    if resumen:
        df = pd.DataFrame(resumen).sort_values("Saldo", ascending=False)
        total_general = df["Saldo"].sum()

        st.metric("💰 Saldo Total a Cobrar", f"${total_general:,.2f}")
        st.markdown("")

        df_display = df.copy()
        df_display["Total Facturado"] = df_display["Total Facturado"].apply(lambda x: f"${x:,.2f}")
        df_display["Total Cobrado"] = df_display["Total Cobrado"].apply(lambda x: f"${x:,.2f}")
        df_display["Saldo"] = df_display["Saldo"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Todas las cuentas corrientes están en cero.")
