import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Quiniela Fase Final", page_icon="⚽", layout="wide")

# Estilos CSS
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

SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"
ID_PESTAÑAS = ["HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", "JMG", "JV", "CAAM", "DSR", "SLO", "JGLM"]

def limpiar_texto(s):
    s = str(s).strip().upper()
    s = re.sub(r'[ÁÉÍÓÚ]', lambda m: {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U'}[m.group(0)], s)
    return s

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

# ==============================================================================
# 2. PROCESAMIENTO DINÁMICO DEL TORNEO DESDE EXCEL
# ==============================================================================
@st.cache_data(ttl=60)
def cargar_y_procesar_todo_el_torneo_dinamico(spreadsheet_id, pestañas_jugadores):
    url = f"https://drive.google.com/uc?export=download&id={spreadsheet_id}"
    
    # Valores de retorno por defecto en caso de error
    calendario_dinamico = []
    fechas_disponibles = []
    bracket_data = {}
    df_ranking = pd.DataFrame(columns=["Participante", "Aciertos Totales"])
    df_pronosticos_por_fecha = {}

    try:
        respuesta = requests.get(url, timeout=15)
        if respuesta.status_code != 200: 
            return df_ranking, df_pronosticos_por_fecha, calendario_dinamico, fechas_disponibles, bracket_data
        
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content), engine='openpyxl')
        nombres_pestañas = excel_file.sheet_names
        
        # 2.1 Procesar Base para Ranking
        if "BASE" not in nombres_pestañas:
            return df_ranking, df_pronosticos_por_fecha, calendario_dinamico, fechas_disponibles, bracket_data
        
        df_base_raw = excel_file.parse("BASE", header=None, dtype=str)
        df_base = procesar_bloque_resumen(df_base_raw)
        set_base = set(df_base["16vos"].dropna().apply(limpiar_texto)) if df_base is not None else set()
        set_base.discard("")

        # 2.2 Procesar Pestaña Calendario dinámicamente
        pestaña_cal = [n for n in nombres_pestañas if "CALENDARIO" in n.upper()]
        if pestaña_cal:
            df_cal_excel = excel_file.parse(pestaña_cal[0], dtype=str)
            # Asegurar limpiar nombres de columnas
            df_cal_excel.columns = [str(c).strip().title() for c in df_cal_excel.columns]
            
            # Mapeo de columnas esperadas
            col_partido = [c for c in df_cal_excel.columns if "PARTIDO" in c.upper()][0]
            col_fecha = [c for c in df_cal_excel.columns if "FECHA" in c.upper()][0]
            col_hora = [c for c in df_cal_excel.columns if "HORA" in c.upper()][0]
            col_marcador = [c for c in df_cal_excel.columns if "MARCADOR" in c.upper()][0]

            cont_id = 1
            for _, fila in df_cal_excel.iterrows():
                texto_partido = str(fila[col_partido]).strip()
                fecha_p = str(fila[col_fecha]).strip()
                hora_p = str(fila[col_hora]).strip()
                marcador_crudo = str(fila[col_marcador]).strip() if pd.notna(fila[col_marcador]) else ""

                if "VS" in texto_partido.upper() and re.search(r'\d{2}/\d{2}/\d{4}', fecha_p):
                    rivales = texto_partido.split(re.search(r'\s+VS\s+', texto_partido, re.IGNORECASE).group(0))
                    rival1 = rivales[0].strip()
                    rival2 = rivales[1].strip()
                    
                    id_p = f"P{cont_id}"
                    cont_id += 1

                    partido_dict = {
                        "Id": id_p,
                        "Fecha": fecha_p,
                        "Hora": hora_p,
                        "Rival 1": rival1,
                        "Rival 2": rival2,
                        "Texto": f"{rival1} 🆚 {rival2}",
                        "Keys 1": [limpiar_texto(rival1), limpiar_texto(rival1)[:3]],
                        "Keys 2": [limpiar_texto(rival2), limpiar_texto(rival2)[:3]],
                        "Resultado": "-",
                        "Ganador": "Por Definir"
                    }

                    # Procesar marcadores si existen
                    bracket_data[id_p] = {"Rival 1": rival1, "Rival 2": rival2, "Goles 1": "-", "Goles 2": "-", "Ganador": "Por Definir"}
                    if marcador_crudo != "" and marcador_crudo != "nan" and re.search(r'\d', marcador_crudo):
                        goles = [int(g) for g in re.findall(r'\d+', marcador_crudo)]
                        if len(goles) >= 2:
                            partido_dict["Resultado"] = f"{goles[0]} - {goles[1]}"
                            bracket_data[id_p]["Goles 1"] = str(goles[0])
                            bracket_data[id_p]["Goles 2"] = str(goles[1])
                            
                            if "HEX" in marcador_crudo.upper() or "PEN" in marcador_crudo.upper() and len(goles) >= 4:
                                bracket_data[id_p]["Goles 1"] += f" ({goles[2]})"
                                bracket_data[id_p]["Goles 2"] += f" ({goles[3]})"
                                partido_dict["Ganador"] = rival1 if goles[2] > goles[3] else rival2
                            else:
                                if goles[0] > goles[1]: partido_dict["Ganador"] = rival1
                                elif goles[1] > goles[0]: partido_dict["Ganador"] = rival2
                            
                            bracket_data[id_p]["Ganador"] = partido_dict["Ganador"]

                    calendario_dinamico.append(partido_dict)

        # Extraer fechas únicas ordenadas cronológicamente
        if calendario_dinamico:
            fechas_disponibles = sorted(list(set(p["Fecha"] for p in calendario_dinamico)), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))

        # 2.3 Procesar elecciones de los jugadores y cruzarlas por cada fecha disponible
        datos_ranking = []
        diccionario_jugadores_procesados = {}

        for pestaña in pestañas_jugadores:
            df_jugador = None
            nombre_real = pestaña
            if pestaña in nombres_pestañas:
                df_jugador_raw = excel_file.parse(pestaña, header=None, dtype=str)
                nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
                df_jugador = procesar_bloque_resumen(df_jugador_raw)
            
            set_jugador = set()
            if df_jugador is not None and "16vos" in df_jugador.columns:
                set_jugador = set(df_jugador["16vos"].dropna().apply(limpiar_texto))
                set_jugador.discard("")
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": len(set_jugador.intersection(set_base))})
            else:
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0})
            
            diccionario_jugadores_procesados[nombre_real] = set_jugador

        df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).drop_duplicates(subset=["Participante"]).reset_index(drop=True)

        # Construir matriz de pronósticos por cada fecha individual
        for f_disp in fechas_disponibles:
            partidos_de_esta_fecha = [p for p in calendario_dinamico if p["Fecha"] == f_disp]
            lista_pronosticos_fecha = []

            for nom_jugador, set_jugador in diccionario_jugadores_procesados.items():
                elecciones_fecha = {"Participante": nom_jugador}
                
                for p in partidos_de_esta_fecha:
                    encontrado = "Ninguno"
                    for pronostico in list(set_jugador):
                        if any(k in pronostico for k in p["Keys 1"]): encontrado = p["Rival 1"].title(); break
                        elif any(k in pronostico for k in p["Keys 2"]): encontrado = p["Rival 2"].title(); break
                    
                    # Regla de Oro aplicada dinámicamente
                    rival_real_1 = p["Rival 1"].title()
                    rival_real_2 = p["Rival 2"].title()
                    
                    if encontrado != "Ninguno" and encontrado not in [rival_real_1, rival_real_2]:
                        elecciones_fecha[p["Texto"]] = f"❌ Eliminado Previo ({encontrado})"
                    else:
                        if p.get("Ganador") and p["Ganador"] != "Por Definir":
                            elecciones_fecha[p["Texto"]] = f"✅ {encontrado}" if limpiar_texto(p["Ganador"]) == limpiar_texto(encontrado) else f"• {encontrado}"
                        else: 
                            elecciones_fecha[p["Texto"]] = encontrado
                
                lista_pronosticos_fecha.append(elecciones_fecha)
            
            df_pronosticos_por_fecha[f_disp] = pd.DataFrame(lista_pronosticos_fecha)

        return df_ranking, df_pronosticos_por_fecha, calendario_dinamico, fechas_disponibles, bracket_data
    except Exception as e:
        st.error(f"Error procesando el archivo Excel: {e}")
        return df_ranking, df_pronosticos_por_fecha, calendario_dinamico, fechas_disponibles, bracket_data

