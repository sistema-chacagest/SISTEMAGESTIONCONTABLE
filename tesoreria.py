import streamlit as st
import pandas as pd
from datetime import date
from utils.database import (
    load_data, save_data, get_next_id, now_str, date_str, BANCOS
)

def show():
    st.markdown("## 🏦 Módulo de Tesorería")
    tab = st.tabs(["💸 Órdenes de Pago", "📥 Cobranzas", "📋 Cheques en Cartera"])

    with tab[0]:
        show_pagos()
    with tab[1]:
        show_cobranzas()
    with tab[2]:
        show_cheques_cartera()


# ─── ÓRDENES DE PAGO ─────────────────────────────────────────
def show_pagos():
    st.markdown("### 💸 Orden de Pago a Proveedor")
    proveedores = load_data("proveedores")
    if not proveedores:
        st.warning("No hay proveedores registrados.")
        return

    opciones_prov = {f"{p['razon_social']} — CUIT: {p['cuit']}": p for p in proveedores}
    prov_sel = st.selectbox("Seleccionar Proveedor", list(opciones_prov.keys()), key="pago_prov")
    proveedor = opciones_prov[prov_sel]

    # Facturas pendientes del proveedor
    facturas_pendientes = [
        f for f in load_data("facturas_compra")
        if f["proveedor_id"] == proveedor["id"] and f.get("saldo_pendiente", 0) > 0
    ]

    if not facturas_pendientes:
        st.info("✅ Este proveedor no tiene facturas pendientes de pago.")
        return

    st.markdown("**Facturas Pendientes**")
    opciones_facturas = {}
    for f in facturas_pendientes:
        label = f"{f['tipo_comprobante']} {f['numero_comprobante']} — ${f['saldo_pendiente']:,.2f} — {f['fecha']}"
        opciones_facturas[label] = f

    facturas_a_pagar = st.multiselect("Seleccionar facturas a cancelar", list(opciones_facturas.keys()))

    total_seleccionado = sum(opciones_facturas[k]["saldo_pendiente"] for k in facturas_a_pagar)
    if facturas_a_pagar:
        st.markdown(f"**Total a pagar:** <span style='color:#1a237e;font-size:1.1rem;font-weight:700'>${total_seleccionado:,.2f}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Forma de Pago**")
    forma_pago = st.selectbox("Seleccionar forma de pago", ["Transferencia Bancaria", "Efectivo", "Cheque Propio", "Cheque de Tercero"])

    fecha_pago = st.date_input("Fecha de Pago", value=date.today())
    referencia = st.text_input("N° Referencia / Comprobante")
    observaciones = st.text_area("Observaciones", height=80)

    banco_sel = None
    if forma_pago == "Transferencia Bancaria":
        banco_sel = st.selectbox("Banco Emisor", BANCOS)

    cheque_tercero_sel = None
    if forma_pago == "Cheque de Tercero":
        cheques_cartera = [c for c in load_data("cheques_cartera") if c.get("estado") == "En Cartera"]
        if not cheques_cartera:
            st.warning("No hay cheques de terceros en cartera.")
        else:
            opciones_cheques = {
                f"Cheque #{c['numero']} — {c['banco']} — ${c['importe']:,.2f} — Vto: {c['fecha_vencimiento']}": c
                for c in cheques_cartera
            }
            ch_sel = st.selectbox("Seleccionar cheque", list(opciones_cheques.keys()))
            cheque_tercero_sel = opciones_cheques[ch_sel]

    if forma_pago == "Cheque Propio":
        st.markdown("**Datos del Cheque a Emitir**")
        with st.form("form_cheque_emitir"):
            col1, col2 = st.columns(2)
            with col1:
                ch_banco = st.selectbox("Banco", BANCOS)
                ch_numero = st.text_input("N° Cheque")
                ch_importe = st.number_input("Importe ($)", min_value=0.0, step=0.01, format="%.2f", value=float(total_seleccionado))
            with col2:
                ch_fecha_emision = st.date_input("Fecha Emisión", value=date.today())
                ch_fecha_vto = st.date_input("Fecha Vencimiento")
                ch_beneficiario = st.text_input("Beneficiario", value=proveedor["razon_social"])
            emitir = st.form_submit_button("📝 Emitir Cheque y Registrar Pago", use_container_width=True)
            if emitir:
                _registrar_cheque_emitido(ch_banco, ch_numero, ch_importe, str(ch_fecha_emision), str(ch_fecha_vto), ch_beneficiario)
                _registrar_pago(proveedor, facturas_a_pagar, opciones_facturas, total_seleccionado,
                                forma_pago, str(fecha_pago), referencia, banco_sel, observaciones, f"Cheque {ch_numero}")
        return

    if st.button("✅ Registrar Pago", type="primary", use_container_width=True, disabled=not facturas_a_pagar):
        if not facturas_a_pagar:
            st.error("Seleccione al menos una factura.")
        else:
            cheque_info = cheque_tercero_sel.get("numero", "") if cheque_tercero_sel else ""
            _registrar_pago(proveedor, facturas_a_pagar, opciones_facturas, total_seleccionado,
                            forma_pago, str(fecha_pago), referencia, banco_sel, observaciones, cheque_info)
            # Marcar cheque de tercero como usado
            if cheque_tercero_sel:
                cheques = load_data("cheques_cartera")
                for c in cheques:
                    if c["id"] == cheque_tercero_sel["id"]:
                        c["estado"] = "Entregado"
                        c["entregado_a"] = proveedor["razon_social"]
                        c["fecha_entrega"] = str(fecha_pago)
                        break
                save_data("cheques_cartera", cheques)


