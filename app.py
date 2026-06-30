import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="Quiniela en Vivo", page_icon="⚽", layout="wide")
st.title("🏆 Control de Aciertos en Tiempo Real - Quiniela 2026")

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

@st.cache_data(ttl=120)
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
    """Extrae el nombre real de la celda B1 (Fila 0, Columna 1)"""
    try:
        if df_raw is not None and df_raw.shape[0] > 0 and df_raw.shape[1] > 1:
            nombre = df_raw.iloc[0, 1]
            if pd.notna(nombre) and str(nombre).strip() != "":
                return str(nombre).strip()
    except Exception:
        pass
    return id_pestaña

def procesar_bloque_resumen(df_raw):
    if df_raw is None or df_raw.empty:
        return None
    try:
        inicio_tabla = None
        for idx, row in df_raw.iterrows():
            if row.astype(str).str.contains('16vos', case=False, na=False).any():
                inicio_tabla = idx
                break
        if inicio_tabla is None:
            return None
            
        df_resumen = df_raw.iloc[inicio_tabla:].copy()
        df_resumen.columns = df_resumen.iloc[0]
        df_resumen = df_resumen[1:]
        df_resumen.columns = [str(c).strip().lower() if pd.notna(c) else "" for c in df_resumen.columns]
        
        mapeo_columnas = {
            "16vos": "16vos", "8vos": "8vos", "4tos": "4tos", 
            "3er lugar": "3er lugar", "final": "final"
        }
        
        columnas_existentes = [c for c in mapeo_columnas.keys() if c in df_resumen.columns]
        df_final = df_resumen[columnas_existentes].copy()
        df_final = df_final.rename(columns=mapeo_columnas)
        df_final = df_final.dropna(how="all").reset_index(drop=True)
        return df_final
    except Exception:
        return None

def calcular_puntos(df_jugador, df_base):
    if df_jugador is None or df_base is None:
        return 0
    puntos = 0
    fases = ["16vos", "8vos", "4tos", "3er lugar", "final"]
    for fase in fases:
        if fase in df_jugador.columns and fase in df_base.columns:
            set_jugador = set(df_jugador[fase].dropna().astype(str).str.strip().str.upper())
            set_base = set(df_base[fase].dropna().astype(str).str.strip().str.upper())
            set_jugador.discard("")
            set_base.discard("")
            puntos += len(set_jugador.intersection(set_base))
    return puntos

# ==============================================================================
# 2. PROCESAMIENTO EN VIVO
# ==============================================================================
with st.spinner("🔄 Procesando datos y nombres desde Google Drive..."):
    df_base_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, "BASE")
    df_base = procesar_bloque_resumen(df_base_raw)

if df_base is None or df_base.empty:
    st.error("⚠️ No se pudo conectar correctamente con la pestaña 'BASE' en Google Drive.")
else:
    datos_ranking = []
    mapeo_nombres_df = {}  # Guardará { Nombre Real: df_procesado }
    mapeo_id_a_nombre = {} # Guardará { ID_Pestaña: Nombre Real }
    
    for pestaña in ID_PESTAÑAS:
        df_jugador_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, pestaña)
        nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
        df_jugador = procesar_bloque_resumen(df_jugador_raw)
        
        mapeo_id_a_nombre[pestaña] = nombre_real
        
        if df_jugador is not None:
            mapeo_nombres_df[nombre_real] = df_jugador
            puntos = calcular_puntos(df_jugador, df_base)
            datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": puntos})
        else:
            datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0})
            
    # Crear DataFrame del Ranking
    df_ranking = pd.DataFrame(datos_ranking)
    df_ranking = df_ranking.sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
    df_ranking.index = df_ranking.index + 1

    # ==============================================================================
    # 3. INTERFAZ GRÁFICA (PESTAÑAS CENTRALES)
    # ==============================================================================
    tab_ranking, tab_participantes = st.tabs(["📊 Tabla de Posiciones (Ranking)", "👤 Participantes"])

    # --- PESTAÑA 1: RANKING ---
    with tab_ranking:
        st.subheader("🏅 Clasificación General")
        st.write("Posiciones calculadas de acuerdo a los pronosticos individuales.")
        
        # Lógica inteligente de Líder: Solo si hay máximo 2 personas con el puntaje más alto
        if not df_ranking.empty:
            max_puntos_actual = df_ranking.iloc[0]["Aciertos Totales"]
            empates_primer_lugar = df_ranking[df_ranking["Aciertos Totales"] == max_puntos_actual]
            
            if len(empates_primer_lugar) <= 2:
                nombres_lideres = " y ".join(empates_primer_lugar["Participante"].tolist())
                st.metric(label="🔥 Líder(es) de la Quiniela", value=nombres_lideres, delta=f"{max_puntos_actual} pts")
            
        st.dataframe(df_ranking, use_container_width=True)

    # --- PESTAÑA 2: PARTICIPANTES ---
    with tab_participantes:
        st.subheader("🔍 Desglose individual de predicciones")
        
        # Lista ordenada de nombres reales para el selector
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
                fases_a_comparar = ["16vos", "8vos", "4tos", "3er lugar", "final"]
                
                for fase in fases_a_comparar:
                    if fase in df_jugador.columns and fase in df_base.columns:
                        set_jugador = set(df_jugador[fase].dropna().astype(str).str.strip().str.upper())
                        set_base = set(df_base[fase].dropna().astype(str).str.strip().str.upper())
                        set_jugador.discard("")
                        set_base.discard("")
                        
                        coincidencias = set_jugador.intersection(set_base)
                        aciertos = len(coincidencias)
                        
                        if aciertos > 0:
                            st.write(f"🔹 **{fase}**: {aciertos} acierto(s) 👉 *{', '.join(coincidencias)}*")
                        else:
                            st.write(f"🔹 **{fase}**: 0 aciertos.")
