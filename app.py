import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime, timedelta

st.set_page_config(page_title="Quiniela Fase Final", page_icon="⚽", layout="wide")

# ==============================================================================
# 1. CONFIGURACIÓN Y DATOS
# ==============================================================================
fecha_actual_mx = datetime.utcnow() - timedelta(hours=6)
fecha_formateada = fecha_actual_mx.strftime("%d/%m/%Y") 

CALENDARIO_COMPLETO = [
    # IZQUIERDA (P1-P8)
    {"Id": "P1", "Fecha": "29/06/2026", "Rival 1": "ALEMANIA", "Rival 2": "PARAGUAY", "Texto": "Alemania 🆚 Paraguay", "Hora": "14:00", "Keys 1": ["ALEMANIA", "GER"], "Keys 2": ["PARAGUAY", "PAR"]},
    {"Id": "P2", "Fecha": "30/06/2026", "Rival 1": "FRANCIA", "Rival 2": "SUECIA", "Texto": "Francia 🆚 Suecia", "Hora": "15:00", "Keys 1": ["FRANCIA", "FRA"], "Keys 2": ["SUECIA", "SUE"]},
    {"Id": "P3", "Fecha": "28/06/2026", "Rival 1": "SUDÁFRICA", "Rival 2": "CANADÁ", "Texto": "Sudáfrica 🆚 Canadá", "Hora": "13:00", "Keys 1": ["SUDAFRICA", "SUDÁFRICA", "RSA"], "Keys 2": ["CANADA", "CANADÁ", "CAN"]},
    {"Id": "P4", "Fecha": "29/06/2026", "Rival 1": "PAÍSES BAJOS", "Rival 2": "MARRUECOS", "Texto": "Países Bajos 🆚 Marruecos", "Hora": "20:00", "Keys 1": ["PAISES BAJOS", "NED"], "Keys 2": ["MARRUECOS", "MAR"]},
    {"Id": "P5", "Id_Img": "W83", "Fecha": "02/07/2026", "Rival 1": "PORTUGAL", "Rival 2": "CROACIA", "Texto": "Portugal 🆚 Croacia", "Hora": "17:00", "Keys 1": ["PORTUGAL", "POR"], "Keys 2": ["CROACIA", "CRO"]},
    {"Id": "P6", "Id_Img": "W84", "Fecha": "02/07/2026", "Rival 1": "ESPAÑA", "Rival 2": "AUSTRIA", "Texto": "España 🆚 Austria", "Hora": "13:00", "Keys 1": ["ESPAÑA", "ESP"], "Keys 2": ["AUSTRIA", "AUT"]},
    {"Id": "P7", "Id_Img": "W81", "Fecha": "01/07/2026", "Rival 1": "ESTADOS UNIDOS", "Rival 2": "BOSNIA", "Texto": "Estados Unidos 🆚 Bosnia", "Hora": "18:00", "Keys 1": ["ESTADOS UNIDOS", "USA"], "Keys 2": ["BOSNIA"]},
    {"Id": "P8", "Id_Img": "W82", "Fecha": "01/07/2026", "Rival 1": "BÉLGICA", "Rival 2": "SENEGAL", "Texto": "Bélgica 🆚 Senegal", "Hora": "14:00", "Keys 1": ["BELGICA", "BEL"], "Keys 2": ["SENEGAL", "SEN"]},
    # DERECHA (P9-P16)
    {"Id": "P9", "Fecha": "29/06/2026", "Rival 1": "BRASIL", "Rival 2": "JAPÓN", "Texto": "Brasil 🆚 Japón", "Hora": "11:00", "Keys 1": ["BRASIL", "BRA"], "Keys 2": ["JAPON", "JPN"]},
    {"Id": "P10", "Fecha": "30/06/2026", "Rival 1": "COSTA DE MARFIL", "Rival 2": "NORUEGA", "Texto": "Costa de Marfil 🆚 Noruega", "Hora": "11:00", "Keys 1": ["COSTA DE MARFIL", "CIV"], "Keys 2": ["NORUEGA", "NOR"]},
    {"Id": "P11", "Fecha": "30/06/2026", "Rival 1": "MÉXICO", "Rival 2": "ECUADOR", "Texto": "México 🇲🇽 🆚 Ecuador", "Hora": "19:00", "Keys 1": ["MEXICO", "MEX"], "Keys 2": ["ECUADOR", "ECU"]},
    {"Id": "P12", "Fecha": "01/07/2026", "Rival 1": "INGLATERRA", "Rival 2": "RD CONGO", "Texto": "Inglaterra 🆚 RD Congo", "Hora": "10:00", "Keys 1": ["INGLATERRA", "ENG"], "Keys 2": ["CONGO", "RDC"]},
    {"Id": "P13", "Id_Img": "W86", "Fecha": "03/07/2026", "Rival 1": "ARGENTINA", "Rival 2": "CABO VERDE", "Texto": "Argentina 🆚 Cabo Verde", "Hora": "16:00", "Keys 1": ["ARGENTINA", "ARG"], "Keys 2": ["CABO VERDE", "CPV"]},
    {"Id": "P14", "Id_Img": "W88", "Fecha": "03/07/2026", "Rival 1": "AUSTRALIA", "Rival 2": "EGIPTO", "Texto": "Australia 🆚 Egipto", "Hora": "12:00", "Keys 1": ["AUSTRALIA", "AUS"], "Keys 2": ["EGIPTO", "EGY"]},
    {"Id": "P15", "Id_Img": "W85", "Fecha": "02/07/2026", "Rival 1": "SUIZA", "Rival 2": "ARGELIA", "Texto": "Suiza 🆚 Argelia", "Hora": "21:00", "Keys 1": ["SUIZA", "SUI"], "Keys 2": ["ARGELIA", "ALG"]},
    {"Id": "P16", "Id_Img": "W87", "Fecha": "03/07/2026", "Rival 1": "COLOMBIA", "Rival 2": "GHANA", "Texto": "Colombia 🆚 Ghana", "Hora": "19:30", "Keys 1": ["COLOMBIA", "COL"], "Keys 2": ["GHANA", "GHA"]}
]

