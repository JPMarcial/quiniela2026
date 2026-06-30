import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Quiniela Mundial 2026",
    page_icon="🏆",
    layout="wide"
)

st.markdown("""
    <style>
    .main-title { font-size: 36px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 5px; }
    .subtitle { font-size: 16px; color: #64748B; text-align: center; margin-bottom: 30px; }
    .metric-card { background-color: #F8FAFC; padding: 15px; border-radius: 10px; border-left: 5px solid #3B82F6; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .podium-1 { font-size: 22px; font-weight: bold; color: #D97706; }
    .podium-2 { font-size: 18px; font-weight: bold; color: #475569; }
    .podium-3 { font-size: 17px; font-weight: bold; color: #B45309; }
    </style>
""", unsafe_allow_html=True)

# Enlace de descarga directa de tu Google Drive
FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# ==============================================================================
# 2. LÓGICA DE EXTRACCIÓN (COLUMNA G EN ADELANTE = ÍNDICE 6)
# ==============================================================================
def extraer_arbol_ganadores(df):
    """
    Recorre el DataFrame desde la Columna G (Índice 6) hacia la derecha.
    Recolecta los nombres de los equipos elegidos en las llaves de avance.
    """
    equipos_seleccionados = set()
    
    # Índice 6 corresponde a la Columna G
    for col_idx in range(6, len(df.columns)):
        # Convertimos todo a texto limpio, eliminando espacios y celdas vacías
        valores = df.iloc[:, col_idx].dropna().astype(str).str.strip()
        
        for val in valores:
            val_upper = val.upper()
            
            # Filtros de seguridad para ignorar textos de llaves o encabezados del Mundial
            if (len(val) > 2 and 
                not val_upper.startswith('W') and 
                not val_upper.startswith('L') and 
                not val.isdigit() and
                "VS" not in val_upper and
                "MUNDIAL" not in val_upper and
                val_upper not in ['NOMBRE', 'FASE', 'RESULTADOS', 'VS']):
                
                # Almacenamos en minúsculas para comparar de forma exacta libre de errores de dedo
                equipos_seleccionados.add(val.lower())
                
    return equipos_seleccionados

@st.cache_data(ttl=15)
def calcular_quiniela():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        if respuesta.status_code != 200:
            return None, "Error al conectar con Google Drive.", set()
            
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        
        # 1. GANADORES REALES (Columna G en adelante de la hoja RESULTADOS)
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        ganadores_reales = extraer_arbol_ganadores(df_res)
        
        lista_ranking = []
        detalles_participantes = {}
        
        # Filtro de pestañas de juego
        hojas_excluidas = ['RESULTADOS', 'MURO', 'CALENDARIO']
        pestanas_jugadores = [p for p in xls.sheet_names if p.upper() not in hojas_excluidas and p.strip() != '']
        
        # 2. EVALUAR CADA PARTICIPANTE
        for p in pestanas_jugadores:
            df_part = pd.read_excel(xls, sheet_name=p, header=None)
            
            # Intentar buscar el nombre real del jugador en las celdas superiores (B1 o B2)
            nombre_mostrar = p
            try:
                for fila in [0, 1]:
                    for col in [0, 1]:
                        celda = str(df_part.iloc[fila, col]).strip()
                        if celda and celda.lower() != 'nan' and len(celda) > 3 and celda.upper() != 'NOMBRE':
                            nombre_mostrar = celda
                            break
            except:
                pass
            
            # Extraer árbol de pronósticos del jugador (Columna G en adelante)
            pronosticos_jugador = extraer_arbol_ganadores(df_part)
            
            # Intersección: ¿A cuáles de la columna G en adelante les atinó?
            aciertos = pronosticos_jugador.intersection(ganadores_reales)
            puntos = len(aciertos)
            
            lista_ranking.append({
                "ID": p,
                "Nombre": nombre_mostrar,
                "Aciertos": puntos
            })
            
            detalles_participantes[p] = {
                "nombre": nombre_mostrar,
                "pronosticos": pronosticos_jugador,
                "aciertos": aciertos
            }
            
        df_ranking = pd.DataFrame(lista_ranking)
        if not df_ranking.empty:
            df_ranking = df_ranking.sort_values(by="Aciertos", ascending=False).reset_index(drop=True)
            df_ranking.index += 1
            
        return df_ranking, detalles_participantes, ganadores_reales
        
    except Exception as e:
        return None, f"Error en procesamiento: {str(e)}", set()

