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
    .bracket-phase { font-weight: bold; text-align: center; color: #475569; background: #e2e8f0; padding: 6px; border-radius: 6px; margin-bottom: 15px; font-size: 14px; }
    .bracket-match { background: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 20px; }
    .bracket-team { font-size: 13px; font-weight: 600; color: #1e293b; padding: 3px 6px; display: flex; justify-content: space-between; }
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
fecha_formateada = fecha_actual_mx.strftime("%d/%m") 

CALENDARIO_COMPLETO = [
    {"Fecha": "30/06", "Rival 1": "COSTA DE MARFIL", "Rival 2": "NORUEGA", "Texto": "Costa de Marfil 🆚 Noruega", "Hora": "11:00 AM", "Keys 1": ["COSTA DE MARFIL", "MARFIL", "CIV"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Fecha": "30/06", "Rival 1": "FRANCIA", "Rival 2": "SUECIA", "Texto": "Francia 🆚 Suecia", "Hora": "03:00 PM", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["SUECIA", "SUE"]},
    {"Fecha": "30/06", "Rival 1": "MÉXICO", "Rival 2": "ECUADOR", "Texto": "México 🇲🇽 🆚 Ecuador", "Hora": "07:00 PM", "Keys 1": ["MEXICO", "MÉXICO", "MEX"], "Keys 2": ["ECUADOR", "ECU"]},
    {"Fecha": "01/07", "Rival 1": "INGLATERRA", "Rival 2": "RD CONGO", "Texto": "Inglaterra 🆚 RD Congo", "Hora": "10:00 AM", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["CONGO", "RD CONGO", "RDC"]},
    {"Fecha": "01/07", "Rival 1": "BÉLGICA", "Rival 2": "SENEGAL", "Texto": "Bélgica 🆚 Senegal", "Hora": "02:00 PM", "Keys 1": ["BELGICA", "BÉLGICA", "BEL"], "Keys 2": ["SENEGAL", "SEN"]},
    {"Fecha": "01/07", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA", "Texto": "Estados Unidos 🆚 Bosnia", "Hora": "06:00 PM", "Keys 1": ["ESTADOS UNIDOS", "USA", "EEUU"], "Keys 2": ["BOSNIA", "HERZEGOVINA", "BOSNIA-HERZ"]},
    {"Fecha": "02/07", "Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria", "Hora": "01:00 PM", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["AUSTRIA", "AUT"]},
    {"Fecha": "02/07", "Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia", "Hora": "05:00 PM", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["CROACIA", "CRO"]},
    {"Fecha": "02/07", "Rival 1": "SUIZA", "Rival 2": "ARGELIA", "Texto": "Suiza 🆚 Argelia", "Hora": "09:00 PM", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["ARGELIA", "ALG"]},
    {"Fecha": "03/07", "Rival 1": "AUSTRALIA", "Rival 2": "EGIPTO", "Texto": "Australia 🆚 Egipto", "Hora": "12:00 PM", "Keys 1": ["AUSTRALIA", "AUS"], "Keys 2": ["EGIPTO", "EGY"]},
    {"Fecha": "03/07", "Rival 1": "ARGENTINA", "Rival 2": "CABO VERDE", "Texto": "Argentina 🆚 Cabo Verde", "Hora": "04:00 PM", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["CABO VERDE", "CPV"]},
    {"Fecha": "03/07", "Rival 1": "COLOMBIA", "Rival 2": "GHANA", "Texto": "Colombia 🆚 Ghana", "Hora": "07:30 PM", "Keys 1": ["COLOMBIA", "COL"], "Keys 2": ["GHANA", "GHA"]},
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
    
    try:
        respuesta = requests.get(url, timeout=15)
        if respuesta.status_code != 200:
            return None, None, partidos_hoy
            
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content), engine='openpyxl')
        nombres_pestañas = excel_file.sheet_names
        
        if "BASE" not in nombres_pestañas:
            return None, None, partidos_hoy
        df_base_raw = excel_file.parse("BASE", header=None, dtype=str)
        df_base = procesar_bloque_resumen(df_base_raw)
        if df_base is None:
            return None, None, partidos_hoy
            
        set_base = set(df_base["16vos"].dropna().apply(limpiar_texto))
        set_base.discard("")

        pestaña_cal = [n for n in nombres_pestañas if "CALENDARIO" in n.upper()]
        
        for p in partidos_hoy:
            p["Resultado"] = ""
            p["Ganador"] = ""
            
            if pestaña_cal:
                df_cal_excel = excel_file.parse(pestaña_cal[0], header=None, dtype=str)
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
                        p["Resultado"] = marcador_crudo
                        
                        goles = [int(g) for g in re.findall(r'\d+', marcador_crudo)]
                        if len(goles) >= 2:
                            if goles[0] > goles[1]:
                                p["Ganador"] = p["Rival 1"]
                            elif goles[1] > goles[0]:
                                p["Ganador"] = p["Rival 2"]
                            else:
                                if "PEN" in marcador_crudo.upper() and len(goles) >= 4:
                                    if goles[2] > goles[3]:
                                        p["Ganador"] = p["Rival 1"]
                                    else:
                                        p["Ganador"] = p["Rival 2"]
        
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
        
        return df_ranking, df_pronosticos_hoy, partidos_hoy

    except Exception as e:
        return None, None, partidos_hoy

# Ejecución
with st.spinner("🚀 Sincronizando archivo Excel..."):
    df_ranking, df_pronosticos_hoy, PARTIDOS_HOY = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, PARTIDOS_HOY)

if df_ranking is None:
    st.error("⚠️ Error crítico al descargar o procesar el archivo Excel.")
else:
    # Agregada la pestaña oculta de desarrollo al final de la lista
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
        
        # --- TABLA DE POSICIONES GENERAL UNIFICADA ---
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

    # --- PESTAÑA 4: DESARROLLO BRACKET (OCULTO/ENTORNO DE PRUEBAS) ---
    with tab_bracket_dev:
        st.warning("🛠️ **Espacio de Trabajo Técnico:** Esta pestaña sirve para ajustar los diseños antes de inyectarlos en la vista principal.")
        st.subheader("🌲 Estructura del Árbol de Eliminación Directa")
        
        # Grid responsive de columnas para simular las fases consecutivas
        col_16_izq, col_4_izq, col_semi_izq, col_final, col_semi_der, col_4_der, col_16_der = st.columns([2, 2, 2, 2.5, 2, 2, 2])
        
        # --- LADO IZQUIERDO: 16VOS ---
        with col_16_izq:
            st.markdown('<div class="bracket-phase">16vos de Final</div>', unsafe_allow_html=True)
            
            # Partido 1
            st.markdown("""
            <div class="bracket-match">
                <div class="bracket-team winner"><span>Francia</span> <span class="bracket-score">2</span></div>
                <div class="bracket-team loser"><span>Suecia</span> <span class="bracket-score">1</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Partido 2
            st.markdown("""
            <div class="bracket-match">
                <div class="bracket-team"><span>Costa de Marfil</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team"><span>Noruega</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)

        # --- LADO IZQUIERDO: CUARTOS ---
        with col_4_izq:
            st.markdown('<div class="bracket-phase">Cuartos</div>', unsafe_allow_html=True)
            st.write("") # Espaciador para centrar con las llaves de 16vos
            st.markdown("""
            <div class="bracket-match" style="margin-top: 15px;">
                <div class="bracket-team"><span>Francia</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team loser"><span>Ganador P2</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)

        # --- LADO IZQUIERDO: SEMIFINAL ---
        with col_semi_izq:
            st.markdown('<div class="bracket-phase">Semifinal</div>', unsafe_allow_html=True)
            st.write("")
            st.markdown("""
            <div class="bracket-match" style="margin-top: 40px;">
                <div class="bracket-team"><span>Por Definir</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team"><span>Por Definir</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)

        # --- CENTRO: GRAN FINAL ---
        with col_final:
            st.markdown('<div class="bracket-phase" style="background:#f59e0b; color:white;">🏆 GRAN FINAL</div>', unsafe_allow_html=True)
            st.write("")
            st.markdown("""
            <div class="bracket-match" style="margin-top: 70px; border: 2px solid #f59e0b;">
                <div class="bracket-team" style="font-size:15px;"><span>👑 Finalista Izq</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team" style="font-size:15px;"><span>👑 Finalista Der</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)

        # --- LADO DERECHO: SEMIFINAL ---
        with col_semi_der:
            st.markdown('<div class="bracket-phase">Semifinal</div>', unsafe_allow_html=True)
            st.write("")
            st.markdown("""
            <div class="bracket-match" style="margin-top: 40px;">
                <div class="bracket-team"><span>Por Definir</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team"><span>Por Definir</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)

        # --- LADO DERECHO: CUARTOS ---
        with col_4_der:
            st.markdown('<div class="bracket-phase">Cuartos</div>', unsafe_allow_html=True)
            st.write("")
            st.markdown("""
            <div class="bracket-match" style="margin-top: 15px;">
                <div class="bracket-team loser"><span>Ganador P3</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team"><span>México 🇲🇽</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)

        # --- LADO DERECHO: 16VOS ---
        with col_16_der:
            st.markdown('<div class="bracket-phase">16vos de Final</div>', unsafe_allow_html=True)
            
            # Partido 3
            st.markdown("""
            <div class="bracket-match">
                <div class="bracket-team"><span>Inglaterra</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team"><span>RD Congo</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Partido 4 (México)
            st.markdown("""
            <div class="bracket-match">
                <div class="bracket-team"><span>México 🇲🇽</span> <span class="bracket-score">-</span></div>
                <div class="bracket-team"><span>Ecuador</span> <span class="bracket-score">-</span></div>
            </div>
            """, unsafe_allow_html=True)
