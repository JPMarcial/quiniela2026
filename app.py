import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (ÁRBOL SIMÉTRICO ESTILO COPA)
# ==============================================================================
st.set_page_config(page_title="Quiniela 2026 - Árbol Fase Final", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .bracket-wrapper {
        background-color: #F8FAFC;
        padding: 30px 20px;
        border-radius: 16px;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.02);
    }
    .bracket-header {
        text-align: center;
        margin-bottom: 35px;
    }
    .bracket-header h1 { font-size: 28px; font-weight: 800; color: #1E3A8A; margin-bottom: 5px; }
    .bracket-header p { font-size: 14px; color: #64748B; }

    /* Contenedor Grid Principal de 9 Columnas Sincronizadas */
    .bracket-container {
        display: grid;
        grid-template-columns: repeat(9, minmax(130px, 1fr));
        align-items: center;
        gap: 10px;
        width: 100%;
        overflow-x: auto;
    }

    /* Columnas de Rondas */
    .bracket-column {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 720px; /* Altura fija para balancear las filas verticalmente */
    }

    /* Cajas de Partido */
    .match-meta {
        font-size: 9px;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        margin-bottom: 3px;
        text-align: center;
    }
    .match-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        overflow: hidden;
    }
    .team-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 600;
        color: #334155;
        border-bottom: 1px solid #F1F5F9;
    }
    .team-row:last-child { border-bottom: none; }
    
    /* Resaltado de Ganador Oficial */
    .winner-highlight {
        background-color: #ECFDF5;
        color: #065F46 !important;
        font-weight: 800;
    }

    /* Centro del Árbol (Trofco y Final) */
    .center-trophy {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        height: 100%;
    }
    .trophy-title {
        font-size: 10px;
        font-weight: 800;
        color: #B45309;
        margin-bottom: 8px;
    }
    .champion-display {
        margin-top: 20px;
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border: 2px solid #F59E0B;
        padding: 12px 15px;
        border-radius: 10px;
        box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# URL pública de tu Google Drive
FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# Mapeo exacto de los Cruces Oficiales de 16vos distribuidos geográficamente (Izquierda y Derecha)
CRUCES_IZQUIERDA = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal")
]

