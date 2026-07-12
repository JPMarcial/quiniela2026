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
    {"Id": "P24", "Fecha": "07/07/2026", "Rival 1": "ARGENTINA", "Rival 2": "EGIPTO", "Texto": "Argentina 🆚 Egipto", "Hora": "10:00", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["EGIPTO", "EGY"]},

    # --- CUARTOS DE FINAL ---
    {"Id": "P25", "Fecha": "09/07/2026", "Rival 1": "FRANCIA", "Rival 2": "MARRUECOS", "Texto": "Francia 🆚 Marruecos", "Hora": "14:00", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["MARRUECOS", "MAR"]},
    {"Id": "P26", "Fecha": "10/07/2026", "Rival 1": "ESPAÑA", "Rival 2": "BÉLGICA", "Texto": "España 🆚 Bélgica", "Hora": "13:00", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["BELGICA", "BÉLGICA", "BEL"]},
    {"Id": "P27", "Fecha": "11/07/2026", "Rival 1": "NORUEGA", "Rival 2": "INGLATERRA", "Texto": "Noruega 🆚 Inglaterra", "Hora": "15:00", "Keys 1": ["NORUEGA", "NOR"], "Keys 2": ["INGLATERRA", "ENG"]},
    {"Id": "P28", "Fecha": "11/07/2026", "Rival 1": "ARGENTINA", "Rival 2": "SUIZA", "Texto": "Argentina 🆚 Suiza", "Hora": "19:00", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["SUIZA", "SUI"]},

    # --- SEMIFINALES ---
    {"Id": "P29", "Fecha": "14/07/2026", "Rival 1": "FRANCIA", "Rival 2": "ESPAÑA", "Texto": "Francia 🆚 España", "Hora": "13:00", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["ESPAÑA", "ESP"]},
    {"Id": "P30", "Fecha": "15/07/2026", "Rival 1": "INGLATERRA", "Rival 2": "ARGENTINA", "Texto": "Inglaterra 🆚 Argentina", "Hora": "13:00", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["ARGENTINA", "ARG"]}
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
    s = re.sub(r'[^A-Z0-9 ]', '', s)
    return s

