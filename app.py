import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS REFINADOS PARA LAS LÍNEAS
# ==============================================================================
st.set_page_config(page_title="Fase Final Mundial 2026", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .bracket-wrapper {
        background-color: #F8FAFC;
        padding: 40px 20px;
        border-radius: 16px;
    }
    .bracket-header {
        text-align: center;
        margin-bottom: 40px;
    }
    .bracket-header h1 { font-size: 32px; font-weight: 800; color: #1E3A8A; margin-bottom: 5px; text-transform: uppercase; }
    .bracket-header p { font-size: 14px; color: #64748B; }

    /* Estructura en Grid para las 9 Columnas de la Llave Simétrica */
    .bracket-container {
        display: grid;
        grid-template-columns: repeat(9, minmax(140px, 1fr));
        align-items: center;
        gap: 8px;
        width: 100%;
        overflow-x: auto;
    }

    .bracket-column {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 780px; /* Alineación vertical perfecta de las cajas */
    }

    /* Diseño Estilo Tarjeta de Partido */
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
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
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
    
    /* Resaltado de ganadores oficiales */
    .winner-highlight {
        background-color: #ECFDF5;
        color: #065F46 !important;
        font-weight: 800;
    }

    /* Bloque Central de la Copa */
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
        margin-top: 25px;
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        border: 2px solid #F59E0B;
        padding: 12px 20px;
        border-radius: 10px;
        box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# Listas de Cruces Base Estáticos de 16vos por Bloque de la Llave Real
CRUCES_IZQUIERDA = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), 
    ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), 
    ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal")
]

CRUCES_DERECHA = [
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), 
    ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), 
    ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

def buscar_ganador_columna_c(df, equipo1, equipo2):
    """
    Busca en el DataFrame si en la columna C (índice 2) se encuentra el ganador oficial
    del enfrentamiento directo entre ambos equipos.
    """
    for idx in range(len(df) - 1):
        c1 = str(df.iloc[idx, 1]).strip().lower()
        c2 = str(df.iloc[idx+1, 1]).strip().lower()
        
        # Si localizamos el par de celdas del partido
        if c1 == equipo1.lower() and c2 == equipo2.lower():
            g1 = str(df.iloc[idx, 2]).strip()
            g2 = str(df.iloc[idx+1, 2]).strip()
            
            # Verificamos si se asentó un marcador numérico para definir un ganador
            if g1.isdigit() and g2.isdigit():
                if int(g1) > int(g2): return equipo1
                if int(g2) > int(g1): return equipo2
    return "⌛"

