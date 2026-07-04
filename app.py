import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Quiniela Fase Final", page_icon="⚽", layout="wide")

# Estilos CSS con contenedores Flexbox para alineación vertical perfecta
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    
    .bracket-column-flex {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 680px; 
        padding: 10px 0;
    }
    
    .bracket-phase { font-weight: bold; text-align: center; color: #475569; background: #e2e8f0; padding: 6px; border-radius: 6px; margin-bottom: 5px; font-size: 13px; }
    .bracket-match { background: #ffffff; padding: 8px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin: 5px 0; }
    .bracket-team { font-size: 12px; font-weight: 600; color: #1e293b; padding: 2px 4px; display: flex; justify-content: space-between; }
    .bracket-team.winner { color: #10b981; background-color: #f0fdf4; border-radius: 4px; }
    .bracket-team.loser { color: #94a3b8; }
    .bracket-score { font-weight: bold; color: #0f172a; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Quiniela - Fase Final 2026")

# ==============================================================================
# 1. DETECCIÓN AUTOMÁTICA DE FECHA (ZONA HORARIA MÉXICO SIN PYTZ)
# ==============================================================================
fecha_actual_mx = datetime.utcnow() - timedelta(hours=6)
fecha_formateada = fecha_actual_mx.strftime("%d/%m/%Y") 
fecha_actual_dt = datetime.strptime(fecha_formateada, "%d/%m/%Y")

# ==============================================================================
# CALENDARIO COMPLETO CON IDENTIFICADORES DE PARTIDO ASOCIADOS A SU RONDA
# ==============================================================================
CALENDARIO_COMPLETO = [
    # --- 16vos LADO IZQUIERDO ---
    {"Id": "P1", "Fecha": "29/06/2026", "Rival 1": "ALEMANIA", "Rival 2": "PARAGUAY", "Texto": "Alemania 🆚 Paraguay", "Hora": "14:00", "Keys 1": ["ALEMANIA", "GER"], "Keys 2": ["PARAGUAY", "PAR"]},
    {"Id": "P2", "Fecha": "30/06/2026", "Rival 1": "FRANCIA", "Rival 2": "SUECIA", "Texto": "Francia 🆚 Suecia", "Hora": "15:00", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["SUECIA", "SUE"]},
    {"Id": "P3", "Fecha": "28/06/2026", "Rival 1": "SUDÁFRICA", "Rival 2": "CANADÁ", "Texto": "Sudáfrica 🆚 Canadá", "Hora": "13:00", "Keys 1": ["SUDAFRICA", "SUDÁFRICA", "RSA"], "Keys 2": ["CANADA", "CANADÁ", "CAN"]},
    {"Id": "P4", "Fecha": "29/06/2026", "Rival 1": "PAÍSES BAJOS", "Rival 2": "MARRUECOS", "Texto": "Países Bajos 🆚 Marruecos", "Hora": "20:00", "Keys 1": ["PAISES BAJOS", "PAÍSES BAJOS", "NED", "HOLANDA"], "Keys 2": ["MARRUECOS", "MAR"]},
    {"Id": "P5", "Fecha": "02/07/2026", "Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia", "Hora": "17:00", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["CROACIA", "CRO"]},
    {"Id": "P6", "Fecha": "02/07/2026", "Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria", "Hora": "13:00", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["AUSTRIA", "AUT"]},
    {"Id": "P7", "Fecha": "01/07/2026", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA", "Texto": "Estados Unidos 🆚 Bosnia", "Hora": "18:00", "Keys 1": ["ESTADOS UNIDOS", "USA", "EEUU"], "Keys 2": ["BOSNIA", "HERZEGOVINA", "BOSNIA-HERZ"]},
    {"Id": "P8", "Fecha": "01/07/2026", "Rival 1": "BÉLGICA", "Rival 2": "SENEGAL", "Texto": "Bélgica 🆚 Senegal", "Hora": "14:00", "Keys 1": ["BELGICA", "BÉLGICA", "BEL"], "Keys 2": ["SENEGAL", "SEN"]},
    
    # --- 16vos LADO DERECHO ---
    {"Id": "P9", "Fecha": "29/06/2026", "Rival 1": "BRASIL", "Rival 2": "JAPÓN", "Texto": "Brasil 🆚 Japón", "Hora": "11:00", "Keys 1": ["BRASIL", "BRA"], "Keys 2": ["JAPON", "JAPÓN", "JPN"]},
    {"Id": "P10", "Fecha": "30/06/2026", "Rival 1": "COSTA DE MARFIL", "Rival 2": "NORUEGA", "Texto": "Costa de Marfil 🆚 Noruega", "Hora": "11:00", "Keys 1": ["COSTA DE MARFIL", "MARFIL", "CIV"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Id": "P11", "Fecha": "30/06/2026", "Rival 1": "MÉXICO", "Rival 2": "ECUADOR", "Texto": "México 🆚 Ecuador", "Hora": "19:00", "Keys 1": ["MEXICO", "MÉXICO", "MEX"], "Keys 2": ["ECUADOR", "ECU"]},
    {"Id": "P12", "Fecha": "01/07/2026", "Rival 1": "INGLATERRA", "Rival 2": "RD CONGO", "Texto": "Inglaterra 🆚 RD Congo", "Hora": "10:00", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["CONGO", "RD CONGO", "RDC"]},
    {"Id": "P13", "Fecha": "03/07/2026", "Rival 1": "ARGENTINA", "Rival 2": "CABO VERDE", "Texto": "Argentina 🆚 Cabo Verde", "Hora": "16:00", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["CABO VERDE", "CPV"]},
    {"Id": "P14", "Fecha": "03/07/2026", "Rival 1": "AUSTRALIA", "Rival 2": "EGIPTO", "Texto": "Australia 🆚 Egipto", "Hora": "12:00", "Keys 1": ["AUSTRALIA", "AUS"], "Keys 2": ["EGIPTO", "EGY"]},
    {"Id": "P15", "Fecha": "02/07/2026", "Rival 1": "SUIZA", "Rival 2": "ARGELIA", "Texto": "Suiza 🆚 Argelia", "Hora": "21:00", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["ARGELIA", "ALG"]},
    {"Id": "P16", "Fecha": "03/07/2026", "Rival 1": "COLOMBIA", "Rival 2": "GHANA", "Texto": "Colombia 🆚 Ghana", "Hora": "19:30", "Keys 1": ["COLOMBIA", "COL"], "Keys 2": ["GHANA", "GHA"]},

    # --- OCTAVOS DE FINAL ---
    {"Id": "P17", "Fecha": "04/07/2026", "Rival 1": "CANADÁ", "Rival 2": "MARRUECOS", "Texto": "Canadá 🆚 Marruecos", "Hora": "11:00", "Keys 1": ["CANADA", "CANADÁ", "CAN"], "Keys 2": ["MARRUECOS", "MAR"]},
    {"Id": "P18", "Fecha": "04/07/2026", "Rival 1": "PARAGUAY", "Rival 2": "FRANCIA", "Texto": "Paraguay 🆚 Francia", "Hora": "15:00", "Keys 1": ["PARAGUAY", "PAR"], "Keys 2": ["FRANCIA", "FRA"]},
    {"Id": "P19", "Fecha": "05/07/2026", "Rival 1": "BRASIL", "Rival 2": "NORUEGA", "Texto": "Brasil 🆚 Noruega", "Hora": "14:00", "Keys 1": ["BRASIL", "BRA"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Id": "P20", "Fecha": "05/07/2026", "Rival 1": "MÉXICO", "Rival 2": "INGLATERRA", "Texto": "México 🆚 Inglaterra", "Hora": "18:00", "Keys 1": ["MEXICO", "MÉXICO", "MEX"], "Keys 2": ["INGLATERRA", "ENG"]},
    {"Id": "P21", "Fecha": "06/07/2026", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BÉLGICA", "Texto": "Estados Unidos 🆚 Bélgica", "Hora": "18:00", "Keys 1": ["ESTADOS UNIDOS", "USA", "EEUU"], "Keys 2": ["BELGICA", "BÉLGICA", "BEL"]},
    {"Id": "P22", "Fecha": "06/07/2026", "Rival 1": "PORTUGAL", "Rival 2": "ESPAÑA", "Texto": "Portugal 🆚 España", "Hora": "13:00", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["ESPAÑA", "ESP"]},
    {"Id": "P23", "Fecha": "07/07/2026", "Rival 1": "SUIZA", "Rival 2": "COLOMBIA", "Texto": "Suiza 🆚 Colombia", "Hora": "14:00", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["COLOMBIA", "COL"]},
    {"Id": "P24", "Fecha": "07/07/2026", "Rival 1": "ARGENTINA", "Rival 2": "EGIPTO", "Texto": "Argentina 🆚 Egipto", "Hora": "10:00", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["EGIPTO", "EGY"]}
]

SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"
ID_PESTAÑAS = ["HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", "JMG", "JV", "CAAM", "DSR", "SLO", "JGLM"]

# ==============================================================================
# 2. FUNCIONES DE PROCESAMIENTO
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

def limpiar_texto(s):
    s = str(s).strip().upper()
    s = re.sub(r'[ÁÉÍÓÚ]', lambda m: {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U'}[m.group(0)], s)
    return s

def extraer_columna_fija(df_raw, col_indice):
    if df_raw is None or df_raw.shape[0] < 55 or df_raw.shape[1] <= col_indice:
        return set()
    try:
        # CORRECCIÓN: Cambiamos de 53 a 54 para ignorar el encabezado de la fila 54 de Excel
        bloque = df_raw.iloc[54:75, col_indice].dropna().astype(str).str.strip()
        valores_limpios = set(bloque.apply(limpiar_texto))
        
        valores_filtrados = {
            v for v in valores_limpios 
            if v not in {"", "0", "NAN", "NINGUNO", "NONE", "NO", "16VOS", "8VOS", "4TOS", "SEMIS", "FINAL"} and len(v) > 2
        }
        return valores_filtrados
    except Exception:
        return set()

@st.cache_data(ttl=60)
def cargar_y_procesar_todo_el_torneo(spreadsheet_id, pestañas_jugadores, fecha_consulta):
    url = f"https://drive.google.com/uc?export=download&id={spreadsheet_id}"
    datos_ranking = []
    pronosticos_fecha_lista = []
    desglose_puntos_lista = []
    
    partidos_fecha = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_consulta]
    
    bracket_data = {}
    for p in CALENDARIO_COMPLETO:
        bracket_data[p["Id"]] = {"Rival 1": p["Rival 1"], "Rival 2": p["Rival 2"], "Goles 1": "-", "Goles 2": "-", "Ganador": "Por Definir"}
    
    try:
        respuesta = requests.get(url, timeout=15)
        if respuesta.status_code != 200: return None, None, partidos_fecha, bracket_data, pd.DataFrame()
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content), engine='openpyxl')
        nombres_pestañas = excel_file.sheet_names
        
        # Cargar matriz de la hoja BASE para calificar aciertos globales (Columna B)
        if "BASE" in nombres_pestañas:
            df_base_raw = excel_file.parse("BASE", header=None, dtype=str)
            set_base_16vos = extraer_columna_fija(df_base_raw, 1) # Columna B
        else:
            set_base_16vos = set()

        lista_base_ordenada = sorted(list(set_base_16vos))

        # Lectura de marcadores reales en el CALENDARIO excel
        pestaña_cal = [n for n in nombres_pestañas if "CALENDARIO" in n.upper()]
        if pestaña_cal:
            df_cal_excel = excel_file.parse(pestaña_cal[0], header=None, dtype=str)
            for p in CALENDARIO_COMPLETO:
                fila_idx = None
                for idx, row in df_cal_excel.iterrows():
                    fila_str = " ".join(row.astype(str).fillna("").tolist()).upper()
                    if re.sub(r'[^\w\s]', '', p["Rival 1"]).strip().upper() in fila_str and re.sub(r'[^\w\s]', '', p["Rival 2"]).strip().upper() in fila_str:
                        fila_idx = idx
                        break
                if fila_idx is not None and df_cal_excel.shape[1] >= 4:
                    marcador_crudo = str(df_cal_excel.iloc[fila_idx, 3]).strip()
                    if pd.notna(marcador_crudo) and marcador_crudo != "" and re.search(r'\d', marcador_crudo):
                        goles = [int(g) for g in re.findall(r'\d+', marcador_crudo)]
                        if len(goles) >= 2:
                            bracket_data[p["Id"]]["Goles 1"] = str(goles[0])
                            bracket_data[p["Id"]]["Goles 2"] = str(goles[1])
                            if "HEX" in marcador_crudo.upper() or "PEN" in marcador_crudo.upper() and len(goles) >= 4:
                                bracket_data[p["Id"]]["Goles 1"] += f" ({goles[2]})"
                                bracket_data[p["Id"]]["Goles 2"] += f" ({goles[3]})"
                                bracket_data[p["Id"]]["Ganador"] = p["Rival 1"] if goles[2] > goles[3] else p["Rival 2"]
                            else:
                                if goles[0] > goles[1]: bracket_data[p["Id"]]["Ganador"] = p["Rival 1"]
                                elif goles[1] > goles[0]: bracket_data[p["Id"]]["Ganador"] = p["Rival 2"]
        
        for p in partidos_fecha:
            id_p = p["Id"]
            if bracket_data[id_p]["Goles 1"] != "-":
                p["Resultado"] = f"{bracket_data[id_p]['Goles 1']} - {bracket_data[id_p]['Goles 2']}"
                p["Ganador"] = bracket_data[id_p]["Ganador"]

        # Procesar elecciones individuales
        for pestaña in pestañas_jugadores:
            df_jugador_raw = None; nombre_real = pestaña
            fases_jugador = {"16vos": set(), "8vos": set(), "4tos": set(), "3er": set(), "Final": set()}
            
            if pestaña in nombres_pestañas:
                df_jugador_raw = excel_file.parse(pestaña, header=None, dtype=str)
                nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
                
                fases_jugador["16vos"] = extraer_columna_fija(df_jugador_raw, 1)  # Columna B

            elecciones_fecha = {"Participante": nombre_real}
            auditoria_puntos = {"Participante": nombre_real}
            
            if df_jugador_raw is not None:
                interseccion_real = fases_jugador["16vos"].intersection(set_base_16vos)
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": len(interseccion_real)})
                
                # Rellenar matriz de desglose
                for equipo_base in lista_base_ordenada:
                    if equipo_base in fases_jugador["16vos"]:
                        auditoria_puntos[equipo_base] = "✅ Sí"
                    else:
                        auditoria_puntos[equipo_base] = "❌ No"
                
                for p in partidos_fecha:
                    num_partido = int(p["Id"].replace("P", ""))
                    set_busqueda = fases_jugador["16vos"] if num_partido <= 16 else fases_jugador["8vos"]
                    
                    encontrado = "Ninguno"
                    for pronostico in list(set_busqueda):
                        if any(k in pronostico for k in p["Keys 1"]): 
                            encontrado = p["Rival 1"].title()
                            break
                        elif any(k in pronostico for k in p["Keys 2"]): 
                            encontrado = p["Rival 2"].title()
                            break
                    
                    if p.get("Ganador") and p["Ganador"] != "Por Definir":
                        elecciones_fecha[p["Texto"]] = f"✅ {encontrado}" if limpiar_texto(p["Ganador"]) == limpiar_texto(encontrado) else f"• {encontrado}"
                    else: 
                        elecciones_fecha[p["Texto"]] = encontrado
            else:
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0})
                for equipo_base in lista_base_ordenada:
                    auditoria_puntos[equipo_base] = "❌ No"
                for p in partidos_fecha: elecciones_fecha[p["Texto"]] = "Sin Datos"
                
            desglose_puntos_lista.append(auditoria_puntos)
            if partidos_fecha: 
                pronosticos_fecha_lista.append(elecciones_fecha)
                
        df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).drop_duplicates(subset=["Participante"]).reset_index(drop=True)
        df_pronosticos_fecha = pd.DataFrame(pronosticos_fecha_lista).reset_index(drop=True) if pronosticos_fecha_lista else pd.DataFrame(columns=["Participante"])
        df_desglose = pd.DataFrame(desglose_puntos_lista).reset_index(drop=True) if desglose_puntos_lista else pd.DataFrame()
        
        if not df_desglose.empty and not df_ranking.empty:
            df_desglose = df_ranking[["Participante", "Aciertos Totales"]].merge(df_desglose, on="Participante", how="left")

        return df_ranking, df_pronosticos_fecha, partidos_fecha, bracket_data, df_desglose
    except Exception: 
        return None, None, partidos_fecha, bracket_data, pd.DataFrame()

# ==============================================================================
# INTERFAZ GRÁFICA DE STREAMLIT
# ==============================================================================
FECHAS_DISPONIBLES = sorted(list(set(p["Fecha"] for p in CALENDARIO_COMPLETO)), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
default_idx = FECHAS_DISPONIBLES.index(fecha_formateada) if fecha_formateada in FECHAS_DISPONIBLES else 0

if "BASE" not in st.session_state:
    with st.spinner("🚀 Sincronizando datos del torneo..."):
        df_ranking, _, _, BRACKET, df_desglose = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, FECHAS_DISPONIBLES[default_idx])

if df_ranking is not None:
    tab_principal, tab_desglose, tab_hoy, tab_bracket_dev = st.tabs(["📊 Clasificación", "🔍 Desglose de Aciertos", "🔮 Pronósticos por Fecha", "🛠️ Desarrollo Bracket"])

    # --- PESTAÑA PRINCIPAL ---
    with tab_principal:
        st.subheader("📅 Partidos del Día")
        PARTIDOS_DEL_DIA_LISTA = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_formateada]
        if not PARTIDOS_DEL_DIA_LISTA: 
            st.info(f"⚽ No hay partidos agendados para el día de hoy ({fecha_formateada}).")
        else:
            columnas_juegos = st.columns(len(PARTIDOS_DEL_DIA_LISTA))
            for i, partido in enumerate(PARTIDOS_DEL_DIA_LISTA):
                with columnas_juegos[i]:
                    id_p = partido["Id"]
                    g1_b = BRACKET[id_p]["Goles 1"]
                    g2_b = BRACKET[id_p]["Goles 2"]
                    
                    if g1_b != "-":
                        marcador = f"{g1_b} - {g2_b}"
                        badge_html = f'<div style="text-align: center; font-size: 26px; font-weight: 800; color: #10B981; background-color: #ECFDF5; padding: 10px; border-radius: 8px; border: 2px solid #A7F3D0; margin-bottom: 10px;">{marcador} <span style="font-size:12px; font-weight:bold; display:block; color:#059669;">FINALIZADO</span></div>'
                    else:
                        badge_html = f'<div style="text-align: center; font-size: 14px; font-weight: 700; color: #1D4ED8; background-color: #EFF6FF; padding: 6px; border-radius: 6px; margin-bottom: 10px;">⏰ {partido["Hora"]} MX</div>'
                    
                    st.markdown(f'<div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); border: 1px solid #F1F5F9;">{badge_html}<div style="font-size: 19px; font-weight: 700; color: #1E293B; text-align: center; line-height: 1.4;">{partido["Rival 1"].title()} <br><span style="color:#94A3B8; font-size:14px; font-weight:normal;">VS</span><br> {partido["Rival 2"].title()}</div></div>', unsafe_allow_html=True)
            st.write("") 
            
        st.write("---")
        st.subheader("🏅 Tabla de Posiciones General")
        max_puntos_global = int(df_ranking["Aciertos Totales"].max()) if df_ranking["Aciertos Totales"].max() > 0 else 1
        for index, row in df_ranking.iterrows():
            pts = int(row["Aciertos Totales"])
            st.markdown(f'<div style="display: flex; align-items: center; background-color: #FFFFFF; padding: 12px 18px; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #F1F5F9;"><div style="width: 50px; font-size: 16px; font-weight: 700; color: #64748B;">#{index + 1}</div><div style="flex-grow: 1; font-size: 16px; font-weight: 600; color: #334155;">{row["Participante"]}</div><div style="width: 140px; margin-right: 20px;"><div style="background-color: #E2E8F0; border-radius: 10px; height: 8px; width: 100%;"><div style="background-color: #3B82F6; height: 8px; border-radius: 10px; width: {(pts / max_puntos_global) * 100}%;"></div></div></div><div style="font-size: 16px; font-weight: 700; color: #1E293B; width: 60px; text-align: right;">{pts} pts</div></div>', unsafe_allow_html=True)

    # --- PESTAÑA: DESGLOSE DE ACIERTOS ---
    with tab_desglose:
        st.markdown("### 🔍 Tabla General de Auditoría de Puntos")
        st.write("Resultados por fase")
        
        if df_desglose.empty or len(df_desglose.columns) <= 2:
            st.warning("No hay equipos registrados en la hoja 'BASE' para desglosar todavía.")
        else:
            def estilar_tabla_aciertos(val):
                if val == "✅ Sí":
                    return 'background-color: #d1fae5; color: #065f46; font-weight: bold; text-align: center;'
                elif val == "❌ No":
                    return 'background-color: #fee2e2; color: #991b1b; text-align: center;'
                return ''
            
            df_estilado = df_desglose.style.map(estilar_tabla_aciertos, subset=df_desglose.columns[2:])
            st.dataframe(df_estilado, use_container_width=True, hide_index=True)

    # --- PESTAÑA PRONÓSTICOS ---
    with tab_hoy:
        st.markdown("### 🔮 Consulta de Pronósticos")
        sub_tabs_fechas = st.tabs([f"📅 {f}" for f in FECHAS_DISPONIBLES])
        
        for idx_f, fecha_select in enumerate(FECHAS_DISPONIBLES):
            with sub_tabs_fechas[idx_f]:
                _, df_pronosticos_fecha, partidos_fecha, _, _ = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, fecha_select)
                if not partidos_fecha or df_pronosticos_fecha.empty:
                    st.info("No hay partidos ni pronósticos registrados para esta fecha.")
                else:
                    st.caption(f"Visualizando elecciones reales según la columna correspondiente de la fase jugada el {fecha_select}")
                    st.dataframe(df_pronosticos_fecha, use_container_width=True, hide_index=True)

    # --- PESTAÑA BRACKET DESARROLLO ---
    with tab_bracket_dev:
        st.markdown("### 🏗️ Bracket del Mundial 2026")
        
        def render_match_html(match_id, data_dict):
            m = data_dict[match_id]
            r1, r2 = m["Rival 1"].title(), m["Rival 2"].title()
            g1, g2 = m.get('Goles 1', '-'), m.get('Goles 2', '-')
            c1 = "winner" if m["Ganador"] == m["Rival 1"] else ("loser" if m["Ganador"] != "Por Definir" and m["Ganador"] is not None else "")
            c2 = "winner" if m["Ganador"] == m["Rival 2"] else ("loser" if m["Ganador"] != "Por Definir" and m["Ganador"] is not None else "")
            return f"""
            <div class="b-card">
                <div class="b-team {c1}"><span>{r1}</span> <span class="score">{g1}</span></div>
                <div class="b-team {c2}"><span>{r2}</span> <span class="score">{g2}</span></div>
            </div>
            """

        def get_w(pid):
            ganador = BRACKET[pid]["Ganador"]
            return ganador.title() if ganador and ganador != "Por Definir" else f"Ganador {pid}"

        w = {f"P{i}": get_w(f"P{i}") for i in range(1, 25)}

        bracket_html = f"""
        <style>
            .b-container {{ display: grid; grid-template-columns: repeat(9, 1fr); gap: 12px; background-color: #0f172a; padding: 20px; border-radius: 12px; font-family: sans-serif; min-width: 1400px; }}
            .b-column {{ display: grid; grid-template-rows: repeat(8, 1fr); height: 850px; }}
            .b-match {{ display: flex; flex-direction: column; justify-content: center; padding: 2px 0; }}
            .b-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: white; font-size: 11px; }}
            .b-team {{ display: flex; justify-content: space-between; margin: 3px 0; }}
            .winner {{ color: #4ade80; font-weight: bold; }}
            .score {{ font-weight: bold; color: #94a3b8; }}
            .phase-title {{ text-align: center; color: #94a3b8; font-size: 13px; font-weight: bold; margin-bottom: 15px; }}
            .final-card {{ border: 2px solid #f59e0b; }}
        </style>

        <div class="b-container">
            <div class="phase-title">16vos (Izq)</div><div class="phase-title">8vos (Izq)</div><div class="phase-title">4tos (Izq)</div><div class="phase-title">Semifinal</div>
            <div class="phase-title" style="color:#f59e0b;">🏆 FINAL</div>
            <div class="phase-title">Semifinal</div><div class="phase-title">4tos (Der)</div><div class="phase-title">8vos (Der)</div><div class="phase-title">16vos (Der)</div>

            <div class="b-column">
                <div class="b-match">{render_match_html("P1", BRACKET)}</div>
                <div class="b-match">{render_match_html("P2", BRACKET)}</div>
                <div class="b-match">{render_match_html("P3", BRACKET)}</div>
                <div class="b-match">{render_match_html("P4", BRACKET)}</div>
                <div class="b-match">{render_match_html("P5", BRACKET)}</div>
                <div class="b-match">{render_match_html("P6", BRACKET)}</div>
                <div class="b-match">{render_match_html("P7", BRACKET)}</div>
                <div class="b-match">{render_match_html("P8", BRACKET)}</div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P18", BRACKET)}</div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P17", BRACKET)}</div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P22", BRACKET)}</div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P21", BRACKET)}</div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P18']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P17']}</span></div></div></div>
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P22']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P21']}</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>Ganador 4tos Izq 1</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>Ganador 4tos Izq 2</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;">
                    <div class="b-card final-card">
                        <div class="b-team" style="font-weight:700;"><span>Finalista Izquierdo</span></div>
                        <div style="height:1px; background:#f59e0b; margin:6px 0;"></div>
                        <div class="b-team" style="font-weight:700;"><span>Finalista Derecho</span></div>
                    </div>
                </div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>Ganador 4tos Der 1</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>Ganador 4tos Der 2</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P19']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P20']}</span></div></div></div>
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P23']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P24']}</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P19", BRACKET)}</div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P20", BRACKET)}</div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P23", BRACKET)}</div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P24", BRACKET)}</div>
            </div>

            <div class="b-column">
                <div class="b-match">{render_match_html("P9", BRACKET)}</div>
                <div class="b-match">{render_match_html("P10", BRACKET)}</div>
                <div class="b-match">{render_match_html("P11", BRACKET)}</div>
                <div class="b-match">{render_match_html("P12", BRACKET)}</div>
                <div class="b-match">{render_match_html("P13", BRACKET)}</div>
                <div class="b-match">{render_match_html("P14", BRACKET)}</div>
                <div class="b-match">{render_match_html("P15", BRACKET)}</div>
                <div class="b-match">{render_match_html("P16", BRACKET)}</div>
            </div>
        </div>
        """
        st.components.v1.html(bracket_html, height=900, scrolling=True)
