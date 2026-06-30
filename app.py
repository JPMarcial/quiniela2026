import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Quiniela Mundial 2026 - Fase Final",
    page_icon="🏆",
    layout="wide"
)

# Estilos visuales premium
st.markdown("""
    <style>
    .main-title { font-size: 38px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 5px; }
    .subtitle { font-size: 16px; color: #64748B; text-align: center; margin-bottom: 30px; }
    .metric-card { background-color: #F8FAFC; padding: 15px; border-radius: 10px; border-left: 5px solid #3B82F6; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .podium-1 { font-size: 24px; font-weight: bold; color: #D97706; }
    .podium-2 { font-size: 20px; font-weight: bold; color: #475569; }
    .podium-3 { font-size: 18px; font-weight: bold; color: #B45309; }
    </style>
""", unsafe_allow_html=True)

# Enlace de descarga directa de tu Drive
FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# ==============================================================================
# 2. LÓGICA DE EXTRACCIÓN FILTRADA
# ==============================================================================
def obtener_clasificados_reales(df_resultados):
    """
    Determina qué equipos han clasificado en la hoja de RESULTADOS.
    Revisa los marcadores de los partidos jugados en filas consecutivas.
    """
    clasificados = set()
    
    # Recorremos la hoja buscando partidos (filas de 2 en 2 para Local y Visitante)
    try:
        for i in range(0, len(df_resultados) - 1, 3): # Brinca de 3 en 3 por los espacios en blanco
            fila_local = df_resultados.iloc[i]
            fila_vis = df_resultados.iloc[i+1]
            
            equipo_local = str(fila_local.iloc[1]).strip()
            equipo_vis = str(fila_vis.iloc[1]).strip()
            
            goles_local = fila_local.iloc[2]
            goles_vis = fila_vis.iloc[2]
            
            # Si hay goles registrados (celdas no vacías)
            if pd.notna(goles_local) and pd.notna(goles_vis):
                if int(goles_local) > int(goles_vis):
                    clasificados.add(equipo_local)
                elif int(goles_vis) > int(goles_local):
                    clasificados.add(equipo_vis)
                    
        # También barremos columnas de rondas posteriores (Octavos, Cuartos, etc.)
        # Si escribes un equipo en columnas de la derecha (ej. columnas D, F, H, J), se añade como clasificado confirmado
        for col_idx in range(3, len(df_resultados.columns)):
            valores = df_resultados.iloc[:, col_idx].dropna().astype(str).str.strip()
            for val in valores:
                if len(val) > 2 and not val.startswith('W') and not val.startswith('L') and val.upper() not in ['NOMBRE', 'FASE', 'RESULTADOS']:
                    clasificados.add(val)
    except:
        pass
        
    return clasificados

def obtener_predicciones_jugador(df_jugador):
    """
    Extrae únicamente las predicciones de las fases avanzadas 
    (las columnas donde el participante coloca a sus clasificados de Octavos en adelante).
    """
    predicciones = set()
    # Ignoramos las primeras 3 columnas (A, B, C) que contienen los equipos fijos de 16vos y sus goles
    if len(df_jugador.columns) > 3:
        for col_idx in range(3, len(df_jugador.columns)):
            valores = df_jugador.iloc[:, col_idx].dropna().astype(str).str.strip()
            for val in valores:
                if len(val) > 2 and not val.startswith('W') and not val.startswith('L') and val.upper() not in ['NOMBRE', 'FASE']:
                    predicciones.add(val)
    return predicciones

@st.cache_data(ttl=30)
def cargar_y_calcular_quiniela():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        if respuesta.status_code != 200:
            return None, "Error de conexión con Drive."
            
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        
        # 1. Obtener ganadores reales confirmados
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        equipos_reales = obtener_clasificados_reales(df_res)
        
        lista_ranking = []
        detalles_participantes = {}
        
        pestanas_participantes = [p for p in xls.sheet_names if p.upper() not in ['RESULTADOS', 'MURO', 'CALENDARIO'] and p.strip() != '']
        
        for p in pestanas_participantes:
            df_part = pd.read_excel(xls, sheet_name=p, header=None)
            
            # Nombre completo del participante (está en la celda B2)
            nombre_completo = p
            try:
                posible_nombre = str(df_part.iloc[1, 1]).strip()
                if posible_nombre and posible_nombre != 'nan' and posible_nombre != '':
                    nombre_completo = posible_nombre
            except:
                pass
            
            # Obtener solo lo que el jugador puso en las rondas avanzadas
            equipos_predichos = obtener_predicciones_jugador(df_part)
            
            # Comparar contra los clasificados oficiales de la app
            aciertos = equipos_predichos.intersection(equipos_reales)
            puntos = len(aciertos)
            
            lista_ranking.append({
                "Iniciales": p,
                "Participante": nombre_completo,
                "Aciertos Totales": puntos
            })
            
            detalles_participantes[p] = {
                "nombre": nombre_completo,
                "predicciones": equipos_predichos,
                "aciertos": aciertos
            }
            
        df_ranking = pd.DataFrame(lista_ranking)
        if not df_ranking.empty:
            df_ranking = df_ranking.sort_values(by="Aciertos Totales", ascending=False).reset_index(drop=True)
            df_ranking.index += 1
            
        return df_ranking, detalles_participantes, equipos_reales
        
    except Exception as e:
        return None, f"Error: {str(e)}", set()

