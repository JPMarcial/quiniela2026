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
# Ajustamos con base al servidor UTC (-6 horas para obtener la hora de México)
fecha_actual_mx = datetime.utcnow() - timedelta(hours=6)
fecha_formateada = fecha_actual_mx.strftime("%d/%m") # Formato: "30/06"

# Base de datos real del calendario de 16vos
CALENDARIO_COMPLETO = [
    # 30 de Junio
    {"Fecha": "30/06", "Rival 1": "COSTA DE MARFIL", "Rival 2": "NORUEGA", "Texto": "Costa de Marfil 🆚 Noruega", "Hora": "11:00 AM", "Keys 1": ["COSTA DE MARFIL", "MARFIL", "CIV"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Fecha": "30/06", "Rival 1": "FRANCIA", "Rival 2": "SUECIA", "Texto": "Francia 🆚 Suecia", "Hora": "03:00 PM", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["SUECIA", "SUE"]},
    {"Fecha": "30/06", "Rival 1": "MÉXICO", "Rival 2": "ECUADOR", "Texto": "México 🆚 Ecuador", "Hora": "07:00 PM", "Keys 1": ["MEXICO", "MÉXICO", "MEX"], "Keys 2": ["ECUADOR", "ECU"]},
    
    # 01 de Julio
    {"Fecha": "01/07", "Rival 1": "INGLATERRA", "Rival 2": "RD CONGO", "Texto": "Inglaterra 🆚 RD Congo", "Hora": "10:00 AM", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["CONGO", "RD CONGO", "RDC"]},
    {"Fecha": "01/07", "Rival 1": "BÉLGICA", "Rival 2": "SENEGAL", "Texto": "Bélgica 🆚 Senegal", "Hora": "02:00 PM", "Keys 1": ["BELGICA", "BÉLGICA", "BEL"], "Keys 2": ["SENEGAL", "SEN"]},
    {"Fecha": "01/07", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA", "Texto": "Estados Unidos 🆚 Bosnia", "Hora": "06:00 PM", "Keys 1": ["ESTADOS UNIDOS", "USA", "EEUU"], "Keys 2": ["BOSNIA", "HERZEGOVINA", "BOSNIA-HERZ"]},
    
    # 02 de Julio
    {"Fecha": "02/07", "Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria", "Hora": "01:00 PM", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["AUSTRIA", "AUT"]},
    {"Fecha": "02/07", "Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia", "Hora": "05:00 PM", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["CROACIA", "CRO"]},
    {"Fecha": "02/07", "Rival 1": "SUIZA", "Rival 2": "ARGELIA", "Texto": "Suiza 🆚 Argelia", "Hora": "09:00 PM", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["ARGELIA", "ALG"]},
    
    # 03 de Julio
    {"Fecha": "03/07", "Rival 1": "AUSTRALIA", "Rival 2": "EGIPTO", "Texto": "Australia 🆚 Egipto", "Hora": "12:00 PM", "Keys 1": ["AUSTRALIA", "AUS"], "Keys 2": ["EGIPTO", "EGY"]},
    {"Fecha": "03/07", "Rival 1": "ARGENTINA", "Rival 2": "CABO VERDE", "Texto": "Argentina 🆚 Cabo Verde", "Hora": "04:00 PM", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["CABO VERDE", "CPV"]},
    {"Fecha": "03/07", "Rival 1": "COLOMBIA", "Rival 2": "GHANA", "Texto": "Colombia 🆚 Ghana", "Hora": "07:30 PM", "Keys 1": ["COLOMBIA", "COL"], "Keys 2": ["GHANA", "GHA"]}
]

# Filtrar dinámicamente los partidos que juegan estrictamente HOY
PARTIDOS_HOY = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_formateada]

# ==============================================================================
# 2. CONFIGURACIÓN DE CONEXIÓN Y JUGADORES
# ==============================================================================
SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"

ID_PESTAÑAS = [
    "HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", 
    "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", 
    "JMG", "JV", "CAAM", "DSR", "SLO"
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

def calcular_puntos(df_jugador, df_base):
    if df_jugador is None or df_base is None:
        return 0
    puntos = 0
    if "16vos" in df_jugador.columns and "16vos" in df_base.columns:
        # Convertir a texto limpio sin acentos para evitar fallos de coincidencia parcial
        def limpiar_texto(s):
            s = str(s).strip().upper()
            s = re.sub(r'[ÁÉÍÓÚ]', lambda m: {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U'}[m.group(0)], s)
            return s

        set_jugador = set(df_jugador["16vos"].dropna().apply(limpiar_texto))
        set_base = set(df_base["16vos"].dropna().apply(limpiar_texto))
        set_jugador.discard("")
        set_base.discard("")
        puntos += len(set_jugador.intersection(set_base))
    return puntos

# ==============================================================================
# 3. PROCESAMIENTO Y CARGA DE DATOS EN VIVO
# ==============================================================================
with st.spinner("🔄 Actualizando calendario y procesando quinielas..."):
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
            
            # Limpiar acentos y estandarizar la lista para el comparador de hoy
            def normalizar(txt):
                txt = str(txt).strip().upper()
                txt = re.sub(r'[ÁÉÍÓÚ]', lambda m: {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U'}[m.group(0)], txt)
                return txt
                
            lista_pronosticos = df_jugador["16vos"].dropna().apply(normalizar).tolist()
            
            # Evaluar los partidos programados para hoy
            for p in PARTIDOS_HOY:
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
            for p in PARTIDOS_HOY:
                elecciones_hoy[p["Texto"]] = "Sin Datos"
                
        if PARTIDOS_HOY:
            pronosticos_hoy_lista.append(elecciones_hoy)
            
    df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
    df_ranking.index = df_ranking.index + 1
    
    if pronosticos_hoy_lista:
        df_pronosticos_hoy = pd.DataFrame(pronosticos_hoy_lista).reset_index(drop=True)
    else:
        df_pronosticos_hoy = pd.DataFrame(columns=["Participante"])

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
        st.write("Posiciones calculadas de acuerdo a los pronósticos individuales.")
        
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
            st.write("Visualiza de un vistazo la selección a ganar de cada persona para los juegos de esta fecha.")
            st.dataframe(df_pronosticos_hoy, use_container_width=True, hide_index=True)

    # --- PESTAÑA 3: VISOR DE PARTICIPANTES (CERRADO TEMPORALMENTE) ---
    with tab_participantes:
        st.write("")
        st.error("### 🤖 Temporalmente fuera de servicio y un robot enojado")
        st.image("https://fonts.gstatic.com/s/e/notoemoji/latest/1f916/512.webp", width=120)
