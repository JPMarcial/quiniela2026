import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (DISEÑO BRACKET CON CONECTORES)
# ==============================================================================
st.set_page_config(page_title="Quiniela 2026 - Bracket Real", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    
    .tournament-bracket {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: stretch;
        width: 100%;
        background-color: #F8FAFC;
        padding: 20px;
        border-radius: 12px;
        overflow-x: auto;
    }
    
    .bracket-round {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        flex-grow: 1;
        width: 290px;
        min-width: 270px;
        padding: 0 12px;
        position: relative;
    }
    
    .bracket-matchup {
        display: flex;
        flex-direction: column;
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        margin: 12px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        position: relative;
        z-index: 2;
    }
    
    .matchup-header {
        font-size: 10px;
        font-weight: 700;
        color: #64748B;
        background-color: #F1F5F9;
        padding: 4px 8px;
        border-bottom: 1px solid #E2E8F0;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    
    .bracket-team {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 10px;
        font-size: 12px;
        border-bottom: 1px solid #F1F5F9;
    }
    .bracket-team:last-child { border-bottom: none; }
    
    .team-name-text { font-weight: 700; color: #334155; }
    .team-winner-official { color: #10B981 !important; font-weight: 800; }
    
    .avatar-list { display: flex; flex-wrap: wrap; gap: 3px; max-width: 130px; }
    .user-chip {
        background-color: #DBEAFE;
        color: #1E40AF;
        font-size: 9px;
        font-weight: 800;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #93C5FD;
    }

    /* Líneas de conexión del árbol */
    .bracket-round:not(:last-child) .bracket-matchup::after {
        content: "";
        position: absolute;
        right: -12px;
        top: 50%;
        width: 12px;
        height: 2px;
        background-color: #94A3B8;
        z-index: 1;
    }
    
    .phase-title {
        text-align: center;
        font-weight: 800;
        font-size: 14px;
        color: #1E3A8A;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 5px;
        margin-bottom: 15px;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

CRUCES_INICIALES = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal"),
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

def obtener_iniciales(nombre):
    partes = nombre.split()
    if len(partes) >= 2: return (partes[0][0] + partes[1][0]).upper()
    return nombre[:2].upper()

def extraer_set_columna(df, num_columna):
    """Extrae un set de palabras en minúsculas de una columna para búsquedas rápidas."""
    if len(df.columns) > num_columna:
        return set(df.iloc[:, num_columna].dropna().astype(str).str.strip().str.lower())
    return set()

@st.cache_data(ttl=10)
def procesar_toda_la_data():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        
        # 1. LEER RESULTADOS OFICIALES EN SETS DE CONTROL
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        res_r1 = extraer_set_columna(df_res, 6)   # Columna G
        res_r2 = extraer_set_columna(df_res, 8)   # Columna I
        res_r3 = extraer_set_columna(df_res, 10)  # Columna K
        
        # 2. RESOLVER LLAVE REAL EN CASCADA POSICIONAL
        # Slots R16vos (16 equipos ganadores fijos en su posición de llave)
        ganadores_r1 = []
        for loc, vis in CRUCES_INICIALES:
            if loc.lower() in res_r1: ganadores_r1.append(loc)
            elif vis.lower() in res_r1: ganadores_r1.append(vis)
            else: ganadores_r1.append("Por Definir")
            
        # Slots Octavos (8 equipos ganadores de los cruces de Octavos)
        ganadores_r2 = []
        for i in range(0, 16, 2):
            eq1, eq2 = ganadores_r1[i], ganadores_r1[i+1]
            if eq1 != "Por Definir" and eq1.lower() in res_r2: ganadores_r2.append(eq1)
            elif eq2 != "Por Definir" and eq2.lower() in res_r2: ganadores_r2.append(eq2)
            else: ganadores_r2.append("Por Definir")

        reales_mapeados = {
            "r16vos_ganadores": ganadores_r1,
            "octavos_ganadores": ganadores_r2,
            "raw_r1": res_r1, "raw_r2": res_r2, "raw_r3": res_r3
        }
        
        # 3. EXTRAER QUINIELAS DE JUGADORES
        participantes_datos = []
        hojas_excluidas = ['RESULTADOS', 'MURO', 'CALENDARIO']
        pestanas_jugadores = [p for p in xls.sheet_names if p.upper() not in hojas_excluidas and p.strip() != '']
        
        for p in pestanas_jugadores:
            df_part = pd.read_excel(xls, sheet_name=p, header=None)
            nombre_mostrar = p
            try:
                celda = str(df_part.iloc[1, 1]).strip()
                if celda and celda.lower() != 'nan' and len(celda) > 3: nombre_mostrar = celda
            except: pass
            
            p_r1 = extraer_set_columna(df_part, 6)
            p_r2 = extraer_set_columna(df_part, 8)
            p_r3 = extraer_set_columna(df_part, 10)
            
            # Puntos calculados con intersección real
            puntos = len(p_r1.intersection(res_r1)) + len(p_r2.intersection(res_r2)) * 2
            
            participantes_datos.append({
                "nombre": nombre_mostrar, "iniciales": obtener_iniciales(nombre_mostrar),
                "pronosticos": {"r1": p_r1, "r2": p_r2, "r3": p_r3}, "puntos": puntos
            })
            
        return participantes_datos, reales_mapeados, None
    except Exception as e:
        return [], {}, f"Error de sincronización: {str(e)}"

# ==============================================================================
# 4. RENDERIZADO DE LA INTERFAZ DE USUARIO
# ==============================================================================
st.markdown('<div class="main-title">🏆 Árbol del Torneo en Tiempo Real 🏆</div>', unsafe_allow_html=True)

participantes, reales, error = procesar_toda_la_data()

if error:
    st.error(error)
elif participantes:
    
    html_bracket = '<div class="tournament-bracket">'
    
    # --------------------------------------------------------------------------
    # COLUMNA 1: 16VOS DE FINAL
    # --------------------------------------------------------------------------
    html_bracket += '<div class="bracket-round"><div class="phase-title">16vos de Final</div>'
    for idx, (loc, vis) in enumerate(CRUCES_INICIALES):
        win_loc = "team-winner-official" if loc.lower() in reales["raw_r1"] else ""
        win_vis = "team-winner-official" if vis.lower() in reales["raw_r1"] else ""
        
        v_loc = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if loc.lower() in p["pronosticos"]["r1"]])
        v_vis = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if vis.lower() in p["pronosticos"]["r1"]])
        
        html_bracket += f"""
        <div class="bracket-matchup">
            <div class="matchup-header">Partido {idx+1}</div>
            <div class="bracket-team">
                <span class="team-name-text {win_loc}">{loc}</span>
                <div class="avatar-list">{v_loc}</div>
            </div>
            <div class="bracket-team">
                <span class="team-name-text {win_vis}">{vis}</span>
                <div class="avatar-list">{v_vis}</div>
            </div>
        </div>
        """
    html_bracket += '</div>'
    
    # --------------------------------------------------------------------------
    # COLUMNA 2: OCTAVOS DE FINAL (Mapeo por slots posicionales correctos)
    # --------------------------------------------------------------------------
    html_bracket += '<div class="bracket-round"><div class="phase-title">Octavos de Final</div>'
    for idx in range(0, 16, 2):
        eq1 = reales["r16vos_ganadores"][idx]
        eq2 = reales["r16vos_ganadores"][idx+1]
        
        win_eq1 = "team-winner-official" if eq1 != "Por Definir" and eq1.lower() in reales["raw_r2"] else ""
        win_eq2 = "team-winner-official" if eq2 != "Por Definir" and eq2.lower() in reales["raw_r2"] else ""
        
        v_eq1 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq1 != "Por Definir" and eq1.lower() in p["pronosticos"]["r2"]])
        v_eq2 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq2 != "Por Definir" and eq2.lower() in p["pronosticos"]["r2"]])
        
        html_bracket += f"""
        <div class="bracket-matchup">
            <div class="matchup-header">Octavos M{ (idx//2)+1 }</div>
            <div class="bracket-team">
                <span class="team-name-text {win_eq1}">{eq1}</span>
                <div class="avatar-list">{v_eq1}</div>
            </div>
            <div class="bracket-team">
                <span class="team-name-text {win_eq2}">{eq2}</span>
                <div class="avatar-list">{v_eq2}</div>
            </div>
        </div>
        """
    html_bracket += '</div>'
    
    # --------------------------------------------------------------------------
    # COLUMNA 3: CUARTOS DE FINAL (Mapeo por slots posicionales desde Octavos)
    # --------------------------------------------------------------------------
    html_bracket += '<div class="bracket-round"><div class="phase-title">Cuartos de Final</div>'
    for idx in range(0, 8, 2):
        eq1 = reales["octavos_ganadores"][idx]
        eq2 = reales["octavos_ganadores"][idx+1]
        
        v_eq1 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq1 != "Por Definir" and eq1.lower() in p["pronosticos"]["r3"]])
        v_eq2 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq2 != "Por Definir" and eq2.lower() in p["pronosticos"]["r3"]])
        
        html_bracket += f"""
        <div class="bracket-matchup">
            <div class="matchup-header">Cuartos C{ (idx//2)+1 }</div>
            <div class="bracket-team">
                <span class="team-name-text">{eq1}</span>
                <div class="avatar-list">{v_eq1}</div>
            </div>
            <div class="bracket-team">
                <span class="team-name-text">{eq2}</span>
                <div class="avatar-list">{v_eq2}</div>
            </div>
        </div>
        """
    html_bracket += '</div>'
    
    html_bracket += '</div>'
    st.write(html_bracket, unsafe_allow_html=True)
