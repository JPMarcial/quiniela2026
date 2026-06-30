import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="Quiniela en Vivo", page_icon="⚽", layout="wide")
st.title("🏆 Control de Aciertos en Tiempo Real - Quiniela 2026")

# ==============================================================================
# 1. ENLACE DE TU GOOGLE DRIVE Y CONFIGURACIÓN DE CONEXIÓN
# ==============================================================================
# ID extraído de tu enlace compartido
SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"

# Lista exacta de los nombres de tus pestañas actuales
PESTAÑAS = [
    "BASE", "HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", 
    "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", 
    "JMG", "JV", "CAAM", "DSR", "SLO"
]

@st.cache_data(ttl=300)  # Guarda en caché por 5 minutos para que cargue rápido sin saturar la red
def cargar_pestaña_desde_drive(spreadsheet_id, nombre_hoja):
    """
    Se conecta al enlace de Google Drive y descarga la pestaña seleccionada en vivo.
    """
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja}"
    try:
        respuesta = requests.get(url)
        if respuesta.status_code == 200:
            # Leemos el archivo en crudo como texto plano
            df_raw = pd.read_csv(io.StringIO(respuesta.text), header=None, dtype=str)
            return df_raw
        else:
            return None
    except Exception:
        return None

def procesar_bloque_resumen(df_raw):
    """
    Busca la palabra '16vos' en el archivo en crudo y extrae las columnas limpias.
    """
    if df_raw is None or df_raw.empty:
        return None
        
    try:
        inicio_tabla = None
        # Recorremos para encontrar la celda que dice '16vos'
        for idx, row in df_raw.iterrows():
            if row.astype(str).str.contains('16vos', case=False, na=False).any():
                inicio_tabla = idx
                break
                
        if inicio_tabla is None:
            return None
            
        # Cortamos el DataFrame desde donde encontramos la fila de cabeceras
        df_resumen = df_raw.iloc[inicio_tabla:].copy()
        df_resumen.columns = df_resumen.iloc[0]  # Asignamos cabeceras ("16vos", "8vos", etc.)
        df_resumen = df_resumen[1:]              # Quitamos la fila repetida de cabeceras
        
        # Forzar nombres de columnas limpiando posibles nulos o espacios
        df_resumen.columns = [str(c).strip().lower() if pd.notna(c) else "" for c in df_resumen.columns]
        
        # Columnas mapeadas exactamente a lo que me explicaste:
        # B=16vos, D=8vos, F=4tos, H=3er lugar, J=final, L=1, M=2, N=3
        mapeo_columnas = {
            "16vos": "16vos", "8vos": "8vos", "4tos": "4tos", 
            "3er lugar": "3er lugar", "final": "final", 
            "1": "1er Lugar", "2": "2do Lugar", "3": "3er Lugar"
        }
        
        # Filtramos solo las columnas que nos interesan y renombramos de forma elegante
        columnas_existentes = [c for c in mapeo_columnas.keys() if c in df_resumen.columns]
        df_final = df_resumen[columnas_existentes].copy()
        df_final = df_final.rename(columns=mapeo_columnas)
        
        # Quitamos filas donde todas las celdas estén vacías
        df_final = df_final.dropna(how="all").reset_index(drop=True)
        return df_final
    except Exception:
        return None

# ==============================================================================
# 2. PROCESAMIENTO EN VIVO DE LOS DATOS
# ==============================================================================
with st.spinner("🔄 Conectando con Google Drive y leyendo las pestañas de resultados..."):
    # Cargamos primero la pestaña BASE
    df_base_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, "BASE")
    df_base = procesar_bloque_resumen(df_base_raw)

# Validamos que la base esté lista
if df_base is None or df_base.empty:
    st.error("⚠️ No se pudo extraer la tabla de control de la pestaña 'BASE'. Asegúrate de que contenga el texto '16vos' en la fila 54.")
else:
    st.success("✅ Conectado exitosamente al Google Sheet en la nube.")
    
    # Filtrar la lista de participantes quitando la palabra "BASE"
    participantes = [p for p in PESTAÑAS if p != "BASE"]
    
    # Selector visual en Streamlit para auditar a los jugadores
    jugador_seleccionado = st.selectbox("👤 Selecciona un participante para auditar aciertos:", participantes)
    
    if jugador_seleccionado:
        # Traer y procesar los datos de ese jugador en vivo
        df_jugador_raw = cargar_pestaña_desde_drive(SPREADSHEET_ID, jugador_seleccionado)
        df_jugador = procesar_bloque_resumen(df_jugador_raw)
        
        if df_jugador is None or df_jugador.empty:
            st.warning(f"⚠️ No se encontró el formato de resumen en la pestaña de {jugador_seleccionado}.")
        else:
            # Presentar la información lado a lado de manera elegante
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"📋 **Predicciones de {jugador_seleccionado}:**")
                st.dataframe(df_jugador, use_container_width=True)
                
            with col2:
                st.markdown("🎯 **Resultados Reales Oficiales (BASE):**")
                st.dataframe(df_base, use_container_width=True)
                
            # --- CONTEO DIRECTO SEGURO ---
            st.markdown("### 📊 Desglose de Coincidencias Realizadas")
            
            fases_a_comparar = ["16vos", "8vos", "4tos", "3er lugar", "final"]
            puntos_totales = 0
            
            for fase in fases_a_comparar:
                if fase in df_jugador.columns and fase in df_base.columns:
                    # Formateo defensivo para evitar fallos de escritura (eliminar espacios y pasar a mayúsculas)
                    set_jugador = set(df_jugador[fase].dropna().astype(str).str.strip().str.upper())
                    set_base = set(df_base[fase].dropna().astype(str).str.strip().str.upper())
                    
                    # Remover valores vacíos del set si los hubiera
                    set_jugador.discard("")
                    set_base.discard("")
                    
                    coincidencias = set_jugador.intersection(set_base)
                    aciertos = len(coincidencias)
                    puntos_totales += aciertos
                    
                    if aciertos > 0:
                        st.write(f"🔹 **{fase}**: {aciertos} acierto(s) 👉 *{', '.join(coincidencias)}*")
                    else:
                        st.write(f"🔹 **{fase}**: 0 aciertos.")
            
            st.metric(label="🏆 Total Aciertos Acumulados", value=puntos_totales)
