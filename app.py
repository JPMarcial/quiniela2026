import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Quiniela Fase Final", page_icon="⚽", layout="wide")

# Estilos CSS mejorados con contenedores Flexbox para alineación vertical perfecta
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] { background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    
    /* Contenedor flexible de columna para centrado perfecto */
    .bracket-column-flex {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 680px; /* Altura fija para contener uniformemente el árbol */
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

CALENDARIO_COMPLETO = [
    # --- LADO IZQUIERDO: Bloque Superior ---
    {"Id": "P1", "Fecha": "29/06/2026", "Rival 1": "ALEMANIA", "Rival 2": "PARAGUAY", "Texto": "Alemania 🆚 Paraguay", "Hora": "14:00", "Keys 1": ["ALEMANIA", "GER"], "Keys 2": ["PARAGUAY", "PAR"]},
    {"Id": "P2", "Fecha": "30/06/2026", "Rival 1": "FRANCIA", "Rival 2": "SUECIA", "Texto": "Francia 🆚 Suecia", "Hora": "15:00", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["SUECIA", "SUE"]},
    {"Id": "P3", "Fecha": "28/06/2026", "Rival 1": "SUDÁFRICA", "Rival 2": "CANADÁ", "Texto": "Sudáfrica 🆚 Canadá", "Hora": "13:00", "Keys 1": ["SUDAFRICA", "SUDÁFRICA", "RSA"], "Keys 2": ["CANADA", "CANADÁ", "CAN"]},
    {"Id": "P4", "Fecha": "29/06/2026", "Rival 1": "PAÍSES BAJOS", "Rival 2": "MARRUECOS", "Texto": "Países Bajos 🆚 Marruecos", "Hora": "20:00", "Keys 1": ["PAISES BAJOS", "PAÍSES BAJOS", "NED", "HOLANDA"], "Keys 2": ["MARRUECOS", "MAR"]},
    
    # --- LADO IZQUIERDO: Bloque Inferior ---
    {"Id": "P5", "Fecha": "02/07/2026", "Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia", "Hora": "17:00", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["CROACIA", "CRO"]},
    {"Id": "P6", "Fecha": "02/07/2026", "Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria", "Hora": "13:00", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["AUSTRIA", "AUT"]},
    {"Id": "P7", "Fecha": "01/07/2026", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA", "Texto": "Estados Unidos 🆚 Bosnia", "Hora": "18:00", "Keys 1": ["ESTADOS UNIDOS", "USA", "EEUU"], "Keys 2": ["BOSNIA", "HERZEGOVINA", "BOSNIA-HERZ"]},
    {"Id": "P8", "Fecha": "01/07/2026", "Rival 1": "BÉLGICA", "Rival 2": "SENEGAL", "Texto": "Bélgica 🆚 Senegal", "Hora": "14:00", "Keys 1": ["BELGICA", "BÉLGICA", "BEL"], "Keys 2": ["SENEGAL", "SEN"]},
    
    # --- LADO DERECHO: Bloque Superior ---
    {"Id": "P9", "Fecha": "29/06/2026", "Rival 1": "BRASIL", "Rival 2": "JAPÓN", "Texto": "Brasil 🆚 Japón", "Hora": "11:00", "Keys 1": ["BRASIL", "BRA"], "Keys 2": ["JAPON", "JAPÓN", "JPN"]},
    {"Id": "P10", "Fecha": "30/06/2026", "Rival 1": "COSTA DE MARFIL", "Rival 2": "NORUEGA", "Texto": "Costa de Marfil 🆚 Noruega", "Hora": "11:00", "Keys 1": ["COSTA DE MARFIL", "MARFIL", "CIV"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Id": "P11", "Fecha": "30/06/2026", "Rival 1": "MÉXICO", "Rival 2": "ECUADOR", "Texto": "México 🇲🇽 🆚 Ecuador", "Hora": "19:00", "Keys 1": ["MEXICO", "MÉXICO", "MEX"], "Keys 2": ["ECUADOR", "ECU"]},
    {"Id": "P12", "Fecha": "01/07/2026", "Rival 1": "INGLATERRA", "Rival 2": "RD CONGO", "Texto": "Inglaterra 🆚 RD Congo", "Hora": "10:00", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["CONGO", "RD CONGO", "RDC"]},
    
    # --- LADO DERECHO: Bloque Inferior ---
    {"Id": "P13", "Fecha": "03/07/2026", "Rival 1": "ARGENTINA", "Rival 2": "CABO VERDE", "Texto": "Argentina 🆚 Cabo Verde", "Hora": "16:00", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["CABO VERDE", "CPV"]},
    {"Id": "P14", "Fecha": "03/07/2026", "Rival 1": "AUSTRALIA", "Rival 2": "EGIPTO", "Texto": "Australia 🆚 Egipto", "Hora": "12:00", "Keys 1": ["AUSTRALIA", "AUS"], "Keys 2": ["EGIPTO", "EGY"]},
    {"Id": "P15", "Fecha": "02/07/2026", "Rival 1": "SUIZA", "Rival 2": "ARGELIA", "Texto": "Suiza 🆚 Argelia", "Hora": "21:00", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["ARGELIA", "ALG"]},
    {"Id": "P16", "Fecha": "03/07/2026", "Rival 1": "COLOMBIA", "Rival 2": "GHANA", "Texto": "Colombia 🆚 Ghana", "Hora": "19:30", "Keys 1": ["COLOMBIA", "COL"], "Keys 2": ["GHANA", "GHA"]}
]

PARTIDOS_HOY = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_formateada]

SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"
ID_PESTAÑAS = ["HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", "JMG", "JV", "CAAM", "DSR", "SLO"]

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

@st.cache_data(ttl=60)
def cargar_y_procesar_todo_el_torneo(spreadsheet_id, pestañas_jugadores, partidos_hoy):
    url = f"https://drive.google.com/uc?export=download&id={spreadsheet_id}"
    datos_ranking = []
    pronosticos_hoy_lista = []
    
    bracket_data = {}
    for p in CALENDARIO_COMPLETO:
        bracket_data[p["Id"]] = {"Rival 1": p["Rival 1"], "Rival 2": p["Rival 2"], "Goles 1": "-", "Goles 2": "-", "Ganador": "Por Definir"}
    
    try:
        respuesta = requests.get(url, timeout=15)
        if respuesta.status_code != 200: return None, None, partidos_hoy, bracket_data
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content), engine='openpyxl')
        nombres_pestañas = excel_file.sheet_names
        
        if "BASE" not in nombres_pestañas: return None, None, partidos_hoy, bracket_data
        df_base_raw = excel_file.parse("BASE", header=None, dtype=str)
        df_base = procesar_bloque_resumen(df_base_raw)
        if df_base is None: return None, None, partidos_hoy, bracket_data
        set_base = set(df_base["16vos"].dropna().apply(limpiar_texto))
        set_base.discard("")

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
        
        for p in partidos_hoy:
            id_p = p["Id"]
            if bracket_data[id_p]["Goles 1"] != "-":
                p["Resultado"] = f"{bracket_data[id_p]['Goles 1']} - {bracket_data[id_p]['Goles 2']}"
                p["Ganador"] = bracket_data[id_p]["Ganador"]

        for pestaña in pestañas_jugadores:
            df_jugador = None; nombre_real = pestaña
            if pestaña in nombres_pestañas:
                df_jugador_raw = excel_file.parse(pestaña, header=None, dtype=str)
                nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
                df_jugador = procesar_bloque_resumen(df_jugador_raw)
            elecciones_hoy = {"Participante": nombre_real}
            
            if df_jugador is not None and "16vos" in df_jugador.columns:
                set_jugador = set(df_jugador["16vos"].dropna().apply(limpiar_texto))
                set_jugador.discard("")
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": len(set_jugador.intersection(set_base))})
                for p in partidos_hoy:
                    encontrado = "Ninguno"
                    for pronostico in list(set_jugador):
                        if any(k in pronostico for k in p["Keys 1"]): encontrado = p["Rival 1"].title(); break
                        elif any(k in pronostico for k in p["Keys 2"]): encontrado = p["Rival 2"].title(); break
                    if p.get("Ganador"):
                        elecciones_hoy[p["Texto"]] = f"✅ {encontrado}" if limpiar_texto(p["Ganador"]) == limpiar_texto(encontrado) else f"• {encontrado}"
                    else: elecciones_hoy[p["Texto"]] = encontrado
            else:
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0})
                for p in partidos_hoy: elecciones_hoy[p["Texto"]] = "Sin Datos"
            if partidos_hoy: pronosticos_hoy_lista.append(elecciones_hoy)
                
        df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
        df_pronosticos_hoy = pd.DataFrame(pronosticos_hoy_lista).reset_index(drop=True) if pronosticos_hoy_lista else pd.DataFrame(columns=["Participante"])
        return df_ranking, df_pronosticos_hoy, partidos_hoy, bracket_data
    except Exception: return None, None, partidos_hoy, bracket_data