CRUCES_DERECHA = [
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

def extraer_set_resultados(df, num_columna):
    if len(df.columns) > num_columna:
        return set(df.iloc[:, num_columna].dropna().astype(str).str.strip().str.lower())
    return set()

@st.cache_data(ttl=10)
def cargar_datos_reales():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        
        # Extracción de sets oficiales de ganadores de cada fase
        res_16vos = extraer_set_resultados(df_res, 6)   # Columna G
        res_octavos = extraer_set_resultados(df_res, 8) # Columna I
        res_cuartos = extraer_set_resultados(df_res, 10) # Columna K
        
        # Armar base de datos real del árbol
        arbol = {}
        
        # --- PROCESAR 16VOS ---
        # Bloque Izquierdo
        for idx, (loc, vis) in enumerate(CRUCES_IZQUIERDA):
            gan = loc if loc.lower() in res_16vos else (vis if vis.lower() in res_16vos else "⌛")
            arbol[f"IZQ_D16_{idx+1}"] = {"local": loc, "visitante": vis, "ganador": gan}
        # Bloque Derecho
        for idx, (loc, vis) in enumerate(CRUCES_DERECHA):
            gan = loc if loc.lower() in res_16vos else (vis if vis.lower() in res_16vos else "⌛")
            arbol[f"DER_D16_{idx+1}"] = {"local": loc, "visitante": vis, "ganador": gan}
            
        # --- PROCESAR OCTAVOS DE FINAL ---
        for i in range(1, 5):
            l1, v1 = arbol[f"IZQ_D16_{2*i-1}"]["ganador"], arbol[f"IZQ_D16_{2*i}"]["ganador"]
            arbol[f"IZQ_OCT_{i}"] = {"local": l1 if l1 != "⌛" else "Por Definir", "visitante": v1 if v1 != "⌛" else "Por Definir"}
            arbol[f"IZQ_OCT_{i}"]["ganador"] = arbol[f"IZQ_OCT_{i}"]["local"] if arbol[f"IZQ_OCT_{i}"]["local"].lower() in res_octavos else (arbol[f"IZQ_OCT_{i}"]["visitante"] if arbol[f"IZQ_OCT_{i}"]["visitante"].lower() in res_octavos else "⌛")
            
        for i in range(1, 5):
            l2, v2 = arbol[f"DER_D16_{2*i-1}"]["ganador"], arbol[f"DER_D16_{2*i}"]["ganador"]
            arbol[f"DER_OCT_{i}"] = {"local": l2 if l2 != "⌛" else "Por Definir", "visitante": v2 if v2 != "⌛" else "Por Definir"}
            arbol[f"DER_OCT_{i}"]["ganador"] = arbol[f"DER_OCT_{i}"]["local"] if arbol[f"DER_OCT_{i}"]["local"].lower() in res_octavos else (arbol[f"DER_OCT_{i}"]["visitante"] if arbol[f"DER_OCT_{i}"]["visitante"].lower() in res_octavos else "⌛")

        # --- PROCESAR CUARTOS DE FINAL ---
        for i in range(1, 3):
            l, v = arbol[f"IZQ_OCT_{2*i-1}"]["ganador"], arbol[f"IZQ_OCT_{2*i}"]["ganador"]
            arbol[f"IZQ_CRT_{i}"] = {"local": l if l != "⌛" else "Por Definir", "visitante": v if v != "⌛" else "Por Definir"}
            arbol[f"IZQ_CRT_{i}"]["ganador"] = arbol[f"IZQ_CRT_{i}"]["local"] if arbol[f"IZQ_CRT_{i}"]["local"].lower() in res_cuartos else (arbol[f"IZQ_CRT_{i}"]["visitante"] if arbol[f"IZQ_CRT_{i}"]["visitante"].lower() in res_cuartos else "⌛")

        for i in range(1, 3):
            l, v = arbol[f"DER_OCT_{2*i-1}"]["ganador"], arbol[f"DER_OCT_{2*i}"]["ganador"]
            arbol[f"DER_CRT_{i}"] = {"local": l if l != "⌛" else "Por Definir", "visitante": v if v != "⌛" else "Por Definir"}
            arbol[f"DER_CRT_{i}"]["ganador"] = arbol[f"DER_CRT_{i}"]["local"] if arbol[f"DER_CRT_{i}"]["local"].lower() in res_cuartos else (arbol[f"DER_CRT_{i}"]["visitante"] if arbol[f"DER_CRT_{i}"]["visitante"].lower() in res_cuartos else "⌛")

        # --- SEMIFINALES ---
        l_semi_izq, v_semi_izq = arbol["IZQ_CRT_1"]["ganador"], arbol["IZQ_CRT_2"]["ganador"]
        arbol["IZQ_SEM"] = {"local": l_semi_izq if l_semi_izq != "⌛" else "Por Definir", "visitante": v_semi_izq if v_semi_izq != "⌛" else "Por Definir", "ganador": "⌛"}
        
        l_semi_der, v_semi_der = arbol["DER_CRT_1"]["ganador"], arbol["DER_CRT_2"]["ganador"]
        arbol["DER_SEM"] = {"local": l_semi_der if l_semi_der != "⌛" else "Por Definir", "visitante": v_semi_der if v_semi_der != "⌛" else "Por Definir", "ganador": "⌛"}

        # --- GRAN FINAL ---
        arbol["FIN"] = {"local": "Por Definir", "visitante": "Por Definir", "ganador": "⌛"}
        
        return arbol, None
    except Exception as e:
        return {}, f"Error al procesar datos: {str(e)}"

arbol_real, error = cargar_datos_reales()

if error:
    st.error(error)
else:
    # Función para renderizar cajas HTML usando los datos leídos en tiempo real
    def render_match_html(id_partido, meta_text=""):
        p = arbol_real.get(id_partido, {"local": "⌛ Pending", "visitante": "⌛ Pending", "ganador": "⌛"})
        loc, vis, gan = p["local"], p["visitante"], p["ganador"]
        
        c_loc = "winner-highlight" if gan == loc and loc != "Por Definir" else ""
        c_vis = "winner-highlight" if gan == vis and vis != "Por Definir" else ""
        
        return f"""
        <div>
            <div class="match-meta">{meta_text}</div>
            <div class="match-box">
                <div class="team-row {c_loc}"><span>{loc}</span></div>
                <div class="team-row {c_vis}"><span>{vis}</span></div>
            </div>
        </div>
        """

    campeon_final = arbol_real.get("FIN", {}).get("ganador", "⌛")

    st.markdown('<div class="bracket-wrapper">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="bracket-header">
            <h1>🏆 ARBOL OFICIAL DE LA QUINIELA 🏆</h1>
            <p>Estructura de fase final actualizada dinámicamente con los resultados ingresados en la hoja de cálculo</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Inyección estructurada de las 9 columnas balanceadas
    html_llave = f"""
    <div class="bracket-container">
        
        <div class="bracket-column">
            {render_match_html("IZQ_D16_1", "28/06 Los Ángeles")}
            {render_match_html("IZQ_D16_2", "29/06 Boston")}
            {render_match_html("IZQ_D16_3", "29/06 Monterrey")}
            {render_match_html("IZQ_D16_4", "29/06 Houston")}
            {render_match_html("IZQ_D16_5", "30/06 NY/NJ")}
            {render_match_html("IZQ_D16_6", "30/06 Dallas")}
            {render_match_html("IZQ_D16_7", "30/06 CDMX")}
            {render_match_html("IZQ_D16_8", "01/07 Atlanta")}
        </div>
        
        <div class="bracket-column">
            {render_match_html("IZQ_OCT_1", "04/07 Filadelfia")}
            {render_match_html("IZQ_OCT_2", "04/07 Houston")}
            {render_match_html("IZQ_OCT_3", "06/07 Dallas")}
            {render_match_html("IZQ_OCT_4", "06/07 CDMX")}
        </div>
        
        <div class="bracket-column">
            {render_match_html("IZQ_CRT_1", "09/07 Boston")}
            {render_match_html("IZQ_CRT_2", "10/07 Los Ángeles")}
        </div>
        
        <div class="bracket-column">
            {render_match_html("IZQ_SEM", "14/07 Dallas")}
        </div>
        
        <div class="center-trophy">
            <div class="trophy-title">19/07 Nueva York</div>
            {render_match_html("FIN", "GRAN FINAL")}
            <div class="champion-display">
                <div style="font-size: 10px; font-weight: bold; opacity: 0.9; letter-spacing: 1px;">CAMPEÓN MUNDIAL</div>
                <div>🏆 {campeon_final}</div>
            </div>
        </div>
        
        <div class="bracket-column">
            {render_match_html("DER_SEM", "15/07 Atlanta")}
        </div>
        
        <div class="bracket-column">
            {render_match_html("DER_CRT_1", "11/07 Miami")}
            {render_match_html("DER_CRT_2", "11/07 Kansas City")}
        </div>
        
        <div class="bracket-column">
            {render_match_html("DER_OCT_1", "05/07 CDMX")}
            {render_match_html("DER_OCT_2", "05/07 Nueva York")}
            {render_match_html("DER_OCT_3", "07/07 Atlanta")}
            {render_match_html("DER_OCT_4", "07/07 Vancouver")}
        </div>
        
        <div class="bracket-column">
            {render_match_html("DER_D16_1", "01/07 S. Francisco")}
            {render_match_html("DER_D16_2", "01/07 Seattle")}
            {render_match_html("DER_D16_3", "02/07 Toronto")}
            {render_match_html("DER_D16_4", "02/07 Los Ángeles")}
            {render_match_html("DER_D16_5", "02/07 Vancouver")}
            {render_match_html("DER_D16_6", "03/07 Miami")}
            {render_match_html("DER_D16_7", "03/07 Kansas City")}
            {render_match_html("DER_D16_8", "03/07 Dallas")}
        </div>

    </div>
    """
    
    st.markdown(html_llave, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