# ==============================================================================
# 3. INTERFAZ GRÁFICA
# ==============================================================================
st.markdown('<div class="main-title">🏆 Quiniela Mundial 2026 🏆</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Seguimiento en Vivo - Fase de Eliminación Directa</div>', unsafe_allow_html=True)

df_ranking, detalles, clasificados_globales = cargar_y_calcular_quiniela()

if df_ranking is not None:
    # Mostrar bloques de podio dinámicos
    col1, col2, col3 = st.columns(3)
    with col1:
        if len(df_ranking) >= 1:
            st.markdown(f'<div class="metric-card"><p style="margin:0; font-size:14px; color:#64748B;">🥇 1ER LUGAR</p><p class="podium-1">{df_ranking.iloc[0]["Participante"]}</p><h2 style="margin:0; color:#1E3A8A;">{df_ranking.iloc[0]["Aciertos Totales"]} Pts</h2></div>', unsafe_allow_html=True)
    with col2:
        if len(df_ranking) >= 2:
            st.markdown(f'<div class="metric-card" style="border-left-color: #64748B;"><p style="margin:0; font-size:14px; color:#64748B;">🥈 2DO LUGAR</p><p class="podium-2">{df_ranking.iloc[1]["Participante"]}</p><h2 style="margin:0; color:#475569;">{df_ranking.iloc[1]["Aciertos Totales"]} Pts</h2></div>', unsafe_allow_html=True)
    with col3:
        if len(df_ranking) >= 3:
            st.markdown(f'<div class="metric-card" style="border-left-color: #B45309;"><p style="margin:0; font-size:14px; color:#64748B;">🥉 3ER LUGAR</p><p class="podium-3">{df_ranking.iloc[2]["Participante"]}</p><h2 style="margin:0; color:#B45309;">{df_ranking.iloc[2]["Aciertos Totales"]} Pts</h2></div>', unsafe_allow_html=True)

    st.write("---")

    left_col, right_col = st.columns([5, 4])
    
    with left_col:
        st.subheader("📊 Tabla General de Posiciones")
        st.dataframe(
            df_ranking, 
            use_container_width=True,
            column_config={
                "Iniciales": st.column_config.TextColumn("ID"),
                "Participante": st.column_config.TextColumn("Nombre"),
                "Aciertos Totales": st.column_config.ProgressColumn("Puntos", min_value=0, max_value=32, format="%d pts")
            }
        )
        
        with st.expander("⚽ Ver equipos clasificados registrados en el sistema"):
            st.write(", ".join(sorted(list(clasificados_globales))) if clasificados_globales else "Aún no se registran partidos jugados o clasificados en la pestaña RESULTADOS.")
        
    with right_col:
        st.subheader("🔍 Auditoría de Aciertos")
        participante_sel = st.selectbox(
            "Selecciona un participante para auditar:",
            options=df_ranking["Iniciales"].tolist(),
            format_func=lambda x: f"{x} - {detalles[x]['nombre']}"
        )
        
        if participante_sel:
            p_info = detalles[participante_sel]
            st.write(f"**Estatus de:** {p_info['nombre']}")
            
            if p_info['aciertos']:
                st.success(f"✔️ **Aciertos en fases finales ({len(p_info['aciertos'])}):**")
                st.write(", ".join(sorted(list(p_info['aciertos']))))
            else:
                st.warning("0 aciertos registrados al momento.")
                
            with st.expander("Ver árbol completo de clasificados elegidos por este participante"):
                st.write(", ".join(sorted(list(p_info['predicciones']))) if p_info['predicciones'] else "No se leyeron elecciones en las rondas avanzadas.")
else:
    st.error("Error al conectar con la plantilla de Google Drive. Verifica el formato de las pestañas.")
