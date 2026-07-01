import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Quiniela Fase Final", page_icon="⚽", layout="wide")

# Estilos CSS personalizados para limpiar la interfaz, mejorar fuentes y brackets
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    
    /* Estilos para el Bracket de Desarrollo */
    .bracket-phase { font-weight: bold; text-align: center; color: #475569; background: #e2e8f0; padding: 6px; border-radius: 6px; margin-bottom: 15px; font-size: 13px; }
    .bracket-match { background: #ffffff; padding: 8px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 12px; }
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

# Calendario oficial reordenado al 100% según el flujo visual de image_272bf4.jpg
CALENDARIO_COMPLETO = [
    # --- LADO IZQUIERDO: Bloque Superior (Feeds W74, W77, W73, W75) ---
    {"Id": "P1", "Fecha": "29/06/2026", "Rival 1": "ALEMANIA", "Rival 2": "PARAGUAY", "Texto": "Alemania 🆚 Paraguay", "Hora": "14:00", "Keys 1": ["ALEMANIA", "GER"], "Keys 2": ["PARAGUAY", "PAR"]},
    {"Id": "P2", "Fecha": "30/06/2026", "Rival 1": "FRANCIA", "Rival 2": "SUECIA", "Texto": "Francia 🆚 Suecia", "Hora": "15:00", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["SUECIA", "SUE"]},
    {"Id": "P3", "Fecha": "28/06/2026", "Rival 1": "SUDÁFRICA", "Rival 2": "CANADÁ", "Texto": "Sudáfrica 🆚 Canadá", "Hora": "13:00", "Keys 1": ["SUDAFRICA", "SUDÁFRICA", "RSA"], "Keys 2": ["CANADA", "CANADÁ", "CAN"]},
    {"Id": "P4", "Fecha": "29/06/2026", "Rival 1": "PAÍSES BAJOS", "Rival 2": "MARRUECOS", "Texto": "Países Bajos 🆚 Marruecos", "Hora": "20:00", "Keys 1": ["PAISES BAJOS", "PAÍSES BAJOS", "NED", "HOLANDA"], "Keys 2": ["MARRUECOS", "MAR"]},
    
    # --- LADO IZQUIERDO: Bloque Inferior (Feeds W83, W84, W81, W82) ---
    {"Id": "P5", "Fecha": "02/07/2026", "Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia", "Hora": "17:00", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["CROACIA", "CRO"]},
    {"Id": "P6", "Fecha": "02/07/2026", "Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria", "Hora": "13:00", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["AUSTRIA", "AUT"]},
    {"Id": "P7", "Fecha": "01/07/2026", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA", "Texto": "Estados Unidos 🆚 Bosnia", "Hora": "18:00", "Keys 1": ["ESTADOS UNIDOS", "USA", "EEUU"], "Keys 2": ["BOSNIA", "HERZEGOVINA", "BOSNIA-HERZ"]},
    {"Id": "P8", "Fecha": "01/07/2026", "Rival 1": "BÉLGICA", "Rival 2": "SENEGAL", "Texto": "Bélgica 🆚 Senegal", "Hora": "14:00", "Keys 1": ["BELGICA", "BÉLGICA", "BEL"], "Keys 2": ["SENEGAL", "SEN"]},
    
    # --- LADO DERECHO: Bloque Superior (Feeds W76, W78, W79, W80) ---
    {"Id": "P9", "Fecha": "29/06/2026", "Rival 1": "BRASIL", "Rival 2": "JAPÓN", "Texto": "Brasil 🆚 Japón", "Hora": "11:00", "Keys 1": ["BRASIL", "BRA"], "Keys 2": ["JAPON", "JAPÓN", "JPN"]},
    {"Id": "P10", "Fecha": "30/06/2026", "Rival 1": "COSTA DE MARFIL", "Rival 2": "NORUEGA", "Texto": "Costa de Marfil 🆚 Noruega", "Hora": "11:00", "Keys 1": ["COSTA DE MARFIL", "MARFIL", "CIV"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Id": "P11", "Fecha": "30/06/2026", "Rival 1": "MÉXICO", "Rival 2": "ECUADOR", "Texto": "México 🇲🇽 🆚 Ecuador", "Hora": "19:00", "Keys 1": ["MEXICO", "MÉXICO", "MEX"], "Keys 2": ["ECUADOR", "ECU"]},
    {"Id": "P12", "Fecha": "01/07/2026", "Rival 1": "INGLATERRA", "Rival 2": "RD CONGO", "Texto": "Inglaterra 🆚 RD Congo", "Hora": "10:00", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["CONGO", "RD CONGO", "RDC"]},
    
    # --- LADO DERECHO: Bloque Inferior (Feeds W86, W88, W85, W87) ---
    {"Id": "P13", "Fecha": "03/07/2026", "Rival 1": "ARGENTINA", "Rival 2": "CABO VERDE", "Texto": "Argentina 🆚 Cabo Verde", "Hora": "16:00", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["CABO VERDE", "CPV"]},
    {"Id": "P14", "Fecha": "03/07/2026", "Rival 1": "AUSTRALIA", "Rival 2": "EGIPTO", "Texto": "Australia 🆚 Egipto", "Hora": "12:00", "Keys 1": ["AUSTRALIA", "AUS"], "Keys 2": ["EGIPTO", "EGY"]},
    {"Id": "P15", "Fecha": "02/07/2026", "Rival 1": "SUIZA", "Rival 2": "ARGELIA", "Texto": "Suiza 🆚 Argelia", "Hora": "21:00", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["ARGELIA", "ALG"]},
    {"Id": "P16", "Fecha": "03/07/2026", "Rival 1": "COLOMBIA", "Rival 2": "GHANA", "Texto": "Colombia 🆚 Ghana", "Hora": "19:30", "Keys 1": ["COLOMBIA", "COL"], "Keys 2": ["GHANA", "GHA"]}
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
# 3. PROCESAMIENTO COMPLETO BAJO CACHÉ
# ==============================================================================
@st.cache_data(ttl=60)
def cargar_y_procesar_todo_el_torneo(spreadsheet_id, pestañas_jugadores, partidos_hoy):
    url = f"https://drive.google.com/uc?export=download&id={spreadsheet_id}"
    datos_ranking = []
    pronosticos_hoy_lista = []
    
    bracket_data = {}
    for p in CALENDARIO_COMPLETO:
        bracket_data[p["Id"]] = {
            "Rival 1": p["Rival 1"], "Rival 2": p["Rival 2"],
            "Goles 1": "-", "Goles 2": "-", "Ganador": "Por Definir"
        }
    
    try:
        respuesta = requests.get(url, timeout=15)
        if respuesta.status_code != 200:
            return None, None, partidos_hoy, bracket_data
            
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content), engine='openpyxl')
        nombres_pestañas = excel_file.sheet_names
        
        if "BASE" not in nombres_pestañas:
            return None, None, partidos_hoy, bracket_data
        df_base_raw = excel_file.parse("BASE", header=None, dtype=str)
        df_base = procesar_bloque_resumen(df_base_raw)
        if df_base is None:
            return None, None, partidos_hoy, bracket_data
            
        set_base = set(df_base["16vos"].dropna().apply(limpiar_texto))
        set_base.discard("")

        pestaña_cal = [n for n in nombres_pestañas if "CALENDARIO" in n.upper()]
        
        if pestaña_cal:
            df_cal_excel = excel_file.parse(pestaña_cal[0], header=None, dtype=str)
            
            for p in CALENDARIO_COMPLETO:
                fila_idx = None
                for idx, row in df_cal_excel.iterrows():
                    fila_str = " ".join(row.astype(str).fillna("").tolist()).upper()
                    rival1_limpio = re.sub(r'[^\w\s]', '', p["Rival 1"]).strip().upper()
                    rival2_limpio = re.sub(r'[^\w\s]', '', p["Rival 2"]).strip().upper()
                    if rival1_limpio in fila_str and rival2_limpio in fila_str:
                        fila_idx = idx
                        break
                
                if fila_idx is not None and df_cal_excel.shape[1] >= 4:
                    marcador_crudo = str(df_cal_excel.iloc[fila_idx, 3]).strip()
                    
                    if pd.notna(marcador_crudo) and marcador_crudo != "" and re.search(r'\d', marcador_crudo) and "nan" not in marcador_crudo.lower():
                        goles = [int(g) for g in re.findall(r'\d+', marcador_crudo)]
                        if len(goles) >= 2:
                            bracket_data[p["Id"]]["Goles 1"] = str(goles[0])
                            bracket_data[p["Id"]]["Goles 2"] = str(goles[1])
                            
                            if "HEX" in marcador_crudo.upper() or "PEN" in marcador_crudo.upper() and len(goles) >= 4:
                                bracket_data[p["Id"]]["Goles 1"] += f" ({goles[2]})"
                                bracket_data[p["Id"]]["Goles 2"] += f" ({goles[3]})"
                                if goles[2] > goles[3]:
                                    bracket_data[p["Id"]]["Ganador"] = p["Rival 1"]
                                else:
                                    bracket_data[p["Id"]]["Ganador"] = p["Rival 2"]
                            else:
                                if goles[0] > goles[1]:
                                    bracket_data[p["Id"]]["Ganador"] = p["Rival 1"]
                                elif goles[1] > goles[0]:
                                    bracket_data[p["Id"]]["Ganador"] = p["Rival 2"]
        
        for p in partidos_hoy:
            id_p = p["Id"]
            p["Resultado"] = ""
            p["Ganador"] = ""
            if bracket_data[id_p]["Goles 1"] != "-":
                p["Resultado"] = f"{bracket_data[id_p]['Goles 1']} - {bracket_data[id_p]['Goles 2']}"
                p["Ganador"] = bracket_data[id_p]["Ganador"]

        for pestaña in pestañas_jugadores:
            df_jugador = None
            nombre_real = pestaña
            
            if pestaña in nombres_pestañas:
                df_jugador_raw = excel_file.parse(pestaña, header=None, dtype=str)
                nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
                df_jugador = procesar_bloque_resumen(df_jugador_raw)
            
            elecciones_hoy = {"Participante": nombre_real}
            
            if df_jugador is not None and "16vos" in df_jugador.columns:
                set_jugador = set(df_jugador["16vos"].dropna().apply(limpiar_texto))
                set_jugador.discard("")
                puntos = len(set_jugador.intersection(set_base))
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": puntos})
                
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
                    
                    if p["Ganador"] != "":
                        ganador_limpia = limpiar_texto(p["Ganador"])
                        eleccion_limpia = limpiar_texto(encontrado)
                        if ganador_limpia == eleccion_limpia:
                            elecciones_hoy[p["Texto"]] = f"✅ {encontrado}"
                        else:
                            elecciones_hoy[p["Texto"]] = f"• {encontrado}"
                    else:
                        elecciones_hoy[p["Texto"]] = encontrado
            else:
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0})
                for p in partidos_hoy:
                    elecciones_hoy[p["Texto"]] = "Sin Datos"
                    
            if partidos_hoy:
                pronosticos_hoy_lista.append(elecciones_hoy)
                
        df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
        df_pronosticos_hoy = pd.DataFrame(pronosticos_hoy_lista).reset_index(drop=True) if pronosticos_hoy_lista else pd.DataFrame(columns=["Participante"])
        
        return df_ranking, df_pronosticos_hoy, partidos_hoy, bracket_data

    except Exception as e:
        return None, None, partidos_hoy, bracket_data

# Ejecución
with st.spinner("🚀 Sincronizando datos de los brackets..."):
    df_ranking, df_pronosticos_hoy, PARTIDOS_HOY, BRACKET = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, PARTIDOS_HOY)

if df_ranking is None:
    st.error("⚠️ Error crítico al descargar o procesar el archivo Excel.")
else:
    tab_principal, tab_hoy, tab_participantes, tab_bracket_dev = st.tabs([
        "📊 Clasificación Principal", 
        "🔮 Pronósticos del Día", 
        "👤 Participantes",
        "🛠️ Desarrollo Bracket"
    ])

    # --- PESTAÑA 1: CLASIFICACIÓN PRINCIPAL Y PARTIDOS ---
    with tab_principal:
        st.subheader(f"📅 Partidos del Día ({fecha_formateada})")
        if not PARTIDOS_HOY:
            st.info("⚽ No hay partidos agendados para el día de hoy.")
        else:
            columnas_juegos = st.columns(len(PARTIDOS_HOY))
            for i, partido in enumerate(PARTIDOS_HOY):
                with columnas_juegos[i]:
                    marcador = partido.get("Resultado", "")
                    if marcador != "":
                        badge_html = f'<div style="text-align: center; font-size: 26px; font-weight: 800; color: #10B981; background-color: #ECFDF5; padding: 10px; border-radius: 8px; border: 2px solid #A7F3D0; margin-bottom: 10px;">{marcador} <span style="font-size:12px; font-weight:bold; display:block; color:#059669;">FINALIZADO</span></div>'
                    else:
                        badge_html = f'<div style="text-align: center; font-size: 14px; font-weight: 700; color: #1D4ED8; background-color: #EFF6FF; padding: 6px; border-radius: 6px; margin-bottom: 10px;">⏰ {partido["Hora"]} MX</div>'
                    
                    rival1_display = partido['Rival 1'].title() + " 🇲🇽" if "MÉXICO" in partido['Rival 1'].upper() else partido['Rival 1'].title()
                    rival2_display = partido['Rival 2'].title() + " 🇲🇽" if "MÉXICO" in partido['Rival 2'].upper() else partido['Rival 2'].title()

                    st.markdown(f"""
                    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.06); border: 1px solid #F1F5F9;">
                        {badge_html}
                        <div style="font-size: 19px; font-weight: 700; color: #1E293B; text-align: center; line-height: 1.4;">
                            {rival1_display} <br><span style="color:#94A3B8; font-size:14px; font-weight:normal;">VS</span><br> {rival2_display}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
        st.write("---")
        st.subheader("🏅 Tabla de Posiciones General")
        if not df_ranking.empty:
            max_puntos_global = int(df_ranking["Aciertos Totales"].max()) if df_ranking["Aciertos Totales"].max() > 0 else 1
            for index, row in df_ranking.iterrows():
                pts = int(row["Aciertos Totales"])
                progreso = pts / max_puntos_global
                st.markdown(f"""
                <div style="display: flex; align-items: center; background-color: #FFFFFF; padding: 12px 18px; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #F1F5F9;">
                    <div style="width: 50px; font-size: 16px; font-weight: 700; color: #64748B;">#{index + 1}</div>
                    <div style="flex-grow: 1; font-size: 16px; font-weight: 600; color: #334155;">{row['Participante']}</div>
                    <div style="width: 140px; margin-right: 20px;">
                        <div style="background-color: #E2E8F0; border-radius: 10px; height: 8px; width: 100%;">
                            <div style="background-color: #3B82F6; height: 8px; border-radius: 10px; width: {progreso * 100}%;"></div>
                        </div>
                    </div>
                    <div style="font-size: 16px; font-weight: 700; color: #1E293B; width: 60px; text-align: right;">{pts} pts</div>
                </div>
                """, unsafe_allow_html=True)

    # --- PESTAÑA 2: PRONÓSTICOS DEL DÍA ---
    with tab_hoy:
        st.subheader(f"🔮 ¿Qué eligió cada participante para hoy ({fecha_formateada})?")
        if not PARTIDOS_HOY:
            st.info("No hay pronósticos que mostrar porque hoy no se juegan partidos.")
        else:
            st.markdown("Marcación sutil: **✅ Acertado** | **• Errado** | Sin marca = En juego.")
            st.dataframe(df_pronosticos_hoy, use_container_width=True, hide_index=True)

    # --- PESTAÑA 3: VISOR DE PARTICIPANTES ---
    with tab_participantes:
        st.write("")
        st.error("### 🤖 Temporalmente fuera de servicio")

    # --- PESTAÑA 4: BRACKET COMPLETO (9 COLUMNAS BASADO EN LA IMAGEN DE ESPN) ---
    with tab_bracket_dev:
        st.warning("🛠️ **Estructura Corregida:** Flujo visual mapeado directamente desde la imagen de ESPN (image_272bf4.jpg).")
        
        def render_match_html(match_id, data_dict):
            m = data_dict[match_id]
            r1, r2 = m["Rival 1"].title(), m["Rival 2"].title()
            if "México" in r1: r1 += " 🇲🇽"
            if "México" in r2: r2 += " 🇲🇽"
            
            c1 = "winner" if m["Ganador"] == m["Rival 1"] else ("loser" if m["Ganador"] != "Por Definir" else "")
            c2 = "winner" if m["Ganador"] == m["Rival 2"] else ("loser" if m["Ganador"] != "Por Definir" else "")
            
            return f"""
            <div class="bracket-match">
                <div class="bracket-team {c1}"><span>{r1}</span> <span class="bracket-score">{m['Goles 1']}</span></div>
                <div class="bracket-team {c2}"><span>{r2}</span> <span class="bracket-score">{m['Goles 2']}</span></div>
            </div>
            """

        # Creamos las 9 columnas simétricas exactas
        (col_16_izq, col_8_izq, col_4_izq, col_semi_izq, 
         col_final, 
         col_semi_der, col_4_der, col_8_der, col_16_der) = st.columns([1.5, 1.3, 1.3, 1.3, 1.6, 1.3, 1.3, 1.3, 1.5])
        
        # --- CÁLCULOS AUTOMÁTICOS DE GANADORES INTERMEDIOS ---
        # 8vos Izquierda
        w74 = BRACKET["P1"]["Ganador"].title() if BRACKET["P1"]["Ganador"] != "Por Definir" else "W74 (P1)"
        w77 = BRACKET["P2"]["Ganador"].title() if BRACKET["P2"]["Ganador"] != "Por Definir" else "W77 (P2)"
        w73 = BRACKET["P3"]["Ganador"].title() if BRACKET["P3"]["Ganador"] != "Por Definir" else "W73 (P3)"
        w75 = BRACKET["P4"]["Ganador"].title() if BRACKET["P4"]["Ganador"] != "Por Definir" else "W75 (P4)"
        w83 = BRACKET["P5"]["Ganador"].title() if BRACKET["P5"]["Ganador"] != "Por Definir" else "W83 (P5)"
        w84 = BRACKET["P6"]["Ganador"].title() if BRACKET["P6"]["Ganador"] != "Por Definir" else "W84 (P6)"
        w81 = BRACKET["P7"]["Ganador"].title() if BRACKET["P7"]["Ganador"] != "Por Definir" else "W81 (P7)"
        w82 = BRACKET["P8"]["Ganador"].title() if BRACKET["P8"]["Ganador"] != "Por Definir" else "W82 (P8)"

        # 8vos Derecha
        w76 = BRACKET["P9"]["Ganador"].title() if BRACKET["P9"]["Ganador"] != "Por Definir" else "W76 (P9)"
        w78 = BRACKET["P10"]["Ganador"].title() if BRACKET["P10"]["Ganador"] != "Por Definir" else "W78 (P10)"
        w79 = BRACKET["P11"]["Ganador"].title() if BRACKET["P11"]["Ganador"] != "Por Definir" else "W79 (P11)"
        w80 = BRACKET["P12"]["Ganador"].title() if BRACKET["P12"]["Ganador"] != "Por Definir" else "W80 (P12)"
        w86 = BRACKET["P13"]["Ganador"].title() if BRACKET["P13"]["Ganador"] != "Por Definir" else "W86 (P13)"
        w88 = BRACKET["P14"]["Ganador"].title() if BRACKET["P14"]["Ganador"] != "Por Definir" else "W88 (P14)"
        w85 = BRACKET["P15"]["Ganador"].title() if BRACKET["P15"]["Ganador"] != "Por Definir" else "W85 (P15)"
        w87 = BRACKET["P16"]["Ganador"].title() if BRACKET["P16"]["Ganador"] != "Por Definir" else "W87 (P16)"
        
        if "México" in w79: w79 += " 🇲🇽"

        # ==========================================
        # COLUMNAS LADO IZQUIERDO
        # ==========================================
        with col_16_izq:
            st.markdown('<div class="bracket-phase">16vos</div>', unsafe_allow_html=True)
            for pid in ["P1", "P2", "P3", "P4"]:
                st.markdown(render_match_html(pid, BRACKET), unsafe_allow_html=True)
            st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
            for pid in ["P5", "P6", "P7", "P8"]:
                st.markdown(render_match_html(pid, BRACKET), unsafe_allow_html=True)

        with col_8_izq:
            st.markdown('<div class="bracket-phase">8vos</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="bracket-match" style="margin-top: 25px;">
                <div class="bracket-team"><span>{w74}</span></div><div class="bracket-team"><span>{w77}</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 45px;">
                <div class="bracket-team"><span>{w73}</span></div><div class="bracket-team"><span>{w75}</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 105px;">
                <div class="bracket-team"><span>{w83}</span></div><div class="bracket-team"><span>{w84}</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 45px;">
                <div class="bracket-team"><span>{w81}</span></div><div class="bracket-team"><span>{w82}</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_4_izq:
            st.markdown('<div class="bracket-phase">4tos</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-match" style="margin-top: 60px;">
                <div class="bracket-team"><span>W89</span></div><div class="bracket-team"><span>W90</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 200px;">
                <div class="bracket-team"><span>W93</span></div><div class="bracket-team"><span>W94</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_semi_izq:
            st.markdown('<div class="bracket-phase">Semifinal</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-match" style="margin-top: 150px;">
                <div class="bracket-team"><span>W97</span></div><div class="bracket-team"><span>W98</span></div>
            </div>
            """, unsafe_allow_html=True)

        # ==========================================
        # COLUMNA CENTRAL: GRAN FINAL
        # ==========================================
        with col_final:
            st.markdown('<div class="bracket-phase" style="background:#f59e0b; color:white;">🏆 FINAL</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-match" style="margin-top: 145px; border: 2px solid #f59e0b;">
                <div class="bracket-team" style="font-weight:700;"><span>W101</span></div>
                <div class="bracket-team" style="font-weight:700;"><span>W102</span></div>
            </div>
            """, unsafe_allow_html=True)

        # ==========================================
        # COLUMNAS LADO DERECHO
        # ==========================================
        with col_semi_der:
            st.markdown('<div class="bracket-phase">Semifinal</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-match" style="margin-top: 150px;">
                <div class="bracket-team"><span>W99</span></div><div class="bracket-team"><span>W100</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_4_der:
            st.markdown('<div class="bracket-phase">4tos</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-match" style="margin-top: 60px;">
                <div class="bracket-team"><span>W91</span></div><div class="bracket-team"><span>W92</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 200px;">
                <div class="bracket-team"><span>W95</span></div><div class="bracket-team"><span>W96</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_8_der:
            st.markdown('<div class="bracket-phase">8vos</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="bracket-match" style="margin-top: 25px;">
                <div class="bracket-team"><span>{w76}</span></div><div class="bracket-team"><span>{w78}</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 45px;">
                <div class="bracket-team"><span>{w79}</span></div><div class="bracket-team"><span>{w80}</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 105px;">
                <div class="bracket-team"><span>{w86}</span></div><div class="bracket-team"><span>{w88}</span></div>
            </div>
            <div class="bracket-match" style="margin-top: 45px;">
                <div class="bracket-team"><span>{w85}</span></div><div class="bracket-team"><span>{w87}</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col_16_der:
            st.markdown('<div class="bracket-phase">16vos</div>', unsafe_allow_html=True)
            for pid in ["P9", "P10", "P11", "P12"]:
                st.markdown(render_match_html(pid, BRACKET), unsafe_allow_html=True)
            st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
            for pid in ["P13", "P14", "P15", "P16"]:
                st.markdown(render_match_html(pid, BRACKET), unsafe_allow_html=True)
