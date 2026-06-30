import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS REFINADOS (LLAVE 100% GRÁFICA)
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

    /* Cuadrícula Grid balanceada para las 9 Columnas de la Llave */
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
        height: 850px;
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
    
    /* Resaltado Verde para Aciertos */
    .winner-highlight {
        background-color: #ECFDF5;
        color: #065F46 !important;
        font-weight: 800;
    }

    /* Estilos del Bloque del Trofeo Central */
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
        padding: 10px 16px;
        border-radius: 10px;
        box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# Estructura del orden de renderizado para la primera columna de base (16vos)
IZQ_16VOS = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal")
]

DER_16VOS = [
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

# ==============================================================================
# 2. CAPTURA SEGURA DE DATOS POR COORDENADAS COGNITIVAS
# ==============================================================================
def extraer_nombre_celda(df, fila, columna, default="Por Definir"):
    """Extrae el nombre de una coordenada del dataframe de forma segura sin romper el flujo"""
    try:
        if fila < len(df) and columna < len(df.columns):
            val = str(df.iloc[fila, columna]).strip()
            if val and val.lower() != "nan" and val.lower() != "0":
                return val
    except:
        pass
    return default

def mapear_hoja_completa(df):
    """
    Lee las columnas mapeando por coordenadas relativas directas
    B=1 (16vos), G=6 (Octavos), K=10 (Cuartos), O=14 (Semis), S=18 (3er Lugar), W=22 (Finales)
    """
    datos = {
        "16vos": [extraer_nombre_celda(df, r, 1) for r in range(len(df))],
        "octavos": [extraer_nombre_celda(df, r, 6) for r in range(len(df))],
        "cuartos": [extraer_nombre_celda(df, r, 10) for r in range(len(df))],
        "semis": [extraer_nombre_celda(df, r, 14) for r in range(len(df))],
        "tercer_lugar": [extraer_nombre_celda(df, r, 18) for r in range(len(df))],
        "campeon": [extraer_nombre_celda(df, r, 22) for r in range(len(df))]
    }
    return datos

@st.cache_data(ttl=5)
def cargar_tablas_quiniela():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        
        # Cargar hoja de control de resultados reales
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        resultados_reales = mapear_hoja_completa(df_res)
        
        # Cargar hojas de los participantes de manera dinámica
        datos_participantes = {}
        for hoja in xls.sheet_names:
            if hoja.upper() not in ['RESULTADOS', 'INICIO', 'CONFIG', 'SHEET1', 'CALENDARIO', 'MURO']:
                df_part = pd.read_excel(xls, sheet_name=hoja, header=None)
                datos_participantes[hoja] = mapear_hoja_completa(df_part)
                
        return resultados_reales, datos_participantes, None
    except Exception as e:
        return {}, {}, f"Error de lectura en archivo de quiniela: {str(e)}"

resultados_reales, participantes, error = cargar_tablas_quiniela()

if error:
    st.error(error)
else:
    # Sidebar de Navegación Lateral
    st.sidebar.title("👤 Visor de Quinielas")
    opciones = ["Resultados Oficiales"] + sorted(list(participantes.keys()))
    seleccion = st.sidebar.selectbox("Seleccione un participante para ver su llave:", opciones)
    
    es_real = seleccion == "Resultados Oficiales"
    fuente = resultados_reales if es_real else participantes[seleccion]

    # ==============================================================================
    # 3. LÓGICA DE COMPARACIÓN DIRECTA CONTRA "RESULTADOS" (CONTROL DE ACUERDOS)
    # ==============================================================================
    def verificar_coincidencia(equipo, llave_fase):
        """Busca si el equipo ingresado por el usuario fue un acierto real en esa fase"""
        if not equipo or equipo == "Por Definir":
            return False
        # Buscamos en toda la columna correspondiente de resultados oficiales
        lista_oficial = [str(x).lower() for x in resultados_reales.get(llave_fase, [])]
        return equipo.lower() in lista_oficial

    # Estructurar la matriz limpia para pasar las variables directamente al HTML
    arbol = {}

    # --- FASE 16VOS ---
    for i, (l, v) in enumerate(IZQ_16VOS):
        arbol[f"IZQ_D16_{i+1}"] = {"l": l, "v": v, "gl": verificar_coincidencia(l, "16vos"), "gv": verificar_coincidencia(v, "16vos")}
    for i, (l, v) in enumerate(DER_16VOS):
        arbol[f"DER_D16_{i+1}"] = {"l": l, "v": v, "gl": verificar_coincidencia(l, "16vos"), "gv": verificar_coincidencia(v, "16vos")}

    # --- FASE OCTAVOS ---
    # Se obtienen secuencialmente las posiciones válidas de la columna G (índice 6)
    for i in range(4):
        l_izq = fuente["octavos"][2*i] if i*2 < len(fuente["octavos"]) else "Por Definir"
        v_izq = fuente["octavos"][2*i+1] if i*2+1 < len(fuente["octavos"]) else "Por Definir"
        arbol[f"IZQ_OCT_{i+1}"] = {"l": l_izq, "v": v_izq, "gl": verificar_coincidencia(l_izq, "octavos"), "gv": verificar_coincidencia(v_izq, "octavos")}

        l_der = fuente["octavos"][8+2*i] if 8+2*i < len(fuente["octavos"]) else "Por Definir"
        v_der = fuente["octavos"][8+2*i+1] if 8+2*i+1 < len(fuente["octavos"]) else "Por Definir"
        arbol[f"DER_OCT_{i+1}"] = {"l": l_der, "v": v_der, "gl": verificar_coincidencia(l_der, "octavos"), "gv": verificar_coincidencia(v_der, "octavos")}

    # --- FASE CUARTOS ---
    for i in range(2):
        l_izq = fuente["cuartos"][2*i] if i*2 < len(fuente["cuartos"]) else "Por Definir"
        v_izq = fuente["cuartos"][2*i+1] if i*2+1 < len(fuente["cuartos"]) else "Por Definir"
        arbol[f"IZQ_CRT_{i+1}"] = {"l": l_izq, "v": v_izq, "gl": verificar_coincidencia(l_izq, "cuartos"), "gv": verificar_coincidencia(v_izq, "cuartos")}

        l_der = fuente["cuartos"][4+2*i] if 4+2*i < len(fuente["cuartos"]) else "Por Definir"
        v_der = fuente["cuartos"][4+2*i+1] if 4+2*i+1 < len(fuente["cuartos"]) else "Por Definir"
        arbol[f"DER_CRT_{i+1}"] = {"l": l_der, "v": v_der, "gl": verificar_coincidencia(l_der, "cuartos"), "gv": verificar_coincidencia(v_der, "cuartos")}

    # --- FASE SEMIFINALES ---
    l_s_izq = fuente["semis"][0] if len(fuente["semis"]) > 0 else "Por Definir"
    v_s_izq = fuente["semis"][1] if len(fuente["semis"]) > 1 else "Por Definir"
    arbol["IZQ_SEM"] = {"l": l_s_izq, "v": v_s_izq, "gl": verificar_coincidencia(l_s_izq, "semis"), "gv": verificar_coincidencia(v_s_izq, "semis")}

    l_s_der = fuente["semis"][2] if len(fuente["semis"]) > 2 else "Por Definir"
    v_s_der = fuente["semis"][3] if len(fuente["semis"]) > 3 else "Por Definir"
    arbol["DER_SEM"] = {"l": l_s_der, "v": v_s_der, "gl": verificar_coincidencia(l_s_der, "semis"), "gv": verificar_coincidencia(v_s_der, "semis")}

    # --- TERCER LUGAR Y GRAN FINAL ---
    tl_l = fuente["tercer_lugar"][0] if len(fuente["tercer_lugar"]) > 0 else "Por Definir"
    tl_v = fuente["tercer_lugar"][1] if len(fuente["tercer_lugar"]) > 1 else "Por Definir"
    arbol["3ER"] = {"l": tl_l, "v": tl_v, "gl": verificar_coincidencia(tl_l, "tercer_lugar"), "gv": verificar_coincidencia(tl_v, "tercer_lugar")}

    f_l = fuente["campeon"][0] if len(fuente["campeon"]) > 0 else "Por Definir"
    f_v = fuente["campeon"][1] if len(fuente["campeon"]) > 1 else "Por Definir"
    arbol["FIN"] = {"l": f_l, "v": f_v, "gl": verificar_coincidencia(f_l, "campeon"), "gv": verificar_coincidencia(f_v, "campeon")}

    # Obtener el Campeón definitivo asentado en la celda final de la columna W
    campeon_final = "⌛"
    if len(fuente["campeon"]) > 2:
        val_c = fuente["campeon"][2]
        if val_c != "Por Definir": campeon_final = val_c

    # Función generadora de cajas HTML sanitizadas
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

    # ==============================================================================
    # 4. INYECCIÓN TOTAL EN PANTALLA DE LA INTERFAZ COMPLETA
    # ==============================================================================
    st.markdown('<div class="bracket-wrapper">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="bracket-header">
            <h1>FASE FINAL MUNDIAL 2026</h1>
            <p>Visualización en formato de llave gráfica para: <b>{seleccion}</b></p>
        </div>
    """, unsafe_allow_html=True)

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
            <div style="margin-bottom: 40px; width: 100%;">
                {render_match_html("FIN", "GRAN FINAL 19/07")}
            </div>
            <div style="width: 100%;">
                {render_match_html("3ER", "TERCER LUGAR 18/07")}
            </div>
            <div class="champion-display">
                <div style="font-size: 9px; font-weight: bold; opacity: 0.9; letter-spacing: 1px;">CAMPEÓN MUNDIAL</div>
                <div style="font-size: 14px; font-weight: 800; color: #1E3A8A; margin-top:4px;">🏆 {campeon_final}</div>
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
    
    st.write(html_llave, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
