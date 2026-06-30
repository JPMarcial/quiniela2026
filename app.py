import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS CSS DE LA LLAVE
# ==============================================================================
st.set_page_config(
    page_title="Quiniela Mundial 2026 - Árbol de Llaves",
    page_icon="🏆",
    layout="wide"
)

# Estilos CSS para maquetar las casillas de los partidos simulando un árbol de llaves
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 5px; }
    .subtitle { font-size: 14px; color: #64748B; text-align: center; margin-bottom: 25px; }
    
    /* Contenedores de Partidos de la Llave */
    .match-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .match-box-header {
        font-size: 10px;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        margin-bottom: 6px;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 2px;
    }
    .team-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
        font-size: 13px;
    }
    .team-name { font-weight: 600; color: #1E293B; }
    .team-winner { color: #10B981; font-weight: 700; }
    
    /* Micro-avatares / Iniciales dentro de la llave */
    .avatar-container {
        margin-top: 4px;
        display: flex;
        flex-wrap: wrap;
        gap: 3px;
    }
    .avatar-chip {
        background-color: #EFF6FF;
        color: #2563EB;
        font-size: 9px;
        font-weight: 700;
        padding: 1px 5px;
        border-radius: 4px;
        border: 1px solid #BFDBFE;
    }
    .avatar-chip-real {
        background-color: #ECFDF5;
        color: #059669;
        border-color: #A7F3D0;
    }
    </style>
""", unsafe_allow_html=True)

FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# Lista estricta para el filtrado e iniciales
PAISES_VALIDOS = {
    "alemania", "paraguay", "francia", "suecia", "sudafrica", "canada", 
    "paises bajos", "marruecos", "portugal", "croacia", "españa", "austria", 
    "estados unidos", "bosnia-herz", "bosnia", "belgica", "senegal", "brasil", 
    "japon", "costa marfil", "costa de marfil", "noruega", "mexico", "ecuador", 
    "inglaterra", "congo", "argentina", "cabo verde", "australia", "egipto", 
    "suiza", "argelia", "colombia", "ghana"
}

def obtener_iniciales(nombre):
    partes = nombre.split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    return nombre[:2].upper()

def extraer_arbol_por_columnas(df):
    """Mapea las elecciones por columnas para saber exactamente en qué ronda posicionar cada equipo."""
    rondas = {"ronda1": set(), "ronda2": set(), "ronda3": set()}
    
    # Columna G (Índice 6): Ganadores de la Primera Ronda
    if len(df.columns) > 6:
        for val in df.iloc[:, 6].dropna().astype(str).str.strip():
            if val.lower() in PAISES_VALIDOS: rondas["ronda1"].add(val.lower())
            
    # Columnas posteriores (Siguientes llaves simuladas)
    if len(df.columns) > 8:
        for val in df.iloc[:, 8].dropna().astype(str).str.strip():
            if val.lower() in PAISES_VALIDOS: rondas["ronda2"].add(val.lower())
            
    if len(df.columns) > 10:
        for val in df.iloc[:, 10].dropna().astype(str).str.strip():
            if val.lower() in PAISES_VALIDOS: rondas["ronda3"].add(val.lower())
            
    return rondas

# Enfoque simplificado de los cruces de primera ronda fijos (Columna B de tu archivo)
CRUCES_INICIALES = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal"),
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

@st.cache_data(ttl=15)
def procesar_datos_torneo():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        
        # 1. Datos reales del Muro/Resultados oficiales
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        reales_por_ronda = extraer_arbol_por_columnas(df_res)
        
        participantes_datos = []
        hojas_excluidas = ['RESULTADOS', 'MURO', 'CALENDARIO']
        pestanas_jugadores = [p for p in xls.sheet_names if p.upper() not in hojas_excluidas and p.strip() != '']
        
        for p in pestanas_jugadores:
            df_part = pd.read_excel(xls, sheet_name=p, header=None)
            
            nombre_mostrar = p
            try:
                celda = str(df_part.iloc[1, 1]).strip()
                if celda and celda.lower() != 'nan' and len(celda) > 3: nombre_mostrar = celda
            except: pass
            
            pronosticos = extraer_arbol_por_columnas(df_part)
            
            # Calcular puntos sumando aciertos de todas las fases de juego
            puntos = len(pronosticos["ronda1"].intersection(reales_por_ronda["ronda1"])) + \
                     len(pronosticos["ronda2"].intersection(reales_por_ronda["ronda2"]))
            
            participantes_datos.append({
                "id": p, "nombre": nombre_mostrar, "iniciales": obtener_iniciales(nombre_mostrar),
                "pronosticos": pronosticos, "puntos": puntos
            })
            
        return participantes_datos, reales_por_ronda, None
    except Exception as e:
        return [], {}, f"Error al leer el archivo: {str(e)}"

# ==============================================================================
# 3. INTERFAZ GRÁFICA: EL ÁRBOL DE LLAVES
# ==============================================================================
st.markdown('<div class="main-title">🏆 Árbol de Eliminación Directa 🏆</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Seguimiento Visual de Cruces e Iniciales de los Participantes</div>', unsafe_allow_html=True)

participantes, reales, error = procesar_datos_torneo()

if error:
    st.error(error)
elif participantes:
    
    # Creamos las pestañas para alternar entre el Árbol Visual y la Tabla de Posiciones
    tab_llave, tab_tabla = st.tabs(["🔀 Ver Árbol de la Llave", "📊 Tabla de Posiciones"])
    
    with tab_tabla:
        df_ranking = pd.DataFrame([{ "Pos": i+1, "Nombre": p["nombre"], "Avatar": f"[{p['iniciales']}]", "Aciertos": p["puntos"] } for i, p in enumerate(sorted(participantes, key=lambda x: x["puntos"], reverse=True))])
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        
    with tab_llave:
        st.info("💡 Abajo se muestran los partidos de la Ronda 1. Dentro de cada casilla verás qué iniciales `[ ]` apostaron por cada ganador en su columna G.")
        
        # Maquetamos el árbol usando columnas distribuidas de Streamlit para simular las fases
        col_ronda1, col_ronda2, col_ronda3 = st.columns([4, 4, 4])
        
        # --- COLUMNA 1: ENFRENTAMIENTOS DE PRIMERA RONDA ---
        with col_ronda1:
            st.markdown('<div class="section-title"> R1: Ganadores en Columna G</div>', unsafe_allow_html=True)
            
            for m_idx, (local, visitante) in enumerate(CRUCES_INICIALES):
                # Validar quién es el ganador oficial en RESULTADOS
                ganador_real = None
                if local.lower() in reales["ronda1"]: ganador_real = local
                elif visitante.lower() in reales["ronda1"]: ganador_real = visitante
                
                # Recolectar iniciales de participantes que eligieron a cada uno
                votos_local = [f"[{p['iniciales']}]" for p in participantes if local.lower() in p["pronosticos"]["ronda1"]]
                votos_vis = [f"[{p['iniciales']}]" for p in participantes if visitante.lower() in p["pronosticos"]["ronda1"]]
                
                # Renderizar la casilla estructurada del partido
                st.markdown(f"""
                <div class="match-box">
                    <div class="match-box-header">Partido {m_idx + 1}</div>
                    <div class="team-row">
                        <span class="team-name {'team-winner' if ganador_real == local else ''}">{local}</span>
                        <div class="avatar-container">{" ".join(votos_local)}</div>
                    </div>
                    <div class="team-row">
                        <span class="team-name {'team-winner' if ganador_real == visitante else ''}">{visitante}</span>
                        <div class="avatar-container">{" ".join(votos_vis)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        # --- COLUMNA 2: SIGUIENTE RONDA (OCTAVOS SIMULADOS DESDE COLUMNA I) ---
        with col_ronda2:
            st.markdown('<div class="section-title"> R2: Pronósticos de Avance</div>', unsafe_allow_html=True)
            st.caption("Muestra a quiénes hicieron avanzar en las siguientes columnas de sus árboles:")
            
            # Agrupamos los equipos que van apareciendo en los pronósticos de la ronda 2
            todos_r2 = set()
            for p in participantes: todos_r2.update(p["pronosticos"]["ronda2"])
            
            for equipo_r2 in sorted(list(todos_r2)):
                votos_r2 = [f"[{p['iniciales']}]" for p in participantes if equipo_r2 in p["pronosticos"]["ronda2"]]
                es_real_r2 = " (✔️ Confirmado)" if equipo_r2 in reales["ronda2"] else ""
                
                st.markdown(f"""
                <div class="match-box" style="border-left: 4px solid #2563EB;">
                    <div class="team-name" style="color: #1E3A8A;">{equipo_r2.title()}<span style="color:#10B981;">{es_real_r2}</span></div>
                    <div class="avatar-container" style="margin-top:5px;">{" ".join(votos_r2)}</div>
                </div>
                """, unsafe_allow_html=True)

        # --- COLUMNA 3: FASE FINAL / CUARTOS ---
        with col_ronda3:
            st.markdown('<div class="section-title"> R3: Camino a la Final</div>', unsafe_allow_html=True)
            
            todos_r3 = set()
            for p in participantes: todos_r3.update(p["pronosticos"]["ronda3"])
            
            for equipo_r3 in sorted(list(todos_r3)):
                votos_r3 = [f"[{p['iniciales']}]" for p in participantes if equipo_r3 in p["pronosticos"]["ronda3"]]
                
                st.markdown(f"""
                <div class="match-box" style="border-left: 4px solid #D97706; background-color: #FFFBEB;">
                    <div class="team-name" style="color: #B45309;">{equipo_r3.title()}</div>
                    <div class="avatar-container">{" ".join(votos_r3)}</div>
                </div>
                """, unsafe_allow_html=True)