# Ejecución Inicial del Procesamiento Dinámico
with st.spinner("🚀 Sincronizando calendario y pronósticos en tiempo real..."):
    df_ranking, df_pronosticos_master, CALENDARIO_COMPLETO, FECHAS_DISPONIBLES, BRACKET = cargar_y_procesar_todo_el_torneo_dinamico(SPREADSHEET_ID, ID_PESTAÑAS)

if CALENDARIO_COMPLETO:
    PARTIDOS_PROXIMOS = [
        partido for partido in CALENDARIO_COMPLETO 
        if datetime.strptime(partido["Fecha"], "%d/%m/%Y") >= fecha_actual_dt
    ]

    tab_principal, tab_hoy, tab_bracket_dev = st.tabs(["📊 Clasificación", "🔮 Pronósticos por Fecha", "🛠️ Desarrollo Bracket"])

    # --- PESTAÑA PRINCIPAL ---
    with tab_principal:
        st.subheader("📅 Partidos del Día y Próximos Encuentros")
        
        if not PARTIDOS_PROXIMOS: 
            st.info("⚽ No hay más partidos agendados o pendientes para esta ronda.")
        else:
            df_prox = pd.DataFrame(PARTIDOS_PROXIMOS)
            fechas_futuras = sorted(list(df_prox["Fecha"].unique()), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            
            for f_futura in fechas_futuras:
                partidos_del_dia = [p for p in PARTIDOS_PROXIMOS if p["Fecha"] == f_futura]
                st.markdown(f"##### 🗓️ Encuentros del día {f_futura}")
                
                columnas_juegos = st.columns(len(partidos_del_dia))
                for i, partido in enumerate(partidos_del_dia):
                    with columnas_juegos[i]:
                        id_p = partido["Id"]
                        g1_b = BRACKET[id_p]["Goles 1"]
                        g2_b = BRACKET[id_p]["Goles 2"]
                        
                        if g1_b != "-":
                            marcador = f"{g1_b} - {g2_b}"
                            badge_html = f'<div style="text-align: center; font-size: 26px; font-weight: 800; color: #10B981; background-color: #ECFDF5; padding: 10px; border-radius: 8px; border: 2px solid #A7F3D0; margin-bottom: 10px;">{marcador} <span style="font-size:12px; font-weight:bold; display:block; color:#059669;">FINALIZADO</span></div>'
                        else:
                            badge_html = f'<div style="text-align: center; font-size: 14px; font-weight: 700; color: #1D4ED8; background-color: #EFF6FF; padding: 6px; border-radius: 6px; margin-bottom: 10px;">⏰ {partido["Hora"]}</div>'
                        
                        st.markdown(f'<div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); border: 1px solid #F1F5F9;">{badge_html}<div style="font-size: 19px; font-weight: 700; color: #1E293B; text-align: center; line-height: 1.4;">{partido["Rival 1"].title()} <br><span style="color:#94A3B8; font-size:14px; font-weight:normal;">VS</span><br> {partido["Rival 2"].title()}</div></div>', unsafe_allow_html=True)
                st.write("") 
            
        st.write("---")
        st.subheader("🏅 Tabla de Posiciones General")
        max_puntos_global = int(df_ranking["Aciertos Totales"].max()) if df_ranking["Aciertos Totales"].max() > 0 else 1
        for index, row in df_ranking.iterrows():
            pts = int(row["Aciertos Totales"])
            st.markdown(f'<div style="display: flex; align-items: center; background-color: #FFFFFF; padding: 12px 18px; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #F1F5F9;"><div style="width: 50px; font-size: 16px; font-weight: 700; color: #64748B;">#{index + 1}</div><div style="flex-grow: 1; font-size: 16px; font-weight: 600; color: #334155;">{row["Participante"]}</div><div style="width: 140px; margin-right: 20px;"><div style="background-color: #E2E8F0; border-radius: 10px; height: 8px; width: 100%;"><div style="background-color: #3B82F6; height: 8px; border-radius: 10px; width: {(pts / max_puntos_global) * 100}%;"></div></div></div><div style="font-size: 16px; font-weight: 700; color: #1E293B; width: 60px; text-align: right;">{pts} pts</div></div>', unsafe_allow_html=True)

    # --- PESTAÑA PRONÓSTICOS (CON RENDIMIENTO CORREGIDO Y FECHAS DINÁMICAS FUTURAS) ---
    with tab_hoy:
        st.markdown("### 🔮 Consulta de Pronósticos")
        
        # Las sub-pestañas se crean dinámicamente usando las fechas leídas directamente desde el Excel
        sub_tabs_fechas = st.tabs([f"📅 {f}" for f in FECHAS_DISPONIBLES])
        
        for idx_f, fecha_select in enumerate(FECHAS_DISPONIBLES):
            with sub_tabs_fechas[idx_f]:
                df_fecha = df_pronosticos_master.get(fecha_select, pd.DataFrame())
                
                if df_fecha.empty:
                    st.info("No hay pronósticos disponibles para esta fecha.")
                else:
                    st.caption(f"Visualizando las elecciones de los participantes para los juegos del {fecha_select}")
                    st.dataframe(df_fecha, use_container_width=True, hide_index=True)

    # --- PESTAÑA BRACKET DESARROLLO ---
    with tab_bracket_dev:
        st.markdown("### 🏗️ Bracket del Mundial 2026")
        
        def render_match_html(match_id, data_dict):
            if match_id not in data_dict:
                return '<div class="b-card"><div class="b-team"><span>Por Definir</span></div></div>'
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
            if pid in BRACKET:
                ganador = BRACKET[pid]["Ganador"]
                if ganador and ganador != "Por Definir":
                    return ganador.title()
            return f"Ganador {pid}"

        w = {f"P{i}": get_w(f"P{i}") for i in range(1, 17)}

        bracket_html = f"""
        <style>
            .b-container {{ display: grid; grid-template-columns: repeat(9, 1fr); gap: 12px; background-color: #0f172a; padding: 20px; border-radius: 12px; font-family: sans-serif; min-width: 1200px; }}
            .b-column {{ display: grid; grid-template-rows: repeat(8, 1fr); height: 850px; }}
            .b-match {{ display: flex; flex-direction: column; justify-content: center; padding: 2px 0; }}
            .b-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: white; font-size: 12px; }}
            .b-team {{ display: flex; justify-content: space-between; margin: 3px 0; }}
            .winner {{ color: #4ade80; font-weight: bold; }}
            .score {{ font-weight: bold; color: #94a3b8; }}
            .phase-title {{ text-align: center; color: #94a3b8; font-size: 13px; font-weight: bold; margin-bottom: 15px; }}
            .final-card {{ border: 2px solid #f59e0b; }}
            .match-date {{ font-size: 10px; color: #94a3b8; text-align: center; margin-top: 5px; font-weight: 500; }}
        </style>

        <div class="b-container">
            <div class="phase-title">16vos (Izq)</div><div class="phase-title">8vos</div><div class="phase-title">4tos</div><div class="phase-title">Semifinal</div>
            <div class="phase-title" style="color:#f59e0b;">🏆 FINAL</div>
            <div class="phase-title">Semifinal</div><div class="phase-title">4tos</div><div class="phase-title">8vos</div><div class="phase-title">16vos (Der)</div>

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
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P1']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P2']}</span></div></div></div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P3']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P4']}</span></div></div></div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P5']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P6']}</span></div></div></div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P7']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P8']}</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>8vos Izq Sup</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>8vos Izq Inf</span></div></div></div>
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>4tos Izq</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>Semifinal 1</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;">
                    <div class="b-card final-card">
                        <div class="b-team" style="font-weight:700;"><span>Finalista 1</span></div>
                        <div style="height:1px; background:#f59e0b; margin:6px 0;"></div>
                        <div class="b-team" style="font-weight:700;"><span>Finalista 2</span></div>
                    </div>
                </div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>Semifinal 2</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>4tos Der</span></div></div></div>
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>8vos Der Sup</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>8vos Der Inf</span></div></div></div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P9']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P10']}</span></div></div></div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P11']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P12']}</span></div></div></div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P13']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P14']}</span></div></div></div>
                <div style="grid-row: span 2; display: flex; flex-direction: column; justify-content: center;"><div class="b-card"><div class="b-team"><span>{w['P15']}</span></div><div style="height:1px; background:#334155; margin:4px 0;"></div><div class="b-team"><span>{w['P16']}</span></div></div></div>
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
else:
    st.error("No se pudo estructurar el calendario desde el archivo Excel. Revisa los nombres de las columnas en la pestaña 'CALENDARIO'.")