def _registrar_cheque_emitido(banco, numero, importe, fecha_emision, fecha_vto, beneficiario):
    cheques = load_data("cheques_emitidos")
    cheques.append({
        "id": get_next_id("cheques_emitidos"),
        "banco": banco,
        "numero": numero,
        "importe": importe,
        "fecha_emision": fecha_emision,
        "fecha_vencimiento": fecha_vto,
        "beneficiario": beneficiario,
        "estado": "Pendiente",
        "fecha_carga": now_str(),
    })
    save_data("cheques_emitidos", cheques)
    # Movimiento bancario
    _mov_banco(banco, fecha_emision, "Egreso", importe, f"Cheque emitido #{numero} a {beneficiario}", "Cheque Emitido")
    st.success(f"✅ Cheque #{numero} emitido correctamente.")


def _registrar_pago(proveedor, facturas_sel, opciones, total, forma, fecha, referencia, banco, obs, cheque_ref=""):
    pagos = load_data("pagos")
    nuevo_pago = {
        "id": get_next_id("pagos"),
        "proveedor_id": proveedor["id"],
        "proveedor_razon_social": proveedor["razon_social"],
        "facturas": facturas_sel,
        "importe": total,
        "forma_pago": forma,
        "banco": banco,
        "cheque_ref": cheque_ref,
        "fecha": fecha,
        "referencia": referencia,
        "observaciones": obs,
        "fecha_carga": now_str(),
    }
    pagos.append(nuevo_pago)
    save_data("pagos", pagos)

    # Actualizar saldos de facturas
    facturas = load_data("facturas_compra")
    for k in facturas_sel:
        fac = opciones[k]
        for f in facturas:
            if f["id"] == fac["id"]:
                f["saldo_pendiente"] = 0
                f["estado"] = "Pagada"
                break
    save_data("facturas_compra", facturas)

    # Movimiento bancario
    if banco:
        _mov_banco(banco, fecha, "Egreso", total, f"Pago a {proveedor['razon_social']} · {referencia}", forma)

    st.success(f"✅ Pago registrado por ${total:,.2f} a {proveedor['razon_social']}")
    st.rerun()


def _mov_banco(banco, fecha, tipo, importe, descripcion, categoria):
    movs = load_data("movimientos_bancarios")
    movs.append({
        "id": get_next_id("movimientos_bancarios"),
        "banco": banco,
        "fecha": fecha,
        "tipo": tipo,
        "importe": importe,
        "descripcion": descripcion,
        "categoria": categoria,
        "fecha_carga": now_str(),
    })
    save_data("movimientos_bancarios", movs)


