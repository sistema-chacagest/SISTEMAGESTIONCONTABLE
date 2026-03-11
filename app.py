import streamlit as st

st.set_page_config(
    page_title="Sistema de Gestión Empresarial",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    /* Main theme */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(26,35,126,0.3);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .main-header p {
        color: rgba(255,255,255,0.8);
        margin: 5px 0 0 0;
        font-size: 0.9rem;
    }
    
    /* Cards */
    .metric-card {
        background: white;
        border: 1px solid #e8eaf6;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-card .value { font-size: 1.5rem; font-weight: 700; color: #1a237e; }
    .metric-card .label { font-size: 0.8rem; color: #666; margin-top: 4px; }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #e8eaf6, #f5f5f5);
        border-left: 4px solid #3949ab;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        margin: 15px 0 12px 0;
    }
    .section-header h3 { margin: 0; color: #1a237e; font-size: 1rem; }
    
    /* Badges */
    .badge-success { background: #e8f5e9; color: #2e7d32; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-warning { background: #fff8e1; color: #f57f17; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-danger  { background: #ffebee; color: #c62828; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-info    { background: #e3f2fd; color: #1565c0; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-neutral { background: #f5f5f5; color: #424242; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a237e 0%, #283593 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox label { color: rgba(255,255,255,0.85) !important; }
    
    /* Tables */
    .dataframe { font-size: 0.85rem !important; }
    
    /* Forms */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        border-radius: 6px !important;
        border-color: #c5cae9 !important;
    }
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(57,73,171,0.3) !important; }
    
    /* Alert boxes */
    .info-box {
        background: #e3f2fd;
        border: 1px solid #90caf9;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .success-box {
        background: #e8f5e9;
        border: 1px solid #a5d6a7;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .warning-box {
        background: #fff8e1;
        border: 1px solid #ffe082;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    
    div[data-testid="stHorizontalBlock"] { gap: 12px; }
    
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🏢 Sistema de Gestión Empresarial</h1>
    <p>Ventas · Compras · Tesorería · Bancos · Reportes</p>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("### 📋 MENÚ PRINCIPAL")
    st.markdown("---")
    
    modulo = st.selectbox(
        "Seleccionar módulo:",
        [
            "🏠 Inicio",
            "💰 Ventas",
            "🛒 Compras",
            "🏦 Tesorería",
            "🏧 Bancos",
            "📊 Reportes",
        ],
        key="modulo_principal"
    )
    
    st.markdown("---")
    st.markdown("<small style='opacity:0.6'>Sistema v1.0 · 2025</small>", unsafe_allow_html=True)

# Route to modules
if modulo == "🏠 Inicio":
    from pages import inicio
    inicio.show()
elif modulo == "💰 Ventas":
    from pages import ventas
    ventas.show()
elif modulo == "🛒 Compras":
    from pages import compras
    compras.show()
elif modulo == "🏦 Tesorería":
    from pages import tesoreria
    tesoreria.show()
elif modulo == "🏧 Bancos":
    from pages import bancos
    bancos.show()
elif modulo == "📊 Reportes":
    from pages import reportes
    reportes.show()
