import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="Quiniela Fase Final", page_icon="⚽", layout="wide")
st.title("⚽ Quiniela - Fase Final 2026")

# ==============================================================================
# 1. CONFIGURACIÓN DE CONEXIÓN Y JUGADORES
# ==============================================================================
SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"

# Identificadores de las pestañas en Drive
ID_PESTAÑAS = [
    "HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", 
    "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", 
    "JMG", "JV", "CAAM", "DSR", "SLO"
]

# Definición de los partidos del día de hoy y los equipos involucrados
PARTIDOS_HOY = [
    {"Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia"},
    {"Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria"},
    {"Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA-HERZ", "Texto": "Estados Unidos 🆚 Bosnia-Herz"}
]

@st.cache_data(ttl=60)
def cargar_pestaña_desde_drive(spreadsheet_id, nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja}"
    try:
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            return pd.read_csv(io.StringIO(respuesta.text), header=None, dtype=str)
    except Exception:
        pass
    return None

def obtener_nombre_real(df_raw, id_pestaña):
    """Extrae el nombre real estrictamente de la celda B1 (Fila 0, Columna 1 del CSV crudo)"""
    try:
        if df_raw is not None and df_raw.shape[0] > 0 and df_raw.shape[1] > 1:
            nombre = df_raw.iloc[0, 1]
            if pd.notna(nombre) and str(nombre).strip() != "" and str(nombre).strip() != "0":
                return str(nombre).strip()
    except Exception:
        pass
    return id_pestaña

def procesar_bloque_resumen(df_raw):
    if df_raw is None or df_raw.empty:
        return None
    try:
        inicio_tabla = None
        # Buscar la fila exacta donde se encuentra el encabezado de las fases
        for idx, row in df_raw.iterrows():
            if row.astype(str).str.contains('16vos', case=False, na=False).any():
                inicio_tabla = idx
                break
        if inicio_tabla is None:
            return None
            
        # Extraer las filas correspondientes al bloque
        df_resumen = df_raw.iloc[inicio_tabla:].copy()
        
        # Guardamos la primera fila como nombres de columna limpios
        cabeceras = [str(c).strip().lower() if pd.notna(c) else "" for c in df_resumen.iloc[0]]
        df_resumen.columns = cabeceras
        df_resumen = df_resumen[1:]
        
        # Encontrar la posición exacta de la columna '16vos' por índice para no confundir datos
        idx_16vos = [i for i, x in enumerate(cabeceras) if x == '16vos']
        if not idx_16vos:
            return None
        col_pos = idx_16vos[0]
        
        # Extraer exclusivamente esa columna por posición de índice
        df_final = pd.DataFrame()
        df_final["16vos"] = df_resumen.iloc[:, col_pos].astype(str).str.strip()
        
        # Limpiar filas vacías o nulas
        df_final = df_final[df_final["16vos"].notna() & (df_final["16vos"] != "") & (df_final["16vos"] != "nan")]
        return df_final.reset_index(drop=True)
    except Exception:
        return None

def calcular_puntos(df_jugador, df_base):
    if df_jugador is None or df_base is None:
        return 0
    puntos = 0
    if "16vos" in df_jugador.columns and "16vos" in df_base.columns:
        set_jugador = set(df_jugador["16vos"].dropna().astype(str).str.strip().str.upper())
        set_base = set(df_base["16vos"].dropna().astype(str).str.strip().str.upper())
        set_jugador.discard("")
        set_base.discard("")
        puntos += len(set_jugador.intersection(set_base))
    return puntos

# ==============================================================================
# 2. PROCESAMIENTO Y CARGA DE DATOS EN VIVO
# ==============================================================================
with st.spinner("🔄 Cargando y procesando datos desde Google Drive..."):
    df_base_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, "BASE")
    df_base = procesar_bloque_resumen(df_base_raw)

if df_base is None or df_base.empty:
    st.error("⚠️ No se pudo conectar correctamente con la pestaña 'BASE' en Google Drive.")
