import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Quiniela Fase Final", page_icon="⚽", layout="wide")
st.title("⚽ Quiniela - Fase Final 2026")

# ==============================================================================
# 1. DETECCIÓN AUTOMÁTICA DE FECHA (ZONA HORARIA MÉXICO SIN PYTZ)
# ==============================================================================
fecha_actual_mx = datetime.utcnow() - timedelta(hours=6)
fecha_formateada = fecha_actual_mx.strftime("%d/%m") 

CALENDARIO_COMPLETO = [
    {"Fecha": "30/06", "Rival 1": "COSTA DE MARFIL", "Rival 2": "NORUEGA", "Texto": "Costa de Marfil 🆚 Noruega", "Hora": "11:00 AM", "Keys 1": ["COSTA DE MARFIL", "MARFIL", "CIV"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Fecha": "30/06", "Rival 1": "FRANCIA", "Rival 2": "SUECIA", "Texto": "Francia 🆚 Suecia", "Hora": "03:00 PM", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["SUECIA", "SUE"]},
    {"Fecha": "30/06", "Rival 1": "MÉXICO", "Rival 2": "ECUADOR", "Texto": "México 🆚 Ecuador", "Hora": "07:00 PM", "Keys 1": ["MEXICO", "MÉXICO", "MEX"], "Keys 2": ["ECUADOR", "ECU"]},
    {"Fecha": "01/07", "Rival 1": "INGLATERRA", "Rival 2": "RD CONGO", "Texto": "Inglaterra 🆚 RD Congo", "Hora": "10:00 AM", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["CONGO", "RD CONGO", "RDC"]},
    {"Fecha": "01/07", "Rival 1": "BÉLGICA", "Rival 2": "SENEGAL", "Texto": "Bélgica 🆚 Senegal", "Hora": "02:00 PM", "Keys 1": ["BELGICA", "BÉLGICA", "BEL"], "Keys 2": ["SENEGAL", "SEN"]},
    {"Fecha": "01/07", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA", "Texto": "Estados Unidos 🆚 Bosnia", "Hora": "06:00 PM", "Keys 1": ["ESTADOS UNIDOS", "USA", "EEUU"], "Keys 2": ["BOSNIA", "HERZEGOVINA", "BOSNIA-HERZ"]},
    {"Fecha": "02/07", "Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria", "Hora": "01:00 PM", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["AUSTRIA", "AUT"]},
    {"Fecha": "02/07", "Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia", "Hora": "05:00 PM", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["CROACIA", "CRO"]},
    {"Fecha": "02/07", "Rival 1": "SUIZA", "Rival 2": "ARGELIA", "Texto": "Suiza 🆚 Argelia", "Hora": "09:00 PM", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["ARGELIA", "ALG"]},
    {"Fecha": "03/07", "Rival 1": "AUSTRALIA", "Rival 2": "EGIPTO", "Texto": "Australia 🆚 Egipto", "Hora": "12:00 PM", "Keys 1": ["AUSTRALIA", "AUS"], "Keys 2": ["EGIPTO", "EGY"]},
    {"Fecha": "03/07", "Rival 1": "ARGENTINA", "Rival 2": "CABO VERDE", "Texto": "Argentina 🆚 Cabo Verde", "Hora": "04:00 PM", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["CABO VERDE", "CPV"]},
    {"Fecha": "03/07", "Rival 1": "COLOMBIA", "Rival 2": "GHANA", "Texto": "Colombia 🆚 Ghana", "Hora": "07:30 PM", "Keys 1": ["COLOMBIA", "COL"], "Keys 2": ["GHANA", "GHA"]}
]

PARTIDOS_HOY = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_formateada]

SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"
ID_PESTAÑAS = [
    "HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", 
    "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", 
    "JMG", "JV", "CAAM", "DSR", "SLO"
]

# ==============================================================================
# 2. FUNCIONES DE PROCESAMIENTO AUXILIARES
# ==============================================================================
def obtener_nombre_real(df_raw, id_pestaña):
    try:
        if df_raw is not None and df_raw.shape[0] > 0 and df_raw.shape[1] > 1:
            raw_val = str(df_raw.iloc[0, 1]).strip()
            if pd.notna(raw_val) and raw_val != "" and raw_val != "0" and raw_val.lower() != "nan":
                nombre = raw_val.split('\n')[0].strip()
                palabras_a_remover = ["Alemania", "Portugal", "Croacia", "España", "Austria", "Francia", "Brasil"]
                for palabra in palabras_a_remover:
                    nombre = re.sub(rf'\s+{palabra}$', '', nombre, flags=re.IGNORECASE).strip()
                return nombre
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
        cabeceras = [str(c).strip().lower() if pd.notna(c) else "" for c in df_resumen.iloc[0]]
        df_resumen.columns = cabeceras
        df_resumen = df_resumen[1:]
        
        idx_16vos = [i for i, x in enumerate(cabeceras) if x == '16vos']
        if not idx_16vos:
            return None
        col_pos = idx_16vos[0]
        
        df_final = pd.DataFrame()
        df_final["16vos"] = df_resumen.iloc[:, col_pos].astype(str).str.strip()
        df_final = df_final[df_final["16vos"].notna() & (df_final["16vos"] != "") & (df_final["16vos"] != "nan")]
        return df_final.reset_index(drop=True)
    except Exception:
        return None

def limpiar_texto(s):
    s = str(s).strip().upper()
    s = re.sub(r'[ÁÉÍÓÚ]', lambda m: {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U'}[m.group(0)], s)
    return s

# ==============================================================================
# 3. PROCESAMIENTO COMPLETO BAJO CACHÉ (URL DE DESCARGA DE EXCEL)
# ==============================================================================
@st.cache_data(ttl=60)
def cargar_y_procesar_todo_el_torneo(spreadsheet_id, pestañas_jugadores, partidos_hoy):
    # URL de descarga directa para archivos alojados en Google Drive (Excel)
    url = f"https://drive.google.com/uc?export=download&id={spreadsheet_id}"
    
    datos_ranking = []
    pronosticos_hoy_lista = []
    
    try:
        respuesta = requests.get(url, timeout=15)
        if respuesta.status_code != 200:
            return None, None
            
        # Leemos el archivo Excel completo en memoria indexando todas las pestañas
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content), engine='openpyxl')
        nombres_pestañas = excel_file.sheet_names
        
        # 1. Cargar y procesar pestaña BASE
        if "BASE" not in nombres_pestañas:
            return None, None
        df_base_raw = excel_file.parse("BASE", header=None, dtype=str)
        df_base = procesar_bloque_resumen(df_base_raw)
        if df_base is None:
            return None, None
            
        set_base = set(df_base["16vos"].dropna().apply(limpiar_texto))
        set_base.discard("")
        
        # 2. Procesar cada jugador desde las pestañas leídas del Excel
        for pestaña in pestañas_jugadores:
            df_jugador = None
            nombre_real = pestaña
            
            if pestaña in nombres_pestañas:
                df_jugador_raw = excel_file.parse(pestaña, header=None, dtype=str)
                nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
                df_jugador = procesar_bloque_resumen(df_jugador_raw)
            
            elecciones_hoy = {"Participante": nombre_real}
            
            if df_jugador is not None and "16vos" in df_jugador.columns:
                # Calcular puntos eficientemente
                set_jugador = set(df_jugador["16vos"].dropna().apply(limpiar_texto))
                set_jugador.discard("")
                puntos = len(set_jugador.intersection(set_base))
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": puntos})
                
                # Evaluar partidos de hoy
                lista_pronosticos = list(set_jugador)
                for p in partidos_hoy:
                    encontrado = "Ninguno"
                    for pronostico in lista_pronosticos:
                        if any(k in pronostico for k in p["Keys 1"]):
                            encontrado = p["Rival 1"].title()
                            break
                        elif any(k in pronostico for k in p["Keys 2"]):
                            encontrado = p["Rival 2"].title()
                            break
                    elecciones_hoy[p["Texto"]] = encontrado
            else:
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0})
                for p in partidos_hoy:
                    elecciones_hoy[p["Texto"]] = "Sin Datos"
                    
            if partidos_hoy:
                pronosticos_hoy_lista.append(elecciones_hoy)
                
        # Estructurar DataFrames de salida
        df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
        df_ranking.index = df_ranking.index + 1
        
        df_pronosticos_hoy = pd.DataFrame(pronosticos_hoy_lista).reset_index(drop=True) if pronosticos_hoy_lista else pd.DataFrame(columns=["Participante"])
        
        return df_ranking, df_pronosticos_hoy

    except Exception as e:
        return None, None

