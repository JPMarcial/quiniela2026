import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (ÁRBOL SIMÉTRICO DE 9 COLUMNAS)
# ==============================================================================
st.set_page_config(page_title="Quiniela Mundial 2026 - Fase Final", page_icon="🏆", layout="wide")

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

    /* Contenedor Grid Sincronizado para las 9 Columnas de la Llave */
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

    /* Diseño de las Tarjetas de Partidos */
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
    
    /* Resaltado de Acierto / Ganador Oficial */
    .winner-highlight {
        background-color: #ECFDF5;
        color: #065F46 !important;
        font-weight: 800;
    }

    /* Bloque Central de Finales y Copa */
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

# Cruces Base Iniciales (Estáticos en Columna B para renderizar el orden del árbol)
IZQ_16VOS = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal")
]

DER_16VOS = [
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

# ==============================================================================
# 2. CARGA EXCEL Y EXTRACCIÓN MAESTRA DE COLUMNAS (B, G, K, O, S, W)
# ==============================================================================
def extraer_lista_columna(df, indice_col):
    if indice_col < len(df.columns):
        return [str(x).strip().lower() for x in df.iloc[:, indice_col].dropna() if str(x).strip()]
    return []

def mapear_hoja_fase(df):
    """Mapea las columnas indicadas: B=1, G=6, K=10, O=14, S=18, W=22"""
    return {
        "16vos": extraer_lista_columna(df, 1),
        "octavos": extraer_lista_columna(df, 6),
        "cuartos": extraer_lista_columna(df, 10),
        "semis": extraer_lista_columna(df, 14),
        "tercer_lugar": extraer_lista_columna(df, 18),
        "campeon": extraer_lista_columna(df, 22)
    }

@st.cache_data(ttl=5)
def cargar_toda_la_quiniela():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        
        # Cargar hoja oficial de resultados reales
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        datos_resultados = mapear_hoja_fase(df_res)
        
        # Cargar hojas de los participantes dinámicamente
        datos_participantes = {}
        for nombre_hoja in xls.sheet_names:
            if nombre_hoja.upper() not in ['RESULTADOS', 'INICIO', 'CONFIG', 'SHEET1']:
                df_part = pd.read_excel(xls, sheet_name=nombre_hoja, header=None)
                datos_participantes[nombre_hoja] = mapear_hoja_fase(df_part)
                
        return datos_resultados, datos_participantes, None
    except Exception as e:
        return {}, {}, f"Error al procesar el archivo Excel: {str(e)}"

resultados_reales, participantes, error = cargar_toda_la_quiniela()

if error:
    st.error(error)
else:
    # Sidebar para control de visualización
    st.sidebar.title("🏆 Navegación")
    opciones_visor = ["Resultados Oficiales"] + sorted(list(participantes.keys()))
    visor_seleccionado = st.sidebar.selectbox("Selecciona qué llave visualizar:", opciones_visor)
    
    # Determinar qué datos renderizar en la estructura gráfica
    es_real = visor_seleccionado == "Resultados Oficiales"
    fuente_datos = resultados_reales if es_real else participantes[visor_seleccionado]

    # ==============================================================================
    # 3. LÓGICA DE CONSTRUCCIÓN DINÁMICA DEL ÁRBOL
    # ==============================================================================
    def verificar_acierto(equipo, fase_key):
        """Verifica si el equipo sugerido por el participante está en los resultados oficiales de esa fase"""
        if not equipo or equipo == "por definir":
            return False
        return equipo.lower() in resultados_reales.get(fase_key, [])

    def obtener_nombre_seguro(lista, indice, default="Por Definir"):
        if indice < len(lista):
            val = str(lista[indice]).strip()
            return val if val and val.lower() != "nan" else default
        return default

    arbol = {}

    # --- 16VOS DE FINAL (Columna B de la fuente) ---
    # Para resultados reales o predicciones, mapeamos los nombres en el orden estático
    for i, (l, v) in enumerate(IZQ_16VOS):
        arbol[f"IZQ_D16_{i+1}"] = {"l": l, "v": v, "gl": verificar_acierto(l, "16vos"), "gv": verificar_acierto(v, "16vos")}
    for i, (l, v) in enumerate(DER_16VOS):
        arbol[f"DER_D16_{i+1}"] = {"l": l, "v": v, "gl": verificar_acierto(l, "16vos"), "gv": verificar_acierto(v, "16vos")}

    # --- OCTAVOS DE FINAL (Columna G de la fuente) ---
    # Extraemos directamente del arreglo de la columna G (índice secuencial para rellenar los 4 partidos por lado)
    for i in range(4):
        l_izq = obtener_nombre_seguro(fuente_datos["octavos"], 2 * i)
        v_izq = obtener_nombre_seguro(fuente_datos["octavos"], 2 * i + 1)
        arbol[f"IZQ_OCT_{i+1}"] = {"l": l_izq, "v": v_izq, "gl": verificar_acierto(l_izq, "octavos"), "gv": verificar_acierto(v_izq, "octavos")}
        
        l_der = obtener_nombre_seguro(fuente_datos["octavos"], 8 + 2 * i)
        v_der = obtener_nombre_seguro(fuente_datos["octavos"], 8 + 2 * i + 1)
        arbol[f"DER_OCT_{i+1}"] = {"l": l_der, "v": v_der, "gl": verificar_acierto(l_der, "octavos"), "gv": verificar_acierto(v_der, "octavos")}

    # --- CUARTOS DE FINAL (Columna K de la fuente) ---
    for i in range(2):
        l_izq = obtener_nombre_seguro(fuente_datos["cuartos"], 2 * i)
        v_izq = obtener_nombre_seguro(fuente_datos["cuartos"], 2 * i + 1)
        arbol[f"IZQ_CRT_{i+1}"] = {"l": l_izq, "v": v_izq, "gl": verificar_acierto(l_izq, "cuartos"), "gv": verificar_acierto(v_izq, "cuartos")}

        l_der = obtener_nombre_seguro(fuente_datos["cuartos"], 4 + 2 * i)
        v_der = Pattern = obtener_nombre_seguro(fuente_datos["cuartos"], 4 + 2 * i + 1)
        arbol[f"DER_CRT_{i+1}"] = {"l": l_der, "v": v_der, "gl": verificar_acierto(l_der, "cuartos"), "gv": verificar_acierto(v_der, "cuartos")}

    # --- SEMIFINALES (Columna O de la fuente) ---
    l_semi_izq = obtener_nombre_seguro(fuente_datos["semis"], 0)
    v_semi_izq = obtener_nombre_seguro(fuente_datos["semis"], 1)
    arbol["IZQ_SEM"] = {"l": l_semi_izq, "v": v_semi_izq, "gl": verificar_acierto(l_semi_izq, "semis"), "gv": verificar_acierto(v_semi_izq, "semis")}

    l_semi_der = obtener_nombre_seguro(fuente_datos["semis"], 2)
    v_semi_der = obtener_nombre_seguro(fuente_datos["semis"], 3)
    arbol["DER_SEM"] = {"l": l_semi_der, "v": v_semi_der, "gl": verificar_acierto(l_semi_der, "semis"), "gv": verificar_acierto(v_semi_der, "semis")}

    # --- TERCER LUGAR Y GRAN FINAL (Columnas S y W) ---
    tl_l = obtener_nombre_seguro(fuente_datos["tercer_lugar"], 0)
    tl_v = obtener_nombre_seguro(fuente_datos["tercer_lugar"], 1)
    arbol["3ER"] = {"l": tl_l, "v": tl_v, "gl": verificar_acierto(tl_l, "tercer_lugar"), "gv": verificar_acierto(tl_v, "tercer_lugar")}

    f_l = obtener_nombre_seguro(fuente_datos["campeon"], 0)
    f_v = obtener_nombre_seguro(fuente_datos["campeon"], 1)
    arbol["FIN"] = {"l": f_l, "v": f_v, "gl": verificar_acierto(f_l, "campeon"), "gv": verificar_acierto(f_v, "campeon")}

    # Determinar Campeón
    campeon_final = "⌛"
    if len(fuente_datos["campeon"]) > 2:
        posible_camp = obtener_nombre_seguro(fuente_datos["campeon"], 2)
        if posible_camp != "Por Definir":
            campeon_final = posible_camp

    # Helper para armar bloques HTML limpios
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
    # 4. RENDERIZADO DE LA ESTRUCTURA VISUAL DE LA LLAVE
    # ==============================================================================
    st.markdown('<div class="bracket-wrapper">', unsafe_allow_html=True)
    st.markdown(f"""
        <div class="bracket-header">
            <h1>FASE ELIMINATORIA QUINIELA 2026</h1>
            <p>Visualizando la llave de: <b>{visor_seleccionado}</b></p>
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
            <div style="margin-bottom: 40px;">
                {render_match_html("FIN", "GRAN FINAL 19/07")}
            </div>
            <div>
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
    
    st.markdown(html_llave, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
