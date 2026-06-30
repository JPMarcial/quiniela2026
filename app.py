import streamlit as st

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Quiniela Mundial 2026", 
    page_icon="⚽", 
    layout="centered"
)

# Centrar vertical y horizontalmente el contenido con un estilo limpio
st.markdown(
    """
    <style>
    .modo-espera {
        text-align: center;
        margin-top: 15%;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .frase {
        font-size: 32px;
        font-weight: bold;
        color: #475569;
        margin-bottom: 30px;
    }
    .emoji-animado {
        font-size: 80px;
        animation: rodar 4s linear infinite;
        display: inline-block;
    }
    @keyframes rodar {
        0% { transform: translateX(-150px) rotate(0deg); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { transform: translateX(150px) rotate(360deg); opacity: 0; }
    }
    </style>
    
    <div class="modo-espera">
        <div class="frase">Fuera de servicio</div>
        <div class="emoji-animado">🌾</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# LÓGICA DE RESPALDO (RESPALDO INTERNO)
# ==========================================
# Toda la infraestructura que calcula el ranking, lee desde Google Drive 
# (ID: 1svfBlcw4oOEltibwpv1c8I4h6sHmeq7z) y procesa las hojas de RESULTADOS 
# y CALENDARIO se mantiene almacenada internamente en el historial del repositorio 
# lista para ser reactivada en cuanto comience la Fase 02.