def extraer_columna_fija(df_raw, col_indice, fila_inicio=54, fila_fin=90):
    if df_raw is None or df_raw.shape[0] < fila_inicio or df_raw.shape[1] <= col_indice:
        return set()
    try:
        bloque = df_raw.iloc[fila_inicio:fila_fin, col_indice].dropna().astype(str).str.strip()
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
    
    desglose_16vos_lista = []
    desglose_8vos_lista = []
    desglose_4tos_lista = []
    desglose_semis_lista = []
    
    partidos_fecha = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_consulta]
    
    bracket_data = {}
    for p in CALENDARIO_COMPLETO:
        bracket_data[p["Id"]] = {"Rival 1": p["Rival 1"], "Rival 2": p["Rival 2"], "Goles 1": "-", "Goles 2": "-", "Ganador": "Por Definir"}
    
    try:
        respuesta = requests.get(url, timeout=15)
        if respuesta.status_code != 200: return None, None, partidos_fecha, bracket_data, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content), engine='openpyxl')
        nombres_pestañas = excel_file.sheet_names
        
        # Cargar matriz de la hoja BASE para calificar aciertos globales
        if "BASE" in nombres_pestañas:
            df_base_raw = excel_file.parse("BASE", header=None, dtype=str)
            set_base_16vos = extraer_columna_fija(df_base_raw, 1)
            set_base_8vos = extraer_columna_fija(df_base_raw, 3)
            set_base_4tos = extraer_columna_fija(df_base_raw, 5)
            
            # Semifinalistas reales (F55-F58)
            set_base_semis = extraer_columna_fija(df_base_raw, 5, fila_inicio=54, fila_fin=58)
            # Finalistas reales (J55-J56)
            set_base_final = extraer_columna_fija(df_base_raw, 9, fila_inicio=54, fila_fin=56)
        else:
            set_base_16vos, set_base_8vos, set_base_4tos, set_base_semis, set_base_final = set(), set(), set(), set(), set()

        lista_base_16vos_ordenada = sorted(list(set_base_16vos))
        lista_base_8vos_ordenada = sorted(list(set_base_8vos))
        lista_base_4tos_ordenada = sorted(list(set_base_4tos))
        lista_base_semis_ordenada = sorted(list(set_base_semis))

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
            fases_jugador = {"16vos": set(), "8vos": set(), "4tos": set(), "semis": set(), "final": set()}
            
            if pestaña in nombres_pestañas:
                df_jugador_raw = excel_file.parse(pestaña, header=None, dtype=str)
                nombre_real = obtener_nombre_real(df_jugador_raw, pestaña)
                
                fases_jugador["16vos"] = extraer_columna_fija(df_jugador_raw, 1)
                fases_jugador["8vos"] = extraer_columna_fija(df_jugador_raw, 3)
                fases_jugador["4tos"] = extraer_columna_fija(df_jugador_raw, 5)
                
                # Semifinalistas elegidos por persona en F55-F58
                fases_jugador["semis"] = extraer_columna_fija(df_jugador_raw, 5, fila_inicio=54, fila_fin=58)
                # Finalistas elegidos en J55-J56
                fases_jugador["final"] = extraer_columna_fija(df_jugador_raw, 9, fila_inicio=54, fila_fin=56)

            elecciones_fecha = {"Participante": nombre_real}
            auditoria_16vos = {"Participante": nombre_real}
            auditoria_8vos = {"Participante": nombre_real}
            auditoria_4tos = {"Participante": nombre_real}
            auditoria_semis = {"Participante": nombre_real}
            
            if df_jugador_raw is not None:
                interseccion_16vos = fases_jugador["16vos"].intersection(set_base_16vos)
                interseccion_8vos = fases_jugador["8vos"].intersection(set_base_8vos)
                interseccion_4tos = fases_jugador["4tos"].intersection(set_base_4tos)
                interseccion_semis = fases_jugador["semis"].intersection(set_base_semis)
                interseccion_final = fases_jugador["final"].intersection(set_base_final)
                
                puntos_16vos = len(interseccion_16vos)
                puntos_8vos = len(interseccion_8vos)
                puntos_4tos = len(interseccion_4tos)
                puntos_semis = len(interseccion_semis)
                puntos_final = len(interseccion_final)
                
                puntos_totales = puntos_16vos + puntos_8vos + puntos_4tos + puntos_semis + puntos_final
                
                datos_ranking.append({
                    "Participante": nombre_real, 
                    "Aciertos Totales": puntos_totales,
                    "Aciertos 16vos": puntos_16vos,
                    "Aciertos 8vos": puntos_8vos,
                    "Aciertos 4tos": puntos_4tos,
                    "Aciertos Semis": puntos_semis
                })
                
                # Desgloses individuales
                auditoria_16vos["Aciertos 16vos"] = puntos_16vos
                for equipo_base in lista_base_16vos_ordenada:
                    auditoria_16vos[equipo_base] = "✅ Sí" if equipo_base in fases_jugador["16vos"] else "❌ No"
                
                auditoria_8vos["Aciertos 8vos"] = puntos_8vos
                for equipo_base in lista_base_8vos_ordenada:
                    auditoria_8vos[equipo_base] = "✅ Sí" if equipo_base in fases_jugador["8vos"] else "❌ No"
                
                auditoria_4tos["Aciertos 4tos"] = puntos_4tos
                for equipo_base in lista_base_4tos_ordenada:
                    auditoria_4tos[equipo_base] = "✅ Sí" if equipo_base in fases_jugador["4tos"] else "❌ No"
                
                auditoria_semis["Aciertos Semis"] = puntos_semis
                for equipo_base in lista_base_semis_ordenada:
                    auditoria_semis[equipo_base] = "✅ Sí" if equipo_base in fases_jugador["semis"] else "❌ No"
                
                # Mapeo exhaustivo para la pestaña "Pronósticos por Fecha"
                for p in partidos_fecha:
                    num_partido = int(p["Id"].replace("P", ""))
                    if num_partido <= 16:
                        set_busqueda = fases_jugador["16vos"]
                    elif num_partido <= 24:
                        set_busqueda = fases_jugador["8vos"]
                    elif num_partido <= 28:
                        set_busqueda = fases_jugador["4tos"]
                    elif num_partido <= 30:
                        set_busqueda = fases_jugador["semis"]
                    else:
                        set_busqueda = fases_jugador["final"]
                    
                    encontrado = "Ninguno"
                    for pronostico in list(set_busqueda):
                        if any(limpiar_texto(k) in pronostico for k in p["Keys 1"]): 
                            encontrado = p["Rival 1"].title()
                            break
                        elif any(limpiar_texto(k) in pronostico for k in p["Keys 2"]): 
                            encontrado = p["Rival 2"].title()
                            break
                    
                    if p.get("Ganador") and p["Ganador"] != "Por Definir":
                        elecciones_fecha[p["Texto"]] = f"✅ {encontrado}" if limpiar_texto(p["Ganador"]) == limpiar_texto(encontrado) else f"• {encontrado}"
                    else: 
                        elecciones_fecha[p["Texto"]] = encontrado
            else:
                datos_ranking.append({"Participante": nombre_real, "Aciertos Totales": 0, "Aciertos 16vos": 0, "Aciertos 8vos": 0, "Aciertos 4tos": 0, "Aciertos Semis": 0})
                auditoria_16vos["Aciertos 16vos"] = 0
                auditoria_8vos["Aciertos 8vos"] = 0
                auditoria_4tos["Aciertos 4tos"] = 0
                auditoria_semis["Aciertos Semis"] = 0
                for equipo_base in lista_base_16vos_ordenada: auditoria_16vos[equipo_base] = "❌ No"
                for equipo_base in lista_base_8vos_ordenada: auditoria_8vos[equipo_base] = "❌ No"
                for equipo_base in lista_base_4tos_ordenada: auditoria_4tos[equipo_base] = "❌ No"
                for equipo_base in lista_base_semis_ordenada: auditoria_semis[equipo_base] = "❌ No"
                for p in partidos_fecha: elecciones_fecha[p["Texto"]] = "Sin Datos"
                
            desglose_16vos_lista.append(auditoria_16vos)
            desglose_8vos_lista.append(auditoria_8vos)
            desglose_4tos_lista.append(auditoria_4tos)
            desglose_semis_lista.append(auditoria_semis)
            if partidos_fecha: 
                pronosticos_fecha_lista.append(elecciones_fecha)
                
        df_ranking = pd.DataFrame(datos_ranking).sort_values(by="Aciertos Totales", ascending=False).drop_duplicates(subset=["Participante"]).reset_index(drop=True)
        df_pronosticos_fecha = pd.DataFrame(pronosticos_fecha_lista).reset_index(drop=True) if pronosticos_fecha_lista else pd.DataFrame(columns=["Participante"])
        
        df_desglose_16vos = pd.DataFrame(desglose_16vos_lista).sort_values(by="Aciertos 16vos", ascending=False).reset_index(drop=True)
        df_desglose_8vos = pd.DataFrame(desglose_8vos_lista).sort_values(by="Aciertos 8vos", ascending=False).reset_index(drop=True)
        df_desglose_4tos = pd.DataFrame(desglose_4tos_lista).sort_values(by="Aciertos 4tos", ascending=False).reset_index(drop=True)
        df_desglose_semis = pd.DataFrame(desglose_semis_lista).sort_values(by="Aciertos Semis", ascending=False).reset_index(drop=True)
        
        # Reordenar columnas para dejar Participante y Conteo al inicio
        if not df_desglose_16vos.empty:
            cols_16 = ["Participante", "Aciertos 16vos"] + [c for c in df_desglose_16vos.columns if c not in ["Participante", "Aciertos 16vos"]]
            df_desglose_16vos = df_desglose_16vos[cols_16]
        if not df_desglose_8vos.empty:
            cols_8 = ["Participante", "Aciertos 8vos"] + [c for c in df_desglose_8vos.columns if c not in ["Participante", "Aciertos 8vos"]]
            df_desglose_8vos = df_desglose_8vos[cols_8]
        if not df_desglose_4tos.empty:
            cols_4 = ["Participante", "Aciertos 4tos"] + [c for c in df_desglose_4tos.columns if c not in ["Participante", "Aciertos 4tos"]]
            df_desglose_4tos = df_desglose_4tos[cols_4]
        if not df_desglose_semis.empty:
            cols_se = ["Participante", "Aciertos Semis"] + [c for c in df_desglose_semis.columns if c not in ["Participante", "Aciertos Semis"]]
            df_desglose_semis = df_desglose_semis[cols_se]

        return df_ranking, df_pronosticos_fecha, partidos_fecha, bracket_data, df_desglose_16vos, df_desglose_8vos, df_desglose_4tos, df_desglose_semis
    except Exception: 
        return None, None, partidos_fecha, bracket_data, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ==============================================================================