# Ejecución de la carga de datos masiva
with st.spinner("🚀 Sincronizando archivo Excel a máxima velocidad..."):
    df_ranking, df_pronosticos_hoy = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, PARTIDOS_HOY)

if df_ranking is None:
    st.error("⚠️ Error crítico al descargar o procesar el archivo Excel. Asegúrate de haber guardado los cambios en Drive y que el archivo no esté corrupto.")
else:
    # ==============================================================================
    # 4. INTERFAZ GRÁFICA CENTRALIZADA (TABS)
    # ==============================================================================
    tab_principal, tab_hoy, tab_participantes = st.tabs([
        "📊 Clasificación Principal", 
        "🔮 Pronósticos del Día", 
        "👤 Participantes"
    ])

    # --- PESTAÑA 1: CALENDARIO DEL DÍA Y RANKING ---
    with tab_principal:
        st.subheader(f"📅 Partidos del Día ({fecha_formateada}) - 16vos de Final")
        
        if not PARTIDOS_HOY:
            st.info("⚽ No hay partidos agendados para el día de hoy.")
        else:
            columnas_juegos = st.columns(len(PARTIDOS_HOY))
            for i, partido in enumerate(PARTIDOS_HOY):
                with columnas_juegos[i]:
                    st.markdown(f"""
                    <div style="background-color: #FFFFFF; padding: 12px; border-left: 4px solid #3B82F6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <span style="font-size: 11px; font-weight: bold; color: #3B82F6; text-transform: uppercase;">⏰ {partido['Hora']} MX</span><br>
                        <span style="font-size: 15px; font-weight: 600; color: #334155;">{partido['Texto']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
        st.write("---")
        st.subheader("🏅 Clasificación General")
        
        if not df_ranking.empty:
            max_puntos_actual = df_ranking.iloc[0]["Aciertos Totales"]
            empates_primer_lugar = df_ranking[df_ranking["Aciertos Totales"] == max_puntos_actual]
            if len(empates_primer_lugar) <= 2:
                nombres_lideres = " y ".join(empates_primer_lugar["Participante"].tolist())
                st.metric(label="🔥 Líder(es) de la Quiniela", value=nombres_lideres, delta=f"{max_puntos_actual} pts")
                
        st.dataframe(df_ranking, use_container_width=True)

    # --- PESTAÑA 2: PRONÓSTICOS DEL DÍA ---
    with tab_hoy:
        st.subheader(f"🔮 ¿Qué eligió cada participante para hoy ({fecha_formateada})?")
        if not PARTIDOS_HOY:
            st.info("No hay pronósticos que mostrar porque hoy no se juegan partidos.")
        else:
            st.dataframe(df_pronosticos_hoy, use_container_width=True, hide_index=True)

    # --- PESTAÑA 3: VISOR DE PARTICIPANTES (CERRADO TEMPORALMENTE) ---
    with tab_participantes:
        st.write("")
        st.error("### 🤖 Temporalmente fuera de servicio")
        st.image("https://fonts.gstatic.com/s/e/notoemoji/latest/1f916/512.webp", width=120)
