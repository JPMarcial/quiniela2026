import streamlit as st

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y AVISO DE MANTENIMIENTO CON HOJITA GIRATORIA
# ==============================================================================
st.set_page_config(page_title="Módulo en Mantenimiento", page_icon="📄", layout="wide")

st.markdown("""
    <style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinning-sheet {
        font-size: 80px;
        margin-bottom: 25px;
        display: inline-block;
        animation: spin 4s linear infinite;
    }
    </style>

    <div style="text-align: center; padding: 100px 20px; font-family: 'Source Sans Pro', sans-serif;">
        <div class="spinning-sheet">📄</div>
        <h1 style="color: #1E3A8A; font-size: 36px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
            MÓDULO TEMPORALMENTE FUERA DE SERVICIO
        </h1>
        <p style="color: #64748B; font-size: 16px; max-width: 620px; margin: 15px auto 0 auto; line-height: 1.6;">
            Estamos actualizando los datos de la hojita de resultados de los 16vos de final en Google Sheets. 
            Vuelve a cargar esta página en unos minutos para ver los aciertos actualizados.
        </p>
    </div>
""", unsafe_allow_html=True)