# ==============================================================================
# 3. INTERFAZ GRÁFICA
# ==============================================================================
st.markdown('<div class="main-title">🏆 Quiniela Mundial 2026 🏆</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Evaluación Directa de Llaves (Columna G en adelante)</div>', unsafe_allow_html=True)

df_ranking, detalles, reales_globales = calcular_quiniela()

if df_ranking is not None:
    # Podio de Líderes
    col1, col2, col3 = st.columns(3)
    with col1:
        if len(df_ranking) >= 1:
            st.markdown(f'<div class="metric-card"><p style="margin:0; font-size:12px; color:#64748B;">🥇 1ER LUGAR</p><p class="podium-1">{df_ranking.iloc[0]["Nombre"]}</p><h3 style="margin:0; color:#1E3A8A;">{df_ranking.iloc[0]["Aciertos"]} Pts</h3></div>', unsafe_allow_html=True)
    with col2:
        if len(df_ranking) >= 2:
            st.markdown(f'<div class="metric-card" style="border-left-color: #64748B;"><p style="margin:0; font-size:12px; color:#64748B;">🥈 2DO LUGAR</p><p class="podium-2">{df_ranking.iloc[1]["Nombre"]}</p><h3 style="margin:0; color:#475569;">{df_ranking.iloc[1]["Aciertos"]} Pts</h3></div>', unsafe_allow_html=True)
    with col3:
        if len(df_ranking) >= 3:
            st.markdown(f'<div class="metric-card" style="border-left-color: #B45309;"><p style="margin:0; font-size:12px; color:#64748B;">🥉 3ER LUGAR</p><p class="podium-3">{df_ranking.iloc[2]["Nombre"]}</p><h3 style="margin:0; color:#B45309;">{df_ranking.iloc[2]["Aciertos"]} Pts</h3></div>', unsafe_allow_html=True)

    st.write("---")

    left_col, right_col = st.columns([5, 4])
    
    with left_col:
        st.subheader("📊 Tabla General de Aciertos")
        st.dataframe(
            df_ranking, 
            use_container_width=True,
            column_config={
                "ID": st.column_config.TextColumn("Hoja"),
                "Nombre": st.column_config.TextColumn("Participante"),
                "Aciertos": st.column_config.NumberColumn("Puntos", format="%d pts")
            }
        )
        
        with st.expander("⚽ Ver ganadores oficiales asentados (Columna G en adelante)"):
            if reales_globales:
                st.write(", ".join(sorted([r.title() for r in reales_globales])))
            else:
                st.info("Aún no se escriben ganadores oficiales en la columna G de RESULTADOS.")
        
    with right_col:
        st.subheader("🔍 Auditoría de Pronósticos")
        participante_sel = st.selectbox(
            "Selecciona un participante:",
            options=df_ranking["ID"].tolist(),
            format_func=lambda x: f"{x} - {detalles[x]['nombre']}"
        )
        
        if participante_sel:
            p_info = detalles[participante_sel]
            
            if p_info['aciertos']:
                st.success(f"✔️ **Aciertos en playoffs ({len(p_info['aciertos'])}):**")
                st.write(", ".join(sorted([a.title() for a in p_info['aciertos']])))
            else:
                st.warning("0 aciertos al momento frente a los resultados asentados.")
                
            with st.expander("Ver árbol completo elegido por este participante (Columna G+)"):
                if p_info['pronosticos']:
                    st.write(", ".join(sorted([pr.title() for pr in p_info['pronosticos']])))
                else:
                    st.write("No se detectaron elecciones en las columnas de juego.")
else:
    st.error("Error al procesar el archivo. Asegúrate de que las hojas mantengan la columna G como el inicio del árbol.")
