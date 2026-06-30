import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS REFINADOS (ÁRBOL SIMÉTRICO)
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

    /* Estructura en Grid para las 9 Columnas Sincronizadas */
    .bracket-container {
        display: grid;
        grid-template-columns: repeat(9, minmax(140px, 1fr));
        align-items: center;
        gap: 10px;
        width: 100%;
        overflow-x: auto;
    }

    .bracket-column {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 800px;
    }

    /* Diseño de las Cajas de los Partidos */
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
    
    /* Resaltado del Ganador de Fase */
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

# ==============================================================================
# 2. LISTAS DE CRUCES ESTÁTICOS BASE (16VOS)
# ==============================================================================
IZQ_16VOS = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal")
]

DER_16VOS = [
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

def obtener_lista_columna(df, indice_col):
    """Extrae los nombres limpios de los equipos ingresados en una columna específica"""
    if indice_col < len(df.columns):
        return [str(x).strip().lower() for x in df.iloc[:, indice_col].dropna() if str(x).strip()]
    return []

@st.cache_data(ttl=5)
def cargar_sets_ganadores():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        
        # Mapeo directo de tus columnas indicadas (Letra -> Índice 0-based)
        # Columna G=6 (16vos), K=10 (Octavos), O=14 (Cuartos), S=18 (Semifinal), W=22 (Campeón)
        return {
            "16vos": obtener_lista_columna(df_res, 6),
            "octavos": obtener_lista_columna(df_res, 10),
            "cuartos": obtener_lista_columna(df_res, 14),
            "semis": obtener_lista_columna(df_res, 18),
            "campeon": obtener_lista_columna(df_res, 22)
        }, None
    except Exception as e:
        return {}, f"Error al cargar el archivo de resultados: {str(e)}"

ganadores, error = cargar_sets_ganadores()

if error:
    st.error(error)
else:
    # Selector de jugador para simulación o vista general (usando participantes si lo deseas)
    st.sidebar.title("Configuración")
    # Si tienes un diccionario de participantes cargado en otra parte, puedes usarlo aquí.
    
    # --------------------------------------------------------------------------
    # 3. LÓGICA DE DETECCIÓN SIMPLIFICADA (Avanza si el nombre está en el Set superior)
    # --------------------------------------------------------------------------
    def verificar_ganador(equipo, fase_key):
        if not equipo or equipo == "Por Definir":
            return False
        return equipo.lower() in ganadores.get(fase_key, [])

    def definir_cruce(eq1, eq2, fase_actual_key):
        """Si un equipo está en la lista de ganadores de la fase anterior, sube a la siguiente"""
        loc = eq1 if verificar_ganador(eq1, fase_actual_key) else "Por Definir"
        vis = eq2 if verificar_ganador(eq2, fase_actual_key) else "Por Definir"
        return loc, vis

    # Armar los pares dinámicos del árbol basándose únicamente en lo que ingresaste en las columnas
    arbol = {}
    
    # --- 16VOS ---
    for i, (l, v) in enumerate(IZQ_16VOS):
        arbol[f"IZQ_D16_{i+1}"] = {"l": l, "v": v, "gl": verificar_ganador(l, "16vos"), "gv": verificar_ganador(v, "16vos")}
    for i, (l, v) in enumerate(DER_16VOS):
        arbol[f"DER_D16_{i+1}"] = {"l": l, "v": v, "gl": verificar_ganador(l, "16vos"), "gv": verificar_ganador(v, "16vos")}

    # --- OCTAVOS ---
    for i in range(1, 5):
        # Elige el ganador del partido impar y par previo para armar el cruce de Octavos
        eq1 = IZQ_16VOS[2*i-2][0] if arbol[f"IZQ_D16_{2*i-1}"]["gl"] else (IZQ_16VOS[2*i-2][1] if arbol[f"IZQ_D16_{2*i-1}"]["gv"] else "Por Definir")
        eq2 = IZQ_16VOS[2*i-1][0] if arbol[f"IZQ_D16_{2*i}"]["gl"] else (IZQ_16VOS[2*i-1][1] if arbol[f"IZQ_D16_{2*i}"]["gv"] else "Por Definir")
        arbol[f"IZQ_OCT_{i}"] = {"l": eq1, "v": eq2, "gl": verificar_ganador(eq1, "octavos"), "gv": verificar_ganador(eq2, "octavos")}

    for i in range(1, 5):
        eq1 = DER_16VOS[2*i-2][0] if arbol[f"DER_D16_{2*i-1}"]["gl"] else (DER_16VOS[2*i-2][1] if arbol[f"DER_D16_{2*i-1}"]["gv"] else "Por Definir")
        eq2 = DER_16VOS[2*i-1][0] if arbol[f"DER_D16_{2*i}"]["gl"] else (DER_16VOS[2*i-1][1] if arbol[f"DER_D16_{2*i}"]["gv"] else "Por Definir")
        arbol[f"DER_OCT_{i}"] = {"l": eq1, "v": eq2, "gl": verificar_ganador(eq1, "octavos"), "gv": verificar_ganador(eq2, "octavos")}

    # --- CUARTOS ---
    for i in range(1, 3):
        eq1 = arbol[f"IZQ_OCT_{2*i-1}"]["l"] if arbol[f"IZQ_OCT_{2*i-1}"]["gl"] else (arbol[f"IZQ_OCT_{2*i-1}"]["v"] if arbol[f"IZQ_OCT_{2*i-1}"]["gv"] else "Por Definir")
        eq2 = arbol[f"IZQ_OCT_{2*i}"]["l"] if arbol[f"IZQ_OCT_{2*i}"]["gl"] else (arbol[f"IZQ_OCT_{2*i}"]["v"] if arbol[f"IZQ_OCT_{2*i}"]["gv"] else "Por Definir")
        arbol[f"IZQ_CRT_{i}"] = {"l": eq1, "v": eq2, "gl": verificar_ganador(eq1, "cuartos"), "gv": verificar_ganador(eq2, "cuartos")}

    for i in range(1, 3):
        eq1 = arbol[f"DER_OCT_{2*i-1}"]["l"] if arbol[f"DER_OCT_{2*i-1}"]["gl"] else (arbol[f"DER_OCT_{2*i-1}"]["v"] if arbol[f"DER_OCT_{2*i-1}"]["gv"] else "Por Definir")
        eq2 = arbol[f"DER_OCT_{2*i}"]["l"] if arbol[f"DER_OCT_{2*i}"]["gl"] else (arbol[f"DER_OCT_{2*i}"]["v"] if arbol[f"DER_OCT_{2*i}"]["gv"] else "Por Definir")
        arbol[f"DER_CRT_{i}"] = {"l": eq1, "v": eq2, "gl": verificar_ganador(eq1, "cuartos"), "gv": verificar_ganador(eq2, "cuartos")}

    # --- SEMIFINALES ---
    eq_si1 = arbol["IZQ_CRT_1"]["l"] if arbol["IZQ_CRT_1"]["gl"] else (arbol["IZQ_CRT_1"]["v"] if arbol["IZQ_CRT_1"]["gv"] else "Por Definir")
    eq_si2 = arbol["IZQ_CRT_2"]["l"] if arbol["IZQ_CRT_2"]["gl"] else (arbol["IZQ_CRT_2"]["v"] if arbol["IZQ_CRT_2"]["gv"] else "Por Definir")
    arbol["IZQ_SEM"] = {"l": eq_si1, "v": eq_si2, "gl": verificar_ganador(eq_si1, "semis"), "gv": verificar_ganador(eq_si2, "semis")}

    eq_sd1 = arbol["DER_CRT_1"]["l"] if arbol["DER_CRT_1"]["gl"] else (arbol["DER_CRT_1"]["v"] if arbol["DER_CRT_1"]["gv"] else "Por Definir")
    eq_sd2 = arbol["DER_CRT_2"]["l"] if arbol["DER_CRT_2"]["gl"] else (arbol["DER_CRT_2"]["v"] if arbol["DER_CRT_2"]["gv"] else "Por Definir")
    arbol["DER_SEM"] = {"l": eq_sd1, "v": eq_sd2, "gl": verificar_ganador(eq_sd1, "semis"), "gv": verificar_ganador(eq_sd2, "semis")}

    # --- GRAN FINAL ---
    fin_l = arbol["IZQ_SEM"]["l"] if arbol["IZQ_SEM"]["gl"] else (arbol["IZQ_SEM"]["v"] if arbol["IZQ_SEM"]["gv"] else "Por Definir")
    fin_v = arbol["DER_SEM"]["l"] if arbol["DER_SEM"]["gl"] else (arbol["DER_SEM"]["v"] if arbol["DER_SEM"]["gv"] else "Por Definir")
    arbol["FIN"] = {"l": fin_l, "v": fin_v, "gl": verificar_ganador(fin_l, "campeon"), "gv": verificar_ganador(fin_v, "campeon")}

    # Obtener Campeón Final
    campeon_final = "⌛"
    if arbol["FIN"]["gl"]: campeon_final = arbol["FIN"]["l"]
    elif arbol["FIN"]["gv"]: campeon_final = arbol["FIN"]["v"]

    # Función local de renderizado HTML limpio
    def render_match_html(id_partido, meta_text=""):
        p = arbol.get(id_partido, {"l": "Por Definir", "v": "Por Definir", "gl": False, "gv": False})
        c_loc = "winner-highlight" if p["gl"] else ""
        c_vis = "winner-highlight" if p["gv"] else ""
        return f"""
        <div>
            <div class="match-meta">{meta_text}</div>
            <div class="match-box">
                <div class="team-row {c_loc}"><span>{p['l']}</span></div>
                <div class="team-row {c_vis}"><span>{p['v']}</span></div>
            </div>
        </div>
        """

    # Rendering Principal de la Aplicación
    st.markdown('<div class="bracket-wrapper">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="bracket-header">
            <h1>FASE FINAL MUNDIAL 2026</h1>
            <p>Visualización del flujo del torneo sincronizado directamente con la lista de aciertos oficiales</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

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