# ─── COBRANZAS ────────────────────────────────────────────────
def show_cobranzas():
    st.markdown("### 📥 Cobranza de Facturas")
    clientes = load_data("clientes")
    if not clientes:
        st.warning("No hay clientes registrados.")
        return

    opciones_cli = {f"{c['razon_social']} — CUIT: {c['cuit']}": c for c in clientes}
    cli_sel = st.selectbox("Seleccionar Cliente", list(opciones_cli.keys()), key="cobr_cli")
    cliente = opciones_cli[cli_sel]

    facturas_pendientes = [
        f for f in load_data("facturas_venta")
        if f["cliente_id"] == cliente["id"] and f.get("saldo_pendiente", 0) > 0
    ]

    if not facturas_pendientes:
        st.info("✅ Este cliente no tiene facturas pendientes de cobro.")
        return

    opciones_facturas = {
        f"{f['tipo_comprobante']} {f['numero_comprobante']} — ${f['saldo_pendiente']:,.2f} — {f['fecha']}": f
        for f in facturas_pendientes
    }
    facturas_a_cobrar = st.multiselect("Seleccionar facturas a cobrar", list(opciones_facturas.keys()))
    total_sel = sum(opciones_facturas[k]["saldo_pendiente"] for k in facturas_a_cobrar)

    if facturas_a_cobrar:
        st.markdown(f"**Total a cobrar:** <span style='color:#2e7d32;font-size:1.1rem;font-weight:700'>${total_sel:,.2f}</span>", unsafe_allow_html=True)

    forma_cobro = st.selectbox("Forma de Cobro", ["Transferencia Bancaria", "Efectivo", "Cheque de Tercero"])
    fecha_cobro = st.date_input("Fecha de Cobro", value=date.today())
    referencia = st.text_input("N° Referencia")
    banco_destino = None

    if forma_cobro == "Transferencia Bancaria":
        banco_destino = st.selectbox("Banco Destino", BANCOS)

    if forma_cobro == "Cheque de Tercero":
        st.markdown("**Datos del Cheque Recibido**")
        col1, col2 = st.columns(2)
        with col1:
            ch_banco = st.selectbox("Banco Librador", BANCOS, key="ch_banco_cobr")
            ch_numero = st.text_input("N° Cheque", key="ch_num_cobr")
            ch_importe = st.number_input("Importe del Cheque ($)", min_value=0.0, step=0.01, format="%.2f", value=float(total_sel), key="ch_imp_cobr")
        with col2:
            ch_librador = st.text_input("Librador (quien lo emite)", key="ch_lib_cobr")
            ch_fecha_emision = st.date_input("Fecha Emisión Cheque", key="ch_fem_cobr")
            ch_fecha_vto = st.date_input("Fecha Vencimiento Cheque", key="ch_vto_cobr")

    if st.button("✅ Registrar Cobranza", type="primary", use_container_width=True, disabled=not facturas_a_cobrar):
        # Si es cheque, guardar en cartera
        if forma_cobro == "Cheque de Tercero":
            cheques = load_data("cheques_cartera")
            cheques.append({
                "id": get_next_id("cheques_cartera"),
                "banco": ch_banco,
                "numero": ch_numero,
                "importe": ch_importe,
                "librador": ch_librador,
                "fecha_emision": str(ch_fecha_emision),
                "fecha_vencimiento": str(ch_fecha_vto),
                "recibido_de": cliente["razon_social"],
                "estado": "En Cartera",
                "fecha_ingreso": str(fecha_cobro),
            })
            save_data("cheques_cartera", cheques)

        # Registrar cobranza
        cobranzas = load_data("cobranzas")
        cobranzas.append({
            "id": get_next_id("cobranzas"),
            "cliente_id": cliente["id"],
            "cliente_razon_social": cliente["razon_social"],
            "facturas": facturas_a_cobrar,
            "importe": total_sel,
            "forma_pago": forma_cobro,
            "banco": banco_destino,
            "fecha": str(fecha_cobro),
            "referencia": referencia,
            "fecha_carga": now_str(),
        })
        save_data("cobranzas", cobranzas)

        # Actualizar facturas
        facturas = load_data("facturas_venta")
        for k in facturas_a_cobrar:
            fac = opciones_facturas[k]
            for f in facturas:
                if f["id"] == fac["id"]:
                    f["saldo_pendiente"] = 0
                    f["estado"] = "Cobrada"
                    break
        save_data("facturas_venta", facturas)

        # Movimiento bancario
        if banco_destino:
            _mov_banco(banco_destino, str(fecha_cobro), "Ingreso", total_sel,
                       f"Cobranza de {cliente['razon_social']} · {referencia}", forma_cobro)

        st.success(f"✅ Cobranza registrada por ${total_sel:,.2f} de {cliente['razon_social']}")
        st.rerun()


# ─── CHEQUES EN CARTERA ───────────────────────────────────────
def show_cheques_cartera():
    st.markdown("### 💳 Cheques de Terceros en Cartera")
    cheques = [c for c in load_data("cheques_cartera") if c.get("estado") == "En Cartera"]

    if not cheques:
        st.info("No hay cheques en cartera actualmente.")
        return

    total = sum(c["importe"] for c in cheques)
    st.metric("💰 Total en Cartera", f"${total:,.2f}", f"{len(cheques)} cheques")
    st.markdown("")

    hoy = date.today()
    for c in sorted(cheques, key=lambda x: x.get("fecha_vencimiento", "")):
        try:
            venc = date.fromisoformat(c["fecha_vencimiento"])
            dias = (venc - hoy).days
            if dias < 0:
                estado_vto = f"<span class='badge-danger'>Vencido hace {abs(dias)} días</span>"
            elif dias <= 7:
                estado_vto = f"<span class='badge-warning'>Vence en {dias} días</span>"
            else:
                estado_vto = f"<span class='badge-success'>Vence en {dias} días</span>"
        except:
            estado_vto = ""

        st.markdown(f"""
        <div style='background:white;border:1px solid #e8eaf6;border-radius:10px;padding:14px;margin:8px 0;box-shadow:0 2px 6px rgba(0,0,0,0.06)'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                <div>
                    <strong style='color:#1a237e;font-size:1rem'>Cheque #{c.get('numero','-')} — {c.get('banco','-')}</strong>
                    <br><span style='color:#2e7d32;font-size:1.1rem;font-weight:700'>${c.get('importe',0):,.2f}</span>
                    <br><small style='color:#555'>Librador: {c.get('librador','-')} · Recibido de: {c.get('recibido_de','-')}</small>
                    <br><small style='color:#666'>Emisión: {c.get('fecha_emision','-')} · Vencimiento: {c.get('fecha_vencimiento','-')}</small>
                    <br><small style='color:#888'>Ingresado: {c.get('fecha_ingreso','-')}</small>
                </div>
                <div style='text-align:right'>
                    {estado_vto}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