# INTERFAZ GRÁFICA DE STREAMLIT
# ==============================================================================
FECHAS_DISPONIBLES = sorted(list(set(p["Fecha"] for p in CALENDARIO_COMPLETO)), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
default_idx = FECHAS_DISPONIBLES.index(fecha_formateada) if fecha_formateada in FECHAS_DISDESP else 0

if "BASE" not in st.session_state:
    with st.spinner("🚀 Sincronizando datos del torneo..."):
        df_ranking, _, _, BRACKET, df_desglose_16vos, df_desglose_8vos, df_desglose_4tos, df_desglose_semis = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, FECHAS_DISPONIBLES[default_idx])

if df_ranking is not None:
    tab_principal, tab_desglose, tab_hoy, tab_bracket_dev = st.tabs(["📊 Clasificación", "🔍 Desglose de Aciertos", "🔮 Pronósticos por Fecha", "Bracket"])

    # --- PESTAÑA PRINCIPAL ---
    with tab_principal:
        st.subheader("📅 Partidos del Día")
        PARTIDOS_DEL_DIA_LISTA = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_formateada]
        
        if not PARTIDOS_DEL_DIA_LISTA: 
            st.info(f"⚽ No hay partidos agendados para el día de hoy, sal a que te dé el aire ({fecha_formateada}).")
            
            col_img1, col_img2, col_img3 = st.columns([2, 1.5, 2])
            with col_img2:
                st.image("01.jpg", caption=". . . ", width=350)
                
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
        st.markdown("### 🔍 Tabla General de Equipos Colocados")
        st.write("")
        
        tab_16vos, tab_8vos, tab_4tos, tab_semis = st.tabs(["🏆 Ronda de 16vos", "⚡ Ronda de 8vos", "🏅 Ronda de Cuartos", "🔥 Semifinales"])
        
        def estilar_tabla_aciertos(val):
            if val == "✅ Sí":
                return 'background-color: #d1fae5; color: #065f46; font-weight: bold; text-align: center;'
            elif val == "❌ No":
                return 'background-color: #fee2e2; color: #991b1b; text-align: center;'
            return ''

        with tab_16vos:
            st.caption("Conteo de aciertos basado en los equipos clasificados reales de la Columna B (Hoja BASE)")
            if df_desglose_16vos.empty or len(df_desglose_16vos.columns) <= 2:
                st.info("No hay datos de 16vos disponibles aún.")
            else:
                df_estilado_16 = df_desglose_16vos.style.map(estilar_tabla_aciertos, subset=df_desglose_16vos.columns[2:])
                st.dataframe(df_estilado_16, use_container_width=True, hide_index=True)
                
        with tab_8vos:
            st.caption("Conteo de aciertos basado en los equipos clasificados reales de la Columna D (Hoja BASE)")
            if df_desglose_8vos.empty or len(df_desglose_8vos.columns) <= 2:
                st.info("No hay datos de Octavos disponibles aún.")
            else:
                df_estilado_8 = df_desglose_8vos.style.map(estilar_tabla_aciertos, subset=df_desglose_8vos.columns[2:])
                st.dataframe(df_estilado_8, use_container_width=True, hide_index=True)

        with tab_4tos:
            st.caption("Conteo de aciertos basado en los equipos clasificados reales de la Columna F (Hoja BASE)")
            if df_desglose_4tos.empty or len(df_desglose_4tos.columns) <= 2:
                st.info("No hay datos de Cuartos de Final disponibles aún.")
            else:
                df_estilado_4 = df_desglose_4tos.style.map(estilar_tabla_aciertos, subset=df_desglose_4tos.columns[2:])
                st.dataframe(df_estilado_4, use_container_width=True, hide_index=True)

        with tab_semis:
            st.caption("Conteo de aciertos basado en los 4 semifinalistas reales de las celdas F55-F58 (Hoja BASE)")
            if df_desglose_semis.empty or len(df_desglose_semis.columns) <= 2:
                st.info("No hay datos de Semifinales disponibles aún.")
            else:
                df_estilado_semi = df_desglose_semis.style.map(estilar_tabla_aciertos, subset=df_desglose_semis.columns[2:])
                st.dataframe(df_estilado_semi, use_container_width=True, hide_index=True)

    # --- PESTAÑA PRONÓSTICOS ---
    with tab_hoy:
        st.markdown("### 🔮 Consulta de Pronósticos")
        sub_tabs_fechas = st.tabs([f"📅 {f}" for f in FECHAS_DISPONIBLES])
        
        for idx_f, fecha_select in enumerate(FECHAS_DISPONIBLES):
            with sub_tabs_fechas[idx_f]:
                _, df_pronosticos_fecha, partidos_fecha, _, _, _, _, _ = cargar_y_procesar_todo_el_torneo(SPREADSHEET_ID, ID_PESTAÑAS, fecha_select)
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

        w = {f"P{i}": get_w(f"P{i}") for i in range(1, 31)}

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
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P25", BRACKET)}</div>
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P26", BRACKET)}</div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P29", BRACKET)}</div>
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
                <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P30", BRACKET)}</div>
            </div>

            <div class="b-column">
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P27", BRACKET)}</div>
                <div style="grid-row: span 4; display: flex; flex-direction: column; justify-content: center;">{render_match_html("P28", BRACKET)}</div>
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