@st.cache_data(ttl=10)
def cargar_datos_reales():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        
        arbol = {}
        
        # 1. RESOLVER 16VOS DE FINAL AUTOMÁTICAMENTE
        for i, (loc, vis) in enumerate(CRUCES_IZQUIERDA):
            gan = buscar_ganador_columna_c(df_res, loc, vis)
            arbol[f"IZQ_D16_{i+1}"] = {"local": loc, "visitante": vis, "ganador": gan}
            
        for i, (loc, vis) in enumerate(CRUCES_DERECHA):
            gan = buscar_ganador_columna_c(df_res, loc, vis)
            arbol[f"DER_D16_{i+1}"] = {"local": loc, "visitante": vis, "ganador": gan}
            
        # 2. RESOLVER OCTAVOS DE FINAL (Cruce exacto posicional 1vs2, 3vs4...)
        for i in range(1, 5):
            g1 = arbol[f"IZQ_D16_{2*i-1}"]["ganador"]
            g2 = arbol[f"IZQ_D16_{2*i}"]["ganador"]
            arbol[f"IZQ_OCT_{i}"] = {"local": g1 if g1 != "⌛" else "Por Definir", "visitante": g2 if g2 != "⌛" else "Por Definir"}
            arbol[f"IZQ_OCT_{i}"]["ganador"] = buscar_ganador_columna_c(df_res, arbol[f"IZQ_OCT_{i}"]["local"], arbol[f"IZQ_OCT_{i}"]["visitante"])
            
        for i in range(1, 5):
            g1 = arbol[f"DER_D16_{2*i-1}"]["ganador"]
            g2 = arbol[f"DER_D16_{2*i}"]["ganador"]
            arbol[f"DER_OCT_{i}"] = {"local": g1 if g1 != "⌛" else "Por Definir", "visitante": g2 if g2 != "⌛" else "Por Definir"}
            arbol[f"DER_OCT_{i}"]["ganador"] = buscar_ganador_columna_c(df_res, arbol[f"DER_OCT_{i}"]["local"], arbol[f"DER_OCT_{i}"]["visitante"])

        # 3. RESOLVER CUARTOS DE FINAL
        for i in range(1, 3):
            g1 = arbol[f"IZQ_OCT_{2*i-1}"]["ganador"]
            g2 = arbol[f"IZQ_OCT_{2*i}"]["ganador"]
            arbol[f"IZQ_CRT_{i}"] = {"local": g1 if g1 != "⌛" else "Por Definir", "visitante": g2 if g2 != "⌛" else "Por Definir"}
            arbol[f"IZQ_CRT_{i}"]["ganador"] = buscar_ganador_columna_c(df_res, arbol[f"IZQ_CRT_{i}"]["local"], arbol[f"IZQ_CRT_{i}"]["visitante"])

        for i in range(1, 3):
            g1 = arbol[f"DER_OCT_{2*i-1}"]["ganador"]
            g2 = arbol[f"DER_OCT_{2*i}"]["ganador"]
            arbol[f"DER_CRT_{i}"] = {"local": g1 if g1 != "⌛" else "Por Definir", "visitante": g2 if g2 != "⌛" else "Por Definir"}
            arbol[f"DER_CRT_{i}"]["ganador"] = buscar_ganador_columna_c(df_res, arbol[f"DER_CRT_{i}"]["local"], arbol[f"DER_CRT_{i}"]["visitante"])

        # 4. RESOLVER SEMIFINALES
        s_izq1 = arbol["IZQ_CRT_1"]["ganador"]
        s_izq2 = arbol["IZQ_CRT_2"]["ganador"]
        arbol["IZQ_SEM"] = {"local": s_izq1 if s_izq1 != "⌛" else "Por Definir", "visitante": s_izq2 if s_izq2 != "⌛" else "Por Definir"}
        arbol["IZQ_SEM"]["ganador"] = buscar_ganador_columna_c(df_res, arbol["IZQ_SEM"]["local"], arbol["IZQ_SEM"]["visitante"])

        s_der1 = arbol["DER_CRT_1"]["ganador"]
        s_der2 = arbol["DER_CRT_2"]["ganador"]
        arbol["DER_SEM"] = {"local": s_der1 if s_der1 != "⌛" else "Por Definir", "visitante": s_der2 if s_der2 != "⌛" else "Por Definir"}
        arbol["DER_SEM"]["ganador"] = buscar_ganador_columna_c(df_res, arbol["DER_SEM"]["local"], arbol["DER_SEM"]["visitante"])

        # 5. RESOLVER GRAN FINAL
        f_izq = arbol["IZQ_SEM"]["ganador"]
        f_der = arbol["DER_SEM"]["ganador"]
        arbol["FIN"] = {"local": f_izq if f_izq != "⌛" else "Por Definir", "visitante": f_der if f_der != "⌛" else "Por Definir"}
        arbol["FIN"]["ganador"] = buscar_ganador_columna_c(df_res, arbol["FIN"]["local"], arbol["FIN"]["visitante"])
        
        return arbol, None
    except Exception as e:
        return {}, f"Error al enlazar el bracket con el archivo: {str(e)}"

# Cargar la data estructurada de forma asíncrona
arbol_real, error = cargar_datos_reales()

if error:
    st.error(error)
else:
    def render_match_html(id_partido, meta_text=""):
        p = arbol_real.get(id_partido, {"local": "Por Definir", "visitante": "Por Definir", "ganador": "⌛"})
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
            <h1>FASE FINAL MUNDIAL 2026</h1>
            <p>Llave de eliminación directa actualizada en tiempo real según el marcador de goles oficial</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Inyección del contenedor HTML simétrico con las columnas sincronizadas
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