PARTIDOS_HOY = [partido for partido in CALENDARIO_COMPLETO if partido["Fecha"] == fecha_formateada]
SPREADSHEET_ID = "1FTUtzXd-ODXBB0QxIf-68FKf0ZQzVnWM"
ID_PESTAÑAS = ["HAAM", "CA", "HR", "JAG", "FB", "PM", "JLJF", "MASM", "CAVL", "AMG", "CAER", "VAVA", "JAMP", "VCBH", "JMG", "JV", "CAAM", "DSR", "SLO"]

# ==============================================================================
# 2. FUNCIONES DE PROCESAMIENTO
# ==============================================================================
def limpiar_texto(s):
    s = str(s).strip().upper()
    s = re.sub(r'[ÁÉÍÓÚ]', lambda m: {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U'}[m.group(0)], s)
    return s

@st.cache_data(ttl=60)
def cargar_y_procesar_todo(spreadsheet_id, pestañas_jugadores, partidos_hoy):
    url = f"https://drive.google.com/uc?export=download&id={spreadsheet_id}"
    bracket_data = {p["Id"]: {"Rival 1": p["Rival 1"], "Rival 2": p["Rival 2"], "G1": "-", "G2": "-", "Ganador": None} for p in CALENDARIO_COMPLETO}
    
    try:
        respuesta = requests.get(url, timeout=15)
        excel_file = pd.ExcelFile(io.BytesIO(respuesta.content))
        pestaña_cal = [n for n in excel_file.sheet_names if "CALENDARIO" in n.upper()]
        
        if pestaña_cal:
            df_cal = excel_file.parse(pestaña_cal[0], header=None).astype(str)
            for p in CALENDARIO_COMPLETO:
                # Búsqueda de fila por rivales
                fila = df_cal[df_cal.apply(lambda row: p["Rival 1"] in " ".join(row).upper() and p["Rival 2"] in " ".join(row).upper(), axis=1)]
                if not fila.empty and len(fila.columns) >= 4:
                    marcador = str(fila.iloc[0, 3])
                    nums = re.findall(r'\d+', marcador)
                    if len(nums) >= 2:
                        bracket_data[p["Id"]]["G1"], bracket_data[p["Id"]]["G2"] = nums[0], nums[1]
                        if int(nums[0]) > int(nums[1]): bracket_data[p["Id"]]["Ganador"] = p["Rival 1"]
                        elif int(nums[1]) > int(nums[0]): bracket_data[p["Id"]]["Ganador"] = p["Rival 2"]

        # Aquí iría el resto del procesamiento de ranking (simplificado para el ejemplo)
        return pd.DataFrame(), pd.DataFrame(), partidos_hoy, bracket_data
    except:
        return pd.DataFrame(), pd.DataFrame(), partidos_hoy, bracket_data

# ==============================================================================
# 3. RENDERIZADO DEL BRACKET (HTML ÚNICO)
# ==============================================================================
def render_bracket_html(BR):
    # Ayudante para obtener nombre de ganador o ID de la imagen
    def get_w(pid):
        ganador = BR[pid]["Ganador"]
        if ganador:
            res = ganador.title()
            return f"{res} 🇲🇽" if "MEXICO" in ganador.upper() else res
        return f"Ganador {pid}"

    # Construcción de las fases
    # 8vos Izq
    w74, w77 = get_w("P1"), get_w("P2")
    w73, w75 = get_w("P3"), get_w("P4")
    w83, w84 = get_w("P5"), get_w("P6")
    w81, w82 = get_w("P7"), get_w("P8")
    # 8vos Der
    w76, w78 = get_w("P9"), get_w("P10")
    w79, w80 = get_w("P11"), get_w("P12")
    w86, w88 = get_w("P13"), get_w("P14")
    w85, w87 = get_w("P15"), get_w("P16")

    html = f"""
    <style>
        .b-container {{
            display: grid;
            grid-template-columns: repeat(9, 1fr);
            gap: 10px;
            background-color: #0f172a;
            padding: 20px;
            border-radius: 15px;
            font-family: sans-serif;
            min-width: 1200px;
            overflow-x: auto;
        }}
        .b-column {{
            display: grid;
            grid-template-rows: repeat(8, 1fr);
            height: 800px;
        }}
        .b-match {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 5px;
        }}
        .b-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 8px;
            color: white;
            font-size: 11px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
        }}
        .b-team {{
            display: flex;
            justify-content: space-between;
            margin: 2px 0;
            padding: 2px 4px;
        }}
        .winner {{ color: #4ade80; font-weight: bold; background: rgba(74, 222, 128, 0.1); border-radius: 3px; }}
        .score {{ font-weight: bold; color: #94a3b8; }}
        .phase-title {{
            text-align: center;
            color: #64748b;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
            grid-column: span 1;
        }}
        .final-card {{ border: 2px solid #f59e0b; background: #2d1b04; }}
    </style>

    <div class="b-container">
        <div class="phase-title">16vos</div><div class="phase-title">8vos</div><div class="phase-title">4tos</div><div class="phase-title">Semi</div>
        <div class="phase-title" style="color:#f59e0b">Final</div>
        <div class="phase-title">Semi</div><div class="phase-title">4tos</div><div class="phase-title">8vos</div><div class="phase-title">16vos</div>

        <div class="b-column">
            {m_html(BR['P1'])}{m_html(BR['P2'])}{m_html(BR['P3'])}{m_html(BR['P4'])}
            {m_html(BR['P5'])}{m_html(BR['P6'])}{m_html(BR['P7'])}{m_html(BR['P8'])}
        </div>

        <div class="b-column">
            {w_html(w74, w77, 2)}{w_html(w73, w75, 2)}{w_html(w83, w84, 2)}{w_html(w81, w82, 2)}
        </div>

        <div class="b-column">
            {w_html("W89", "W90", 4)}{w_html("W93", "W94", 4)}
        </div>

        <div class="b-column">
            {w_html("W97", "W98", 8)}
        </div>

        <div class="b-column">
            <div style="grid-row: span 8; display: flex; flex-direction: column; justify-content: center;">
                <div class="b-card final-card">
                    <div class="b-team"><span>W101</span><span class="score">-</span></div>
                    <div style="height:1px; background:#444; margin:4px 0;"></div>
                    <div class="b-team"><span>W102</span><span class="score">-</span></div>
                </div>
            </div>
        </div>

        <div class="b-column">
            {w_html("W99", "W100", 8)}
        </div>

        <div class="b-column">
            {w_html("W91", "W92", 4)}{w_html("W95", "W96", 4)}
        </div>

        <div class="b-column">
            {w_html(w76, w78, 2)}{w_html(w79, w80, 2)}{w_html(w86, w88, 2)}{w_html(w85, w87, 2)}
        </div>

        <div class="b-column">
            {m_html(BR['P9'])}{m_html(BR['P10'])}{m_html(BR['P11'])}{m_html(BR['P12'])}
            {m_html(BR['P13'])}{m_html(BR['P14'])}{m_html(BR['P15'])}{m_html(BR['P16'])}
        </div>
    </div>
    """
    return html

def m_html(m):
    r1, r2 = m["Rival 1"].title(), m["Rival 2"].title()
    if "Mexico" in r1.upper() or "MÉXICO" in r1.upper(): r1 += " 🇲🇽"
    if "Mexico" in r2.upper() or "MÉXICO" in r2.upper(): r2 += " 🇲🇽"
    c1 = "winner" if m["Ganador"] == m["Rival 1"] else ""
    c2 = "winner" if m["Ganador"] == m["Rival 2"] else ""
    return f"""
    <div class="b-match">
        <div class="b-card">
            <div class="b-team {c1}"><span>{r1}</span><span class="score">{m['G1']}</span></div>
            <div class="b-team {c2}"><span>{r2}</span><span class="score">{m['G2']}</span></div>
        </div>
    </div>"""

def w_html(t1, t2, span):
    return f"""
    <div style="grid-row: span {span}; display: flex; flex-direction: column; justify-content: center; padding: 5px;">
        <div class="b-card">
            <div class="b-team"><span>{t1}</span></div>
            <div style="height:1px; background:#334155; margin:4px 0;"></div>
            <div class="b-team"><span>{t2}</span></div>
        </div>
    </div>"""

# ==============================================================================
# 4. EJECUCIÓN
# ==============================================================================
df_r, df_p, PARTIDOS_HOY, BRACKET = cargar_y_procesar_todo(SPREADSHEET_ID, ID_PESTAÑAS, PARTIDOS_HOY)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Clasificación", "🔮 Pronósticos", "👤 Participantes", "🏗️ En construcción"])

with tab4:
    st.markdown("### 🏗️ Bracket del Mundial 2026")
    st.components.v1.html(render_bracket_html(BRACKET), height=900, scrolling=True)
