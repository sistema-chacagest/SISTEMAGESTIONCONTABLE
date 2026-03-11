import streamlit as st
import pandas as pd
from datetime import date
from utils.database import (
    load_data, save_data, get_next_id, now_str, date_str,
    CONDICIONES_IVA, ALICUOTAS_IVA, CUENTAS_GASTOS
)

def show():
    st.markdown("## 🛒 Módulo de Compras")
    tab = st.tabs(["🏪 Proveedores", "📄 Carga de Gastos", "📋 Cuenta Corriente", "📊 Cuentas Corrientes Gral."])

    with tab[0]:
        show_proveedores()
    with tab[1]:
        show_gastos()
    with tab[2]:
        show_cc_individual()
    with tab[3]:
        show_cc_general()


# ─── PROVEEDORES ──────────────────────────────────────────────
def show_proveedores():
    st.markdown("### 🏪 Gestión de Proveedores")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-header"><h3>➕ Nuevo Proveedor</h3></div>', unsafe_allow_html=True)
        with st.form("form_proveedor", clear_on_submit=True):
            razon_social = st.text_input("Razón Social *")
            cuit = st.text_input("CUIT *", placeholder="XX-XXXXXXXX-X")
            direccion = st.text_input("Dirección")
            email = st.text_input("Email")
            cond_iva = st.selectbox("Condición IVA *", CONDICIONES_IVA)
            telefono = st.text_input("Teléfono")
            cuenta_gastos = st.selectbox("Cuenta de Gastos Principal", CUENTAS_GASTOS)

            submitted = st.form_submit_button("💾 Guardar Proveedor", use_container_width=True)
            if submitted:
                if not razon_social or not cuit:
                    st.error("Razón Social y CUIT son obligatorios.")
                else:
                    proveedores = load_data("proveedores")
                    if any(p["cuit"] == cuit for p in proveedores):
                        st.error("Ya existe un proveedor con ese CUIT.")
                    else:
                        nuevo = {
                            "id": get_next_id("proveedores"),
                            "razon_social": razon_social.upper(),
                            "cuit": cuit,
                            "direccion": direccion,
                            "email": email,
                            "condicion_iva": cond_iva,
                            "telefono": telefono,
                            "cuenta_gastos": cuenta_gastos,
                            "fecha_alta": date_str(),
                        }
                        proveedores.append(nuevo)
                        save_data("proveedores", proveedores)
                        st.success(f"✅ Proveedor '{razon_social.upper()}' guardado.")
                        st.rerun()

    with col2:
        st.markdown('<div class="section-header"><h3>📋 Lista de Proveedores</h3></div>', unsafe_allow_html=True)
        proveedores = load_data("proveedores")
        if proveedores:
            buscar = st.text_input("🔍 Buscar proveedor", key="buscar_prov")
            filtered = [p for p in proveedores if buscar.lower() in p["razon_social"].lower() or buscar in p["cuit"]] if buscar else proveedores
            for p in filtered:
                badge_map = {
                    "Responsable Inscripto": "badge-info",
                    "Monotributista": "badge-success",
                    "Exento en IVA": "badge-neutral",
                    "Consumidor Final": "badge-warning",
                }
                badge = badge_map.get(p["condicion_iva"], "badge-neutral")
                st.markdown(f"""
                <div style='background:white;border:1px solid #e8eaf6;border-radius:8px;padding:12px;margin:6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.05)'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                        <div>
                            <strong style='color:#1a237e'>{p['razon_social']}</strong>
                            <br><small style='color:#666'>CUIT: {p['cuit']} · {p.get('email','-')}</small>
                            <br><small style='color:#888'>Cuenta: {p.get('cuenta_gastos','-')}</small>
                        </div>
                        <span class="{badge}">{p['condicion_iva']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay proveedores registrados aún.")


# ─── CARGA DE GASTOS ──────────────────────────────────────────
def show_gastos():
    st.markdown("### 📄 Carga de Factura de Compra")
    proveedores = load_data("proveedores")
    if not proveedores:
        st.warning("⚠️ No hay proveedores cargados.")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-header"><h3>Datos del Comprobante</h3></div>', unsafe_allow_html=True)
        opciones_prov = {f"{p['razon_social']} — CUIT: {p['cuit']}": p for p in proveedores}
        prov_sel = st.selectbox("Proveedor *", list(opciones_prov.keys()))
        proveedor = opciones_prov[prov_sel]

        cond = proveedor["condicion_iva"]
        st.markdown(f"<span class='badge-info'>{cond}</span>", unsafe_allow_html=True)

        tipo_comp = st.selectbox("Tipo Comprobante", ["Factura A", "Factura B", "Factura C", "Ticket", "Recibo"])
        numero_comp = st.text_input("N° Comprobante *", placeholder="0001-00000001")
        fecha_comp = st.date_input("Fecha Comprobante", value=date.today())
        fecha_vto = st.date_input("Fecha Vencimiento Pago")
        cuenta_gastos = st.selectbox("Cuenta de Gastos", CUENTAS_GASTOS,
                                     index=CUENTAS_GASTOS.index(proveedor.get("cuenta_gastos", CUENTAS_GASTOS[0])) if proveedor.get("cuenta_gastos") in CUENTAS_GASTOS else 0)
        concepto = st.text_area("Concepto")

    with col2:
        st.markdown('<div class="section-header"><h3>Importes e IVA</h3></div>', unsafe_allow_html=True)

        # Monotributistas y Consumidor Final → todo exento
        es_exento_forzado = cond in ["Monotributista", "Consumidor Final"]

        if es_exento_forzado:
            st.info("🔔 Proveedor Monotributista/Consumidor Final: el importe se carga como Exento.")
            neto_exento = st.number_input("Importe Total ($)", min_value=0.0, step=0.01, format="%.2f")
            neto_21 = neto_105 = neto_27 = 0.0
            iva_21 = iva_105 = iva_27 = 0.0
        else:
            neto_21 = st.number_input("Neto gravado 21% ($)", min_value=0.0, step=0.01, format="%.2f")
            neto_105 = st.number_input("Neto gravado 10,5% ($)", min_value=0.0, step=0.01, format="%.2f")
            neto_27 = st.number_input("Neto gravado 27% ($)", min_value=0.0, step=0.01, format="%.2f")
            neto_exento = st.number_input("Importe Exento ($)", min_value=0.0, step=0.01, format="%.2f")
            iva_21 = round(neto_21 * 0.21, 2)
            iva_105 = round(neto_105 * 0.105, 2)
            iva_27 = round(neto_27 * 0.27, 2)

        total_neto = neto_21 + neto_105 + neto_27 + neto_exento
        total_iva = iva_21 + iva_105 + iva_27

        st.markdown("**Retenciones**")
        ret_iva = st.number_input("Retención IVA ($)", min_value=0.0, step=0.01, format="%.2f")
        ret_iibb = st.number_input("Retención IIBB ($)", min_value=0.0, step=0.01, format="%.2f")
        ret_imp_int = st.number_input("Ret. Impuestos Internos ($)", min_value=0.0, step=0.01, format="%.2f")

        total_retenciones = ret_iva + ret_iibb + ret_imp_int
        total_factura = total_neto + total_iva
        total_a_pagar = total_factura - total_retenciones

        st.markdown(f"""
        <div style='background:#f8f9ff;border:1px solid #c5cae9;border-radius:10px;padding:16px;margin-top:10px'>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'><span>Neto Total:</span><strong>${total_neto:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'><span>IVA Total:</span><strong>${total_iva:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'><span>Total Factura:</span><strong>${total_factura:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px;color:#c62828'><span>(-) Retenciones:</span><strong>-${total_retenciones:,.2f}</strong></div>
            <hr style='margin:8px 0;border-color:#e8eaf6'>
            <div style='display:flex;justify-content:space-between'><span style='color:#1a237e;font-weight:700;font-size:1.1rem'>A PAGAR:</span><strong style='color:#1a237e;font-size:1.1rem'>${total_a_pagar:,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💾 Registrar Factura de Compra", use_container_width=True, type="primary"):
            if not numero_comp or total_factura <= 0:
                st.error("Complete los datos obligatorios y el importe.")
            else:
                facturas = load_data("facturas_compra")
                nueva = {
                    "id": get_next_id("facturas_compra"),
                    "proveedor_id": proveedor["id"],
                    "proveedor_razon_social": proveedor["razon_social"],
                    "proveedor_cuit": proveedor["cuit"],
                    "condicion_iva": cond,
                    "tipo_comprobante": tipo_comp,
                    "numero_comprobante": numero_comp,
                    "fecha": str(fecha_comp),
                    "fecha_vencimiento": str(fecha_vto),
                    "cuenta_gastos": cuenta_gastos,
                    "concepto": concepto,
                    "neto_21": neto_21, "iva_21": iva_21,
                    "neto_105": neto_105, "iva_105": iva_105,
                    "neto_27": neto_27, "iva_27": iva_27,
                    "neto_exento": neto_exento,
                    "total_neto": total_neto,
                    "total_iva": total_iva,
                    "total_factura": total_factura,
                    "ret_iva": ret_iva,
                    "ret_iibb": ret_iibb,
                    "ret_imp_int": ret_imp_int,
                    "total_retenciones": total_retenciones,
                    "total_a_pagar": total_a_pagar,
                    "saldo_pendiente": total_a_pagar,
                    "estado": "Pendiente",
                    "fecha_carga": now_str(),
                }
                facturas.append(nueva)
                save_data("facturas_compra", facturas)
                st.success(f"✅ Factura {numero_comp} registrada. A pagar: ${total_a_pagar:,.2f}")
                st.rerun()


# ─── CUENTA CORRIENTE INDIVIDUAL ─────────────────────────────
def show_cc_individual():
    st.markdown("### 📋 Cuenta Corriente por Proveedor")
    proveedores = load_data("proveedores")
    if not proveedores:
        st.info("No hay proveedores registrados.")
        return

    opciones = {f"{p['razon_social']} — CUIT: {p['cuit']}": p for p in proveedores}
    sel = st.selectbox("Seleccionar Proveedor", list(opciones.keys()), key="cc_prov_sel")
    proveedor = opciones[sel]

    facturas = [f for f in load_data("facturas_compra") if f["proveedor_id"] == proveedor["id"]]
    pagos = [p for p in load_data("pagos") if p.get("proveedor_id") == proveedor["id"]]

    movs = []
    for f in facturas:
        movs.append({"Fecha": f["fecha"], "Tipo": f["tipo_comprobante"], "Comprobante": f["numero_comprobante"],
                     "Concepto": f.get("concepto", "-"), "Debe": f["total_a_pagar"], "Haber": 0, "Saldo": 0})
    for p in pagos:
        movs.append({"Fecha": p["fecha"], "Tipo": "Pago", "Comprobante": p.get("referencia", "-"),
                     "Concepto": p.get("forma_pago", "-"), "Debe": 0, "Haber": p["importe"], "Saldo": 0})

    movs.sort(key=lambda x: x["Fecha"])
    saldo = 0
    for m in movs:
        saldo += m["Debe"] - m["Haber"]
        m["Saldo"] = saldo

    total_facturado = sum(f["total_a_pagar"] for f in facturas)
    total_pagado = sum(p["importe"] for p in pagos)
    saldo_final = total_facturado - total_pagado

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Facturado", f"${total_facturado:,.2f}")
    col2.metric("Total Pagado", f"${total_pagado:,.2f}")
    col3.metric("Saldo Pendiente", f"${saldo_final:,.2f}")

    if movs:
        df = pd.DataFrame(movs)
        df["Debe"] = df["Debe"].apply(lambda x: f"${x:,.2f}" if x else "-")
        df["Haber"] = df["Haber"].apply(lambda x: f"${x:,.2f}" if x else "-")
        df["Saldo"] = df["Saldo"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay movimientos para este proveedor.")


# ─── CUENTA CORRIENTE GENERAL ────────────────────────────────
def show_cc_general():
    st.markdown("### 📊 Resumen Cuentas Corrientes — Todos los Proveedores")
    proveedores = load_data("proveedores")
    facturas = load_data("facturas_compra")
    pagos = load_data("pagos")

    resumen = []
    for p in proveedores:
        total_f = sum(f["total_a_pagar"] for f in facturas if f["proveedor_id"] == p["id"])
        total_p = sum(pa["importe"] for pa in pagos if pa.get("proveedor_id") == p["id"])
        saldo = total_f - total_p
        if saldo != 0:
            resumen.append({"Proveedor": p["razon_social"], "CUIT": p["cuit"],
                            "Condición IVA": p["condicion_iva"], "Cuenta Gastos": p.get("cuenta_gastos", "-"),
                            "Total Facturado": total_f, "Total Pagado": total_p, "Saldo": saldo})

    if resumen:
        df = pd.DataFrame(resumen).sort_values("Saldo", ascending=False)
        st.metric("💸 Saldo Total a Pagar", f"${df['Saldo'].sum():,.2f}")
        df_d = df.copy()
        for col in ["Total Facturado", "Total Pagado", "Saldo"]:
            df_d[col] = df_d[col].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_d, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Todas las cuentas corrientes con proveedores están en cero.")
