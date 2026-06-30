import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="Quiniela en Vivo", page_icon="⚽", layout="wide")
st.title("🏆 Control de Aciertos en Tiempo Real - Quiniela 2026")

# ==============================================================================
# 1. ENLACE DE TU GOOGLE DRIVE Y CONFIGURACIÓN DE CONEXIÓN
# ==============================================================================
SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"

# Lista completa de todas las pestañas de tus jugadores
JUGADORES = [
    "HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", 
    "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", 
    "JMG", "JV", "CAAM", "DSR", "SLO"
]

@st.cache_data(ttl=120)  # Bajamos a 2 minutos para que el ranking se actualice más rápido si cambias la BASE
def cargar_pestaña_desde_drive(spreadsheet_id, nombre_hoja):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja}"
    try:
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            return pd.read_csv(io.StringIO(respuesta.text), header=None, dtype=str)
    except Exception:
        pass
    return None

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
# 2. PROCESAMIENTO GENERAL DE DATOS (EN VIVO)
# ==============================================================================
with st.spinner("🔄 Calculando posiciones y aciertos desde Google Drive..."):
    df_base_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, "BASE")
    df_base = procesar_bloque_resumen(df_base_raw)

if df_base is None or df_base.empty:
    st.error("⚠️ No se pudo conectar correctamente con la pestaña 'BASE' en Google Drive.")
else:
    # Calculamos los puntos de cada uno para el Ranking
    datos_ranking = []
    diccionario_jugadores_df = {} # Guardamos los dfs para no volver a pedirlos en la otra pestaña
    
    for jugador in JUGADORES:
        df_jugador_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, jugador)
        df_jugador = procesar_bloque_resumen(df_jugador_raw)
        
        if df_jugador is not None:
            diccionario_jugadores_df[jugador] = df_jugador
            puntos = calcular_puntos(df_jugador, df_base)
            datos_ranking.append({"Participante": jugador, "Aciertos Totales": puntos})
        else:
            datos_ranking.append({"Participante": jugador, "Aciertos Totales": 0})
            
    # Crear DataFrame del Ranking y ordenarlo de mayor a menor
    df_ranking = pd.DataFrame(datos_ranking)
    df_ranking = df_ranking.sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
    df_ranking.index = df_ranking.index + 1 # Que empiece en posición 1, 2, 3...

    # ==============================================================================
    # 3. DISEÑO DE PESTAÑAS AL CENTRO DE LA PANTALLA
    # ==============================================================================
    # Definimos las pestañas principales en el centro de la aplicación
    tab_ranking, tab_auditoria = st.tabs(["📊 Tabla de Posiciones (Ranking)", "👤 Auditoría por Participante"])

    # --- PESTAÑA 1: RANKING (VISTA PRINCIPAL) ---
    with tab_ranking:
        st.subheader("🏅 Clasificación General")
        st.write("Posiciones calculadas en tiempo real comparando las matrices contra la pestaña **BASE**.")
        
        # Resaltar al líder con una tarjeta métrica
        if not df_ranking.empty:
            lider = df_ranking.iloc[0]["Participante"]
            max_puntos = df_ranking.iloc[0]["Aciertos Totales"]
            st.metric(label=f"🔥 Líder Actual de la Quiniela", value=f"{lider}", delta=f"{max_puntos} pts")
            
        st.dataframe(df_ranking, use_container_width=True)

    # --- PESTAÑA 2: AUDITORÍA (DETALLE DE JUGADAS) ---
    with tab_auditoria:
        st.subheader("🔍 Desglose individual de predicciones")
        
        jugador_seleccionado = st.selectbox("Selecciona un participante para revisar sus aciertos:", JUGADORES)
        
        if jugador_seleccionado:
            df_jugador = diccionario_jugadores_df.get(jugador_seleccionado)
            
            if df_jugador is None or df_jugador.empty:
                st.warning(f"⚠️ No se encontraron predicciones en formato válido para {jugador_seleccionado}.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📋 **Predicciones de {jugador_seleccionado}:**")
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
