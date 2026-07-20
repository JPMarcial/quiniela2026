import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="España Campeón del Mundo 2026",
    page_icon="🏆",
    layout="centered"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        text-align: center;
    }
    .title-banner {
        background: linear-gradient(135deg, #c5221f 0%, #f1bf00 50%, #c5221f 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin-bottom: 25px;
    }
    .title-banner h1 {
        font-size: 36px;
        font-weight: 900;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .title-banner p {
        font-size: 20px;
        margin-top: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Banner de Felicitaciones
st.markdown("""
    <div class="title-banner">
        <h1>🇪🇸 ¡FELICIDADES ESPAÑA! 🇪🇸</h1>
        <p>🏆 CAMPEÓN DEL MUNDO 2026 🏆</p>
    </div>
""", unsafe_allow_html=True)

# URL cruda (raw) de la imagen en tu repositorio
IMAGE_URL = "https://raw.githubusercontent.com/JPMarcial/quiniela2026/main/02.jpeg"

# Despliegue de la imagen
st.image(IMAGE_URL, use_container_width=True)
