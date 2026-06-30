import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS PARA DIBUJAR LAS LÍNEAS DE LA LLAVE
# ==============================================================================
st.set_page_config(page_title="Quiniela 2026 - Bracket Real", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    
    /* Contenedor del Torneo en Flexbox */
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
    
    /* Columnas de Rondas */
    .bracket-round {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        flex-grow: 1;
        width: 280px;
        min-width: 260px;
        padding: 0 10px;
        position: relative;
    }
    
    /* Estructura de cada Partido */
    .bracket-matchup {
        display: flex;
        flex-direction: column;
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        position: relative;
        z-index: 2;
    }
    
    .matchup-header {
        font-size: 9px;
        font-weight: 700;
        color: #64748B;
        background-color: #F1F5F9;
        padding: 3px 8px;
        border-bottom: 1px solid #E2E8F0;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    
    /* Filas de Equipos */
    .bracket-team {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 10px;
        font-size: 12px;
        border-bottom: 1px solid #F1F5F9;
    }
    .bracket-team:last-child { border-bottom: none; }
    
    .team-name-text { font-weight: 700; color: #334155; }
    .team-winner-official { color: #10B981 !important; font-weight: 800; }
    
    /* Chips de Iniciales de los Participantes (Legibles) */
    .avatar-list { display: flex; flex-wrap: wrap; gap: 3px; max-width: 120px; }
    .user-chip {
        background-color: #DBEAFE;
        color: #1E40AF;
        font-size: 9px;
        font-weight: 800;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #93C5FD;
    }

    /* ==========================================================================
       CONECTORES REALES: LÍNEAS DEL ÁRBOL
       ========================================================================== */
    /* Línea saliente horizontal del partido actual hacia la derecha */
    .bracket-round:not(:last-child) .bracket-matchup::after {
        content: "";
        position: absolute;
        right: -10px;
        top: 50%;
        width: 10px;
        height: 2px;
        background-color: #94A3B8;
        z-index: 1;
    }

    /* Línea vertical de unión para partidos pares/impares en la siguiente columna */
    .bracket-round:first-child .bracket-matchup:nth-child(odd)::before {
        content: "";
        position: absolute;
        right: -10px;
        top: 50%;
        width: 2px;
        height: 65px; /* Distancia aproximada entre cajas */
        background-color: #94A3B8;
        z-index: 1;
    }
    
    /* Encabezados de Fase */
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

# URL pública de descarga del archivo de quiniela
FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# Lista para el mapeo estricto
PAISES_VALIDOS = {
    "alemania", "paraguay", "francia", "suecia", "sudafrica", "canada", 
    "paises bajos", "marruecos", "portugal", "croacia", "españa", "austria", 
    "estados unidos", "bosnia-herz", "bosnia", "belgica", "senegal", "brasil", 
    "japon", "costa marfil", "costa de marfil", "noruega", "mexico", "ecuador", 
    "inglaterra", "congo", "argentina", "cabo verde", "australia", "egipto", 
    "suiza", "argelia", "colombia", "ghana"
}

def obtener_iniciales(nombre):
    partes = nombre.split()
    if len(partes) >= 2: return (partes[0][0] + partes[1][0]).upper()
    return nombre[:2].upper()

def extraer_lista_por_columna(df, num_columna):
    """Extrae secuencialmente los equipos de una columna específica del árbol."""
    lista = []
    if len(df.columns) > num_columna:
        for val in df.iloc[:, num_columna].dropna().astype(str).str.strip():
            if val.lower() in PAISES_VALIDOS:
                lista.append(val.lower())
    return lista

# Cruces Fijos de 16vos sacados de la plantilla original
CRUCES_INICIALES = [
    ("Alemania", "Paraguay"), ("Francia", "Suecia"), ("Sudáfrica", "Canadá"), ("Países Bajos", "Marruecos"),
    ("Portugal", "Croacia"), ("España", "Austria"), ("Estados Unidos", "Bosnia-Herz"), ("Bélgica", "Senegal"),
    ("Brasil", "Japón"), ("Costa Marfil", "Noruega"), ("México", "Ecuador"), ("Inglaterra", "Congo"),
    ("Argentina", "Cabo Verde"), ("Australia", "Egipto"), ("Suiza", "Argelia"), ("Colombia", "Ghana")
]

@st.cache_data(ttl=10)
def procesar_toda_la_data():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        
        # 1. ACTUALIZACIÓN AUTOMÁTICA DESDE RESULTADOS REALES
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        resultados_reales = {
            "r16vos": extraer_lista_por_columna(df_res, 6), # Columna G
            "octavos": extraer_lista_por_columna(df_res, 8), # Columna I
            "cuartos": extraer_lista_por_columna(df_res, 10) # Columna K
        }
        
        # 2. Extracción de Quinielas de Usuarios
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
            
            p_pronos = {
                "r16vos": extraer_lista_por_columna(df_part, 6),
                "octavos": extraer_lista_por_columna(df_part, 8),
                "cuartos": extraer_lista_por_columna(df_part, 10)
            }
            
            # Cálculo dinámico de puntajes por aciertos reales
            puntos = len(set(p_pronos["r16vos"]).intersection(set(resultados_reales["r16vos"]))) + \
                     len(set(p_pronos["octavos"]).intersection(set(resultados_reales["octavos"]))) * 2
            
            participantes_datos.append({
                "nombre": nombre_mostrar, "iniciales": obtener_iniciales(nombre_mostrar),
                "pronosticos": p_pronos, "puntos": puntos
            })
            
        return participantes_datos, resultados_reales, None
    except Exception as e:
        return [], {}, f"Error de sincronización: {str(e)}"

# ==============================================================================
# 3. CONSTRUCCIÓN DE LA INTERFAZ DE USUARIO
# ==============================================================================
st.markdown('<div class="main-title">🏆 Árbol del Torneo en Tiempo Real 🏆</div>', unsafe_allow_html=True)

participantes, reales, error = procesar_toda_la_data()

if error:
    st.error(error)
elif participantes:
    
    # Renderizador del árbol usando el contenedor CSS inyectado
    html_bracket = '<div class="tournament-bracket">'
    
    # --------------------------------------------------------------------------
    # FASE 1: 16VOS DE FINAL (Fija de base, marca ganadores oficiales de Columna G)
    # --------------------------------------------------------------------------
    html_bracket += '<div class="bracket-round"><div class="phase-title">16vos de Final</div>'
    for idx, (loc, vis) in enumerate(CRUCES_INICIALES):
        # Verificar cuál avanzó según tu pestaña RESULTADOS
        win_loc = "team-winner-official" if loc.lower() in reales["r16vos"] else ""
        win_vis = "team-winner-official" if vis.lower() in reales["r16vos"] else ""
        
        # Buscar qué iniciales votaron por cada uno en esta casilla
        v_loc = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if loc.lower() in p["pronosticos"]["r16vos"]])
        v_vis = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if vis.lower() in p["pronosticos"]["r16vos"]])
        
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
    # FASE 2: OCTAVOS DE FINAL (Se alimenta en cascada de los resultados oficiales de la R1)
    # --------------------------------------------------------------------------
    html_bracket += '<div class="bracket-round"><div class="phase-title">Octavos de Final</div>'
    
    # Generamos los 8 partidos de octavos agrupando los ganadores en parejas correlativas
    for idx in range(0, 16, 2):
        # Trae de manera automática el ganador oficial desde el Excel
        eq1 = reales["r16vos"][idx].upper() if idx < len(reales["r16vos"]) else "Por definir"
        eq2 = reales["r16vos"][idx+1].upper() if (idx+1) < len(reales["r16vos"]) else "Por definir"
        
        win_eq1 = "team-winner-official" if eq1.lower() in reales["octavos"] else ""
        win_eq2 = "team-winner-official" if eq2.lower() in reales["octavos"] else ""
        
        v_eq1 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq1.lower() in p["pronosticos"]["octavos"]])
        v_eq2 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq2.lower() in p["pronosticos"]["octavos"]])
        
        html_bracket += f"""
        <div class="bracket-matchup">
            <div class="matchup-header">Octavos M{ (idx//2)+1 }</div>
            <div class="bracket-team">
                <span class="team-name-text {win_eq1}">{eq1.title()}</span>
                <div class="avatar-list">{v_eq1}</div>
            </div>
            <div class="bracket-team">
                <span class="team-name-text {win_eq2}">{eq2.title()}</span>
                <div class="avatar-list">{v_eq2}</div>
            </div>
        </div>
        """
    html_bracket += '</div>'
    
    # --------------------------------------------------------------------------
    # FASE 3: CUARTOS DE FINAL (Se alimenta en cascada del resultado oficial de Octavos)
    # --------------------------------------------------------------------------
    html_bracket += '<div class="bracket-round"><div class="phase-title">Cuartos de Final</div>'
    for idx in range(0, 8, 2):
        eq1 = reales["octavos"][idx].upper() if idx < len(reales["octavos"]) else "Por definir"
        eq2 = reales["octavos"][idx+1].upper() if (idx+1) < len(reales["octavos"]) else "Por definir"
        
        v_eq1 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq1.lower() in p["pronosticos"]["cuartos"]])
        v_eq2 = "".join([f'<span class="user-chip">{p["iniciales"]}</span>' for p in participantes if eq2.lower() in p["pronosticos"]["cuartos"]])
        
        html_bracket += f"""
        <div class="bracket-matchup">
            <div class="matchup-header">Cuartos C{ (idx//2)+1 }</div>
            <div class="bracket-team">
                <span class="team-name-text">{eq1.title()}</span>
                <div class="avatar-list">{v_eq1}</div>
            </div>
            <div class="bracket-team">
                <span class="team-name-text">{eq2.title()}</span>
                <div class="avatar-list">{v_eq2}</div>
            </div>
        </div>
        """
    html_bracket += '</div>'
    
    html_bracket += '</div>'
    
    # Renderizar el HTML final sanitizado dentro de Streamlit
    st.write(html_bracket, unsafe_allow_html=True)