with st.spinner("🚀 Sincronizando datos..."):
    df_ranking, df_pronosticos_hoy, PARTIDOS_HOY, BRACKET = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, PARTIDOS_HOY)

if df_ranking is not None:
    tab_principal, tab_hoy, tab_participantes, tab_bracket_dev = st.tabs(["📊 Clasificación", "🔮 Pronósticos", "👤 Participantes", "🛠️ Desarrollo Bracket"])

    # --- PESTAÑA PRINCIPAL ---
    with tab_principal:
        st.subheader(f"📅 Partidos del Día ({fecha_formateada})")
        if not PARTIDOS_HOY: st.info("⚽ No hay partidos agendados para hoy.")
        else:
            columnas_juegos = st.columns(len(PARTIDOS_HOY))
            for i, partido in enumerate(PARTIDOS_HOY):
                with columnas_juegos[i]:
                    marcador = partido.get("Resultado", "")
                    badge_html = f'<div style="text-align: center; font-size: 26px; font-weight: 800; color: #10B981; background-color: #ECFDF5; padding: 10px; border-radius: 8px; border: 2px solid #A7F3D0; margin-bottom: 10px;">{marcador} <span style="font-size:12px; font-weight:bold; display:block; color:#059669;">FINALIZADO</span></div>' if marcador != "" else f'<div style="text-align: center; font-size: 14px; font-weight: 700; color: #1D4ED8; background-color: #EFF6FF; padding: 6px; border-radius: 6px; margin-bottom: 10px;">⏰ {partido["Hora"]} MX</div>'
                    st.markdown(f'<div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); border: 1px solid #F1F5F9;">{badge_html}<div style="font-size: 19px; font-weight: 700; color: #1E293B; text-align: center; line-height: 1.4;">{partido["Rival 1"].title()} <br><span style="color:#94A3B8; font-size:14px; font-weight:normal;">VS</span><br> {partido["Rival 2"].title()}</div></div>', unsafe_allow_html=True)
            
        st.write("---")
        st.subheader("🏅 Tabla de Posiciones General")
        max_puntos_global = int(df_ranking["Aciertos Totales"].max()) if df_ranking["Aciertos Totales"].max() > 0 else 1
        for index, row in df_ranking.iterrows():
            pts = int(row["Aciertos Totales"])
            st.markdown(f'<div style="display: flex; align-items: center; background-color: #FFFFFF; padding: 12px 18px; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #F1F5F9;"><div style="width: 50px; font-size: 16px; font-weight: 700; color: #64748B;">#{index + 1}</div><div style="flex-grow: 1; font-size: 16px; font-weight: 600; color: #334155;">{row["Participante"]}</div><div style="width: 140px; margin-right: 20px;"><div style="background-color: #E2E8F0; border-radius: 10px; height: 8px; width: 100%;"><div style="background-color: #3B82F6; height: 8px; border-radius: 10px; width: {(pts / max_puntos_global) * 100}%;"></div></div></div><div style="font-size: 16px; font-weight: 700; color: #1E293B; width: 60px; text-align: right;">{pts} pts</div></div>', unsafe_allow_html=True)

    # --- PESTAÑA PRONÓSTICOS ---
    with tab_hoy:
        st.dataframe(df_pronosticos_hoy, use_container_width=True, hide_index=True)

    # --- PESTAÑA PARTICIPANTES ---
    with tab_participantes:
        st.error("### 🤖 Temporalmente fuera de servicio")

   # --- PESTAÑA BRACKET (9 COLUMNAS AUTOMÁTICAS Y ALINEADAS CORRECTAMENTE) ---
    with tab_bracket_dev:
        st.info("💡  En construcción ")
        
        def render_match_html(match_id, data_dict):
            m = data_dict[match_id]
            r1, r2 = m["Rival 1"].title(), m["Rival 2"].title()
            if "México" in r1: r1 += " 🇲🇽"
            if "México" in r2: r2 += " 🇲🇽"
            c1 = "winner" if m["Ganador"] == m["Rival 1"] else ("loser" if m["Ganador"] != "Por Definir" else "")
            c2 = "winner" if m["Ganador"] == m["Rival 2"] else ("loser" if m["Ganador"] != "Por Definir" else "")
            return f"""
            <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; width: 100%;">
                <div class="bracket-match">
                    <div class="bracket-team {c1}"><span>{r1}</span> <span class="bracket-score">{m['Goles 1']}</span></div>
                    <div class="bracket-team {c2}"><span>{r2}</span> <span class="bracket-score">{m['Goles 2']}</span></div>
                </div>
            </div>
            """

        # Estructura de columnas simétricas
        cols = st.columns([1.5, 1.3, 1.3, 1.3, 1.6, 1.3, 1.3, 1.3, 1.5])
        
        # Mapeo de ganadores para Octavos de Final
        w = {pid: (BRACKET[pid]["Ganador"].title() if BRACKET[pid]["Ganador"] != "Por Definir" else f"Ganador {pid}") for pid in BRACKET}
        if "México" in w["P11"]: w["P11"] += " 🇲🇽"

        # 1. 16vos Izquierda (Un solo contenedor maestro con distribución proporcional)
        with cols[0]:
            st.markdown('<div class="bracket-phase">16vos</div>', unsafe_allow_html=True)
            st.markdown('<div class="bracket-column-flex">', unsafe_allow_html=True)
            st.markdown(render_match_html("P1", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P2", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P3", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P4", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P5", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P6", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P7", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P8", BRACKET), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # 2. 8vos Izquierda
        with cols[1]:
            st.markdown('<div class="bracket-phase">8vos</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="bracket-column-flex">
                <div class="bracket-match"><div class="bracket-team"><span>{w['P1']}</span></div><div class="bracket-team"><span>{w['P2']}</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>{w['P3']}</span></div><div class="bracket-team"><span>{w['P4']}</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>{w['P5']}</span></div><div class="bracket-team"><span>{w['P6']}</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>{w['P7']}</span></div><div class="bracket-team"><span>{w['P8']}</span></div></div>
            </div>
            """, unsafe_allow_html=True)

        # 3. 4tos Izquierda
        with cols[2]:
            st.markdown('<div class="bracket-phase">4tos</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-column-flex">
                <div class="bracket-match"><div class="bracket-team"><span>W89</span></div><div class="bracket-team"><span>W90</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>W93</span></div><div class="bracket-team"><span>W94</span></div></div>
            </div>
            """, unsafe_allow_html=True)

        # 4. Semifinal Izquierda
        with cols[3]:
            st.markdown('<div class="bracket-phase">Semifinal</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-column-flex">
                <div class="bracket-match"><div class="bracket-team"><span>W97</span></div><div class="bracket-team"><span>W98</span></div></div>
            </div>
            """, unsafe_allow_html=True)

        # 5. Gran Final (Centro)
        with cols[4]:
            st.markdown('<div class="bracket-phase" style="background:#f59e0b; color:white;">🏆 FINAL</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-column-flex">
                <div class="bracket-match" style="border: 2px solid #f59e0b;">
                    <div class="bracket-team" style="font-weight:700;"><span>W101</span></div>
                    <div class="bracket-team" style="font-weight:700;"><span>W102</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 6. Semifinal Derecha
        with cols[5]:
            st.markdown('<div class="bracket-phase">Semifinal</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-column-flex">
                <div class="bracket-match"><div class="bracket-team"><span>W99</span></div><div class="bracket-team"><span>W100</span></div></div>
            </div>
            """, unsafe_allow_html=True)

        # 7. 4tos Derecha
        with cols[6]:
            st.markdown('<div class="bracket-phase">4tos</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="bracket-column-flex">
                <div class="bracket-match"><div class="bracket-team"><span>W91</span></div><div class="bracket-team"><span>W92</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>W95</span></div><div class="bracket-team"><span>W96</span></div></div>
            </div>
            """, unsafe_allow_html=True)

        # 8. 8vos Derecha
        with cols[7]:
            st.markdown('<div class="bracket-phase">8vos</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="bracket-column-flex">
                <div class="bracket-match"><div class="bracket-team"><span>{w['P9']}</span></div><div class="bracket-team"><span>{w['P10']}</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>{w['P11']}</span></div><div class="bracket-team"><span>{w['P12']}</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>{w['P13']}</span></div><div class="bracket-team"><span>{w['P14']}</span></div></div>
                <div class="bracket-match"><div class="bracket-team"><span>{w['P15']}</span></div><div class="bracket-team"><span>{w['P16']}</span></div></div>
            </div>
            """, unsafe_allow_html=True)

        # 9. 16vos Derecha (Un solo contenedor maestro con distribución proporcional)
        with cols[8]:
            st.markdown('<div class="bracket-phase">16vos</div>', unsafe_allow_html=True)
            st.markdown('<div class="bracket-column-flex">', unsafe_allow_html=True)
            st.markdown(render_match_html("P9", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P10", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P11", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P12", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P13", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P14", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P15", BRACKET), unsafe_allow_html=True)
            st.markdown(render_match_html("P16", BRACKET), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