else:
    datos_ranking = []
    mapeo_nombres_df = {}  
    pronosticos_hoy_lista = []
    
    for pestaña in ID_PESTAÑAS:
        df_jugador_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, pestaña)
        nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
        df_jugador = procesar_bloque_resumen(df_jugador_raw)
        
        elecciones_hoy = {"Participante": nombre_real}
        
        if df_jugador is not None:
            mapeo_nombres_df[nombre_real] = df_jugador
            puntos = calcular_puntos(df_jugador, df_base)
            datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": puntos})
            
            # Extraer los pronósticos específicos del día evaluando la columna limpia
            lista_pronosticos = df_jugador["16vos"].dropna().astype(str).str.strip().str.upper().tolist()
            
            for p in PARTIDOS_HOY:
                r1 = p["Rival 1"]
                r2 = p["Rival 2"]
                if r1 in lista_pronosticos:
                    elecciones_hoy[p["Texto"]] = r1.title()
                elif r2 in lista_pronosticos:
                    elecciones_hoy[p["Texto"]] = r2.title()
                else:
                    elecciones_hoy[p["Texto"]] = "Ninguno"
        else:
            datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0})
            for p in PARTIDOS_HOY:
                elecciones_hoy[p["Texto"]] = "Sin Datos"
                
        pronosticos_hoy_lista.append(elecciones_hoy)
            
    # Estructurar tablas generales
    df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
    df_ranking.index = df_ranking.index + 1
    
    df_pronosticos_hoy = pd.DataFrame(pronosticos_hoy_lista).reset_index(drop=True)

    # ==============================================================================
    # 3. INTERFAZ GRÁFICA CENTRALIZADA (TABS)
    # ==============================================================================
    tab_principal, tab_hoy, tab_participantes = st.tabs([
        "📊 Clasificación Principal", 
        "🔮 Pronósticos del Día", 
        "👤 Participantes"
    ])

    # --- PESTAÑA 1: CALENDARIO Y RANKING JUNTOS ---
    with tab_principal:
        st.subheader("📅 Partidos del Día - 16vos de Final")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("""
            <div style="background-color: #FFFFFF; padding: 12px; border-left: 4px solid #3B82F6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 10px;">
                <span style="font-size: 11px; font-weight: bold; color: #94A3B8; text-transform: uppercase;">30/06 - NY/NJ</span><br>
                <span style="font-size: 14px; font-weight: 600; color: #334155;">Portugal 🆚 Croacia</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div style="background-color: #FFFFFF; padding: 12px; border-left: 4px solid #3B82F6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 10px;">
                <span style="font-size: 11px; font-weight: bold; color: #94A3B8; text-transform: uppercase;">30/06 - Dallas</span><br>
                <span style="font-size: 14px; font-weight: 600; color: #334155;">España 🆚 Austria</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_m2:
            st.markdown("""
            <div style="background-color: #FFFFFF; padding: 12px; border-left: 4px solid #3B82F6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 10px;">
                <span style="font-size: 11px; font-weight: bold; color: #94A3B8; text-transform: uppercase;">30/06 - CDMX</span><br>
                <span style="font-size: 14px; font-weight: 600; color: #334155;">Estados Unidos 🆚 Bosnia-Herz</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div style="background-color: #FFFFFF; padding: 12px; border-left: 4px solid #10B981; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 10px;">
                <span style="font-size: 11px; font-weight: bold; color: #10B981; text-transform: uppercase;">01/07 - Mañana</span><br>
                <span style="font-size: 14px; font-weight: 600; color: #334155;">Bélgica 🆚 Senegal</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("---")
        
        st.subheader("🏅 Clasificación General")
        st.write("Posiciones calculadas de acuerdo a los pronosticos individuales.")
        
        if not df_ranking.empty:
            max_puntos_actual = df_ranking.iloc[0]["Aciertos Totales"]
            empates_primer_lugar = df_ranking[df_ranking["Aciertos Totales"] == max_puntos_actual]
            if len(empates_primer_lugar) <= 2:
                nombres_lideres = " y ".join(empates_primer_lugar["Participante"].tolist())
                st.metric(label="🔥 Líder(es) de la Quiniela", value=nombres_lideres, delta=f"{max_puntos_actual} pts")
                
        st.dataframe(df_ranking, use_container_width=True)

    # --- PESTAÑA 2: PRONÓSTICOS DEL DIA ---
    with tab_hoy:
        st.subheader("🔮 ¿Qué eligió cada participante para hoy?")
        st.write("Visualiza de un vistazo la selección a ganar de cada persona para los juegos de esta fecha.")
        st.dataframe(df_pronosticos_hoy, use_container_width=True, hide_index=True)

    # --- PESTAÑA 3: VISOR DE PARTICIPANTES ---
    with tab_participantes:
        st.subheader("🔍 Desglose individual de predicciones")
        lista_nombres_reales = sorted(list(mapeo_nombres_df.keys()))
        nombre_seleccionado = st.selectbox("Selecciona un participante para revisar sus aciertos:", lista_nombres_reales)
        
        if nombre_seleccionado:
            df_jugador = mapeo_nombres_df.get(nombre_seleccionado)
            if df_jugador is None or df_jugador.empty:
                st.warning(f"⚠️ No se encontraron predicciones válidas para {nombre_seleccionado}.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📋 **Predicciones de {nombre_seleccionado}:**")
                    st.dataframe(df_jugador, use_container_width=True)
                with col2:
                    st.markdown("🎯 **Resultados Reales Oficiales (BASE):**")
                    st.dataframe(df_base, use_container_width=True)
                    
                st.markdown("### 📊 Coincidencias Detectadas")
                if "16vos" in df_jugador.columns and "16vos" in df_base.columns:
                    set_jugador = set(df_jugador["16vos"].dropna().astype(str).str.strip().str.upper())
                    set_base = set(df_base["16vos"].dropna().astype(str).str.strip().str.upper())
                    set_jugador.discard("")
                    set_base.discard("")
                    
                    coincidencias = set_jugador.intersection(set_base)
                    aciertos = len(coincidencias)
                    
                    if aciertos > 0:
                        st.success(f"🔹 **16vos de Final**: {aciertos} aciertos correctos obtenidos.")
                        st.write(f"👉 *{', '.join(sorted(coincidencias))}*")
                    else:
                        st.write("🔹 **16vos de Final**: 0 aciertos por el momento.")
