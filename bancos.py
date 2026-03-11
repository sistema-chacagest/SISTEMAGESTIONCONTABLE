import streamlit as st
import pandas as pd
from datetime import date
from utils.database import load_data, save_data, get_next_id, now_str, BANCOS

def show():
    st.markdown("## 🏧 Módulo de Bancos")
    tab = st.tabs(["🏦 Movimientos Bancarios", "💳 Cheques en Cartera", "📋 Cheques Diferidos (Emitidos)"])

    with tab[0]:
        show_movimientos()
    with tab[1]:
        show_cheques_cartera()
    with tab[2]:
        show_cheques_diferidos()


# ─── MOVIMIENTOS BANCARIOS ────────────────────────────────────
def show_movimientos():
    st.markdown("### 🏦 Movimientos Bancarios")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        banco_filtro = st.selectbox("Banco", ["Todos"] + BANCOS, key="mb_banco")
    with col2:
        tipo_filtro = st.selectbox("Tipo", ["Todos", "Ingreso", "Egreso"], key="mb_tipo")
    with col3:
        buscar = st.text_input("🔍 Buscar descripción", key="mb_buscar")

    movs = load_data("movimientos_bancarios")
    if banco_filtro != "Todos":
        movs = [m for m in movs if m.get("banco") == banco_filtro]
    if tipo_filtro != "Todos":
        movs = [m for m in movs if m.get("tipo") == tipo_filtro]
    if buscar:
        movs = [m for m in movs if buscar.lower() in m.get("descripcion", "").lower()]

    # Saldo por banco
    st.markdown("**Saldos por Banco**")
    todos_movs = load_data("movimientos_bancarios")
    saldos_cols = st.columns(len(BANCOS))
    for i, banco in enumerate(BANCOS):
        ing = sum(m["importe"] for m in todos_movs if m.get("banco") == banco and m.get("tipo") == "Ingreso")
        egr = sum(m["importe"] for m in todos_movs if m.get("banco") == banco and m.get("tipo") == "Egreso")
        saldo = ing - egr
        saldos_cols[i].metric(banco, f"${saldo:,.0f}")

    st.markdown("---")

    # Ingreso manual
    with st.expander("➕ Registrar Movimiento Manual"):
        with st.form("form_mov_banco", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                m_banco = st.selectbox("Banco", BANCOS)
                m_tipo = st.selectbox("Tipo", ["Ingreso", "Egreso"])
                m_fecha = st.date_input("Fecha", value=date.today())
            with c2:
                m_importe = st.number_input("Importe ($)", min_value=0.0, step=0.01, format="%.2f")
                m_cat = st.text_input("Categoría")
                m_desc = st.text_input("Descripción")
            if st.form_submit_button("💾 Guardar", use_container_width=True):
                movs_all = load_data("movimientos_bancarios")
                movs_all.append({
                    "id": get_next_id("movimientos_bancarios"),
                    "banco": m_banco, "fecha": str(m_fecha), "tipo": m_tipo,
                    "importe": m_importe, "descripcion": m_desc, "categoria": m_cat,
                    "fecha_carga": now_str(),
                })
                save_data("movimientos_bancarios", movs_all)
                st.success("✅ Movimiento registrado.")
                st.rerun()

    movs_sorted = sorted(movs, key=lambda x: x.get("fecha", ""), reverse=True)
    if movs_sorted:
        rows = []
        for m in movs_sorted:
            rows.append({
                "Fecha": m.get("fecha", ""),
                "Banco": m.get("banco", ""),
                "Tipo": m.get("tipo", ""),
                "Importe": m.get("importe", 0),
                "Descripción": m.get("descripcion", ""),
                "Categoría": m.get("categoria", ""),
            })
        df = pd.DataFrame(rows)

        def color_tipo(val):
            if val == "Ingreso":
                return "color: #2e7d32; font-weight: bold"
            elif val == "Egreso":
                return "color: #c62828; font-weight: bold"
            return ""

        df_styled = df.copy()
        df_styled["Importe"] = df_styled.apply(
            lambda r: f"+${r['Importe']:,.2f}" if r["Tipo"] == "Ingreso" else f"-${r['Importe']:,.2f}", axis=1
        )
        st.dataframe(df_styled, use_container_width=True, hide_index=True)
    else:
        st.info("No hay movimientos con los filtros seleccionados.")


# ─── CHEQUES EN CARTERA ───────────────────────────────────────
def show_cheques_cartera():
    st.markdown("### 💳 Cheques de Terceros en Cartera")
    cheques = load_data("cheques_cartera")

    filtro_estado = st.selectbox("Estado", ["En Cartera", "Entregado", "Todos"], key="ch_est_filt")
    if filtro_estado != "Todos":
        cheques = [c for c in cheques if c.get("estado") == filtro_estado]

    if not cheques:
        st.info("No hay cheques con ese estado.")
        return

    total = sum(c.get("importe", 0) for c in cheques if c.get("estado") == "En Cartera")
    st.metric("💰 Total en Cartera", f"${total:,.2f}", f"{sum(1 for c in cheques if c.get('estado')=='En Cartera')} cheques")

    hoy = date.today()
    rows = []
    for c in sorted(cheques, key=lambda x: x.get("fecha_vencimiento", "")):
        try:
            venc = date.fromisoformat(c["fecha_vencimiento"])
            dias = (venc - hoy).days
            dias_str = f"{dias} días" if dias >= 0 else f"Vencido {abs(dias)}d"
        except:
            dias_str = "-"

        rows.append({
            "N° Cheque": c.get("numero", "-"),
            "Banco": c.get("banco", "-"),
            "Importe": f"${c.get('importe',0):,.2f}",
            "Librador": c.get("librador", "-"),
            "Recibido de": c.get("recibido_de", "-"),
            "F. Emisión": c.get("fecha_emision", "-"),
            "F. Vencimiento": c.get("fecha_vencimiento", "-"),
            "Días p/vencer": dias_str,
            "Estado": c.get("estado", "-"),
            "Entregado a": c.get("entregado_a", "-"),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ─── CHEQUES DIFERIDOS EMITIDOS ───────────────────────────────
def show_cheques_diferidos():
    st.markdown("### 📋 Cheques Diferidos Emitidos")

    cheques = load_data("cheques_emitidos")
    filtro = st.selectbox("Mostrar", ["Pendientes", "Conciliados", "Todos"], key="ch_dif_filt")

    if filtro == "Pendientes":
        cheques_f = [c for c in cheques if c.get("estado") == "Pendiente"]
    elif filtro == "Conciliados":
        cheques_f = [c for c in cheques if c.get("estado") == "Conciliado"]
    else:
        cheques_f = cheques

    if not cheques_f:
        st.info("No hay cheques con ese estado.")
        return

    total_pendiente = sum(c.get("importe", 0) for c in cheques if c.get("estado") == "Pendiente")
    st.metric("📤 Total Cheques Pendientes de Débito", f"${total_pendiente:,.2f}")

    hoy = date.today()
    for c in sorted(cheques_f, key=lambda x: x.get("fecha_vencimiento", "")):
        try:
            venc = date.fromisoformat(c["fecha_vencimiento"])
            dias = (venc - hoy).days
            if c["estado"] == "Conciliado":
                badge = "<span class='badge-success'>Conciliado ✓</span>"
            elif dias < 0:
                badge = f"<span class='badge-danger'>Vencido hace {abs(dias)}d</span>"
            elif dias <= 5:
                badge = f"<span class='badge-warning'>Vence en {dias}d</span>"
            else:
                badge = f"<span class='badge-info'>Vence en {dias}d</span>"
        except:
            badge = "<span class='badge-neutral'>-</span>"

        col_info, col_btn = st.columns([4, 1])
        with col_info:
            st.markdown(f"""
            <div style='background:white;border:1px solid #e8eaf6;border-radius:10px;padding:14px;margin:6px 0;box-shadow:0 2px 6px rgba(0,0,0,0.06)'>
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div>
                        <strong style='color:#1a237e'>Cheque #{c.get('numero','-')} — {c.get('banco','-')}</strong>
                        &nbsp; {badge}
                        <br><span style='color:#c62828;font-size:1.05rem;font-weight:700'>${c.get('importe',0):,.2f}</span>
                        <br><small style='color:#555'>Beneficiario: <strong>{c.get('beneficiario','-')}</strong></small>
                        <br><small style='color:#666'>Emisión: {c.get('fecha_emision','-')} · Vencimiento: {c.get('fecha_vencimiento','-')}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if c.get("estado") == "Pendiente":
            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ Conciliar", key=f"conciliar_{c['id']}", type="secondary"):
                    cheques_all = load_data("cheques_emitidos")
                    for ch in cheques_all:
                        if ch["id"] == c["id"]:
                            ch["estado"] = "Conciliado"
                            ch["fecha_conciliacion"] = str(hoy)
                            break
                    save_data("cheques_emitidos", cheques_all)
                    # Movimiento bancario de débito
                    movs = load_data("movimientos_bancarios")
                    movs.append({
                        "id": get_next_id("movimientos_bancarios"),
                        "banco": c["banco"],
                        "fecha": str(hoy),
                        "tipo": "Egreso",
                        "importe": c["importe"],
                        "descripcion": f"Débito cheque #{c['numero']} a {c['beneficiario']}",
                        "categoria": "Cheque Debitado",
                        "fecha_carga": now_str(),
                    })
                    save_data("movimientos_bancarios", movs)
                    st.success(f"Cheque #{c['numero']} conciliado y debitado del banco.")
                    st.rerun()
