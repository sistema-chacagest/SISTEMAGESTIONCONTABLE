import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils.database import load_data, CUENTAS_GASTOS, BANCOS

def show():
    st.markdown("## 📊 Reportes y Balance")
    tab = st.tabs(["📈 Ingresos vs Egresos", "💼 Por Cuenta de Gastos", "🏦 Movimientos Bancarios", "📋 Balance General"])

    with tab[0]:
        show_ingresos_egresos()
    with tab[1]:
        show_por_cuenta()
    with tab[2]:
        show_movimientos_banco()
    with tab[3]:
        show_balance()


def _filtro_fechas(key_prefix):
    col1, col2 = st.columns(2)
    with col1:
        desde = st.date_input("Desde", value=date(date.today().year, 1, 1), key=f"{key_prefix}_desde")
    with col2:
        hasta = st.date_input("Hasta", value=date.today(), key=f"{key_prefix}_hasta")
    return str(desde), str(hasta)


# ─── INGRESOS VS EGRESOS ──────────────────────────────────────
def show_ingresos_egresos():
    st.markdown("### 📈 Reporte de Ingresos vs Egresos")
    desde, hasta = _filtro_fechas("ive")

    # Ingresos: facturas de venta emitidas
    facturas_v = [f for f in load_data("facturas_venta") if desde <= f.get("fecha", "") <= hasta]
    total_ventas_neto = sum(f.get("neto", 0) for f in facturas_v)
    total_ventas_iva = sum(f.get("iva", 0) for f in facturas_v)
    total_ventas = sum(f.get("total", 0) for f in facturas_v)

    # Egresos: facturas de compra
    facturas_c = [f for f in load_data("facturas_compra") if desde <= f.get("fecha", "") <= hasta]
    total_compras_neto = sum(f.get("total_neto", 0) for f in facturas_c)
    total_compras_iva = sum(f.get("total_iva", 0) for f in facturas_c)
    total_compras = sum(f.get("total_factura", 0) for f in facturas_c)

    resultado = total_ventas - total_compras

    col1, col2, col3 = st.columns(3)
    col1.metric("💚 Total Ingresos (Ventas)", f"${total_ventas:,.2f}", f"Neto: ${total_ventas_neto:,.2f}")
    col2.metric("🔴 Total Egresos (Compras)", f"${total_compras:,.2f}", f"Neto: ${total_compras_neto:,.2f}")
    col3.metric("💰 Resultado Bruto", f"${resultado:,.2f}", delta_color="normal")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 📥 Detalle Ingresos")
        st.markdown(f"""
        <div style='background:#e8f5e9;border-radius:10px;padding:16px'>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'><span>Neto Ventas:</span><strong>${total_ventas_neto:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'><span>IVA Ventas:</span><strong>${total_ventas_iva:,.2f}</strong></div>
            <hr style='border-color:#a5d6a7'>
            <div style='display:flex;justify-content:space-between'><span style='font-weight:700'>TOTAL VENTAS:</span><strong style='color:#2e7d32'>${total_ventas:,.2f}</strong></div>
            <br><small style='color:#555'>{len(facturas_v)} comprobantes en el período</small>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("#### 📤 Detalle Egresos")
        st.markdown(f"""
        <div style='background:#ffebee;border-radius:10px;padding:16px'>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'><span>Neto Compras:</span><strong>${total_compras_neto:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'><span>IVA Compras:</span><strong>${total_compras_iva:,.2f}</strong></div>
            <hr style='border-color:#ef9a9a'>
            <div style='display:flex;justify-content:space-between'><span style='font-weight:700'>TOTAL COMPRAS:</span><strong style='color:#c62828'>${total_compras:,.2f}</strong></div>
            <br><small style='color:#555'>{len(facturas_c)} comprobantes en el período</small>
        </div>
        """, unsafe_allow_html=True)

    # Posición IVA
    st.markdown("#### 🧾 Posición IVA")
    dif_iva = total_ventas_iva - total_compras_iva
    iva_color = "#c62828" if dif_iva > 0 else "#2e7d32"
    iva_label = "IVA a pagar (Débito > Crédito)" if dif_iva > 0 else "IVA a favor (Crédito > Débito)"
    st.markdown(f"""
    <div style='background:#f3e5f5;border-radius:10px;padding:16px;display:flex;justify-content:space-between;align-items:center'>
        <div>
            <div>IVA Débito (ventas): <strong>${total_ventas_iva:,.2f}</strong></div>
            <div>IVA Crédito (compras): <strong>${total_compras_iva:,.2f}</strong></div>
            <div style='margin-top:8px;font-weight:700;color:{iva_color}'>{iva_label}: <strong style='font-size:1.1rem'>${abs(dif_iva):,.2f}</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── POR CUENTA DE GASTOS ─────────────────────────────────────
def show_por_cuenta():
    st.markdown("### 💼 Egresos por Cuenta de Gastos")
    desde, hasta = _filtro_fechas("pcg")

    facturas_c = [f for f in load_data("facturas_compra") if desde <= f.get("fecha", "") <= hasta]

    if not facturas_c:
        st.info("No hay compras en el período seleccionado.")
        return

    por_cuenta = {}
    for f in facturas_c:
        cuenta = f.get("cuenta_gastos", "Sin clasificar")
        por_cuenta[cuenta] = por_cuenta.get(cuenta, 0) + f.get("total_factura", 0)

    total = sum(por_cuenta.values())
    st.metric("Total Egresos", f"${total:,.2f}")

    rows = sorted(por_cuenta.items(), key=lambda x: x[1], reverse=True)
    for cuenta, monto in rows:
        pct = (monto / total * 100) if total else 0
        st.markdown(f"""
        <div style='background:white;border:1px solid #e8eaf6;border-radius:8px;padding:12px;margin:6px 0'>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                <strong>{cuenta}</strong>
                <strong>${monto:,.2f}</strong>
            </div>
            <div style='background:#e8eaf6;border-radius:4px;height:6px'>
                <div style='background:#3949ab;width:{pct:.1f}%;height:6px;border-radius:4px'></div>
            </div>
            <small style='color:#666'>{pct:.1f}% del total</small>
        </div>
        """, unsafe_allow_html=True)


# ─── MOVIMIENTOS BANCARIOS ────────────────────────────────────
def show_movimientos_banco():
    st.markdown("### 🏦 Resumen por Banco")
    desde, hasta = _filtro_fechas("mb_rep")

    movs = [m for m in load_data("movimientos_bancarios") if desde <= m.get("fecha", "") <= hasta]

    for banco in BANCOS:
        movs_banco = [m for m in movs if m.get("banco") == banco]
        if not movs_banco:
            continue

        ingresos = sum(m["importe"] for m in movs_banco if m.get("tipo") == "Ingreso")
        egresos = sum(m["importe"] for m in movs_banco if m.get("tipo") == "Egreso")
        saldo = ingresos - egresos

        with st.expander(f"🏦 {banco} — Saldo período: ${saldo:,.2f} ({len(movs_banco)} movimientos)"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Ingresos", f"${ingresos:,.2f}")
            col2.metric("Egresos", f"${egresos:,.2f}")
            col3.metric("Saldo", f"${saldo:,.2f}")

            df = pd.DataFrame([{
                "Fecha": m["fecha"], "Tipo": m["tipo"], "Importe": f"${m['importe']:,.2f}",
                "Descripción": m.get("descripcion", ""), "Categoría": m.get("categoria", ""),
            } for m in sorted(movs_banco, key=lambda x: x["fecha"], reverse=True)])
            st.dataframe(df, use_container_width=True, hide_index=True)


# ─── BALANCE GENERAL ─────────────────────────────────────────
def show_balance():
    st.markdown("### 📋 Balance General")
    desde, hasta = _filtro_fechas("bal")

    facturas_v = [f for f in load_data("facturas_venta") if desde <= f.get("fecha", "") <= hasta]
    facturas_c = [f for f in load_data("facturas_compra") if desde <= f.get("fecha", "") <= hasta]
    cobranzas = [c for c in load_data("cobranzas") if desde <= c.get("fecha", "") <= hasta]
    pagos = [p for p in load_data("pagos") if desde <= p.get("fecha", "") <= hasta]

    ventas = sum(f.get("total", 0) for f in facturas_v)
    compras = sum(f.get("total_factura", 0) for f in facturas_c)
    cobrado = sum(c.get("importe", 0) for c in cobranzas)
    pagado = sum(p.get("importe", 0) for p in pagos)

    # Cuentas por cobrar y pagar total (no solo período)
    todas_fv = load_data("facturas_venta")
    todas_fc = load_data("facturas_compra")
    por_cobrar = sum(f.get("saldo_pendiente", 0) for f in todas_fv if f.get("saldo_pendiente", 0) > 0)
    por_pagar = sum(f.get("saldo_pendiente", 0) for f in todas_fc if f.get("saldo_pendiente", 0) > 0)

    # Cheques cartera
    cheques_cartera = sum(c.get("importe", 0) for c in load_data("cheques_cartera") if c.get("estado") == "En Cartera")

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#1a237e,#283593);color:white;border-radius:14px;padding:24px;margin-bottom:20px'>
        <h2 style='margin:0 0 5px 0;color:white'>Balance General</h2>
        <p style='margin:0;opacity:0.8'>Período: {desde} al {hasta}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📥 INGRESOS DEL PERÍODO")
        st.markdown(f"""
        <div style='background:white;border:1px solid #e8eaf6;border-radius:10px;padding:18px'>
            <div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f5f5f5'><span>Ventas Facturadas</span><strong>${ventas:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f5f5f5'><span>Cobrado en período</span><strong>${cobrado:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f5f5f5'><span>Cuentas por Cobrar (total)</span><strong>${por_cobrar:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;padding:8px 0'><span>Cheques en Cartera</span><strong>${cheques_cartera:,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📤 EGRESOS DEL PERÍODO")
        st.markdown(f"""
        <div style='background:white;border:1px solid #e8eaf6;border-radius:10px;padding:18px'>
            <div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f5f5f5'><span>Compras Facturadas</span><strong>${compras:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f5f5f5'><span>Pagado en período</span><strong>${pagado:,.2f}</strong></div>
            <div style='display:flex;justify-content:space-between;padding:8px 0'><span>Cuentas por Pagar (total)</span><strong>${por_pagar:,.2f}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    resultado = ventas - compras
    res_color = "#2e7d32" if resultado >= 0 else "#c62828"
    res_label = "SUPERÁVIT" if resultado >= 0 else "DÉFICIT"
    st.markdown(f"""
    <div style='background:{res_color};color:white;border-radius:12px;padding:20px;text-align:center'>
        <div style='font-size:0.9rem;opacity:0.9'>{res_label} DEL PERÍODO</div>
        <div style='font-size:2.5rem;font-weight:700'>${abs(resultado):,.2f}</div>
        <div style='opacity:0.8;font-size:0.85rem'>Ventas ${ventas:,.2f} — Compras ${compras:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
