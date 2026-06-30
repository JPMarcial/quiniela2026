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
    .main-title { font-size: 34px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 5px; }
    .subtitle { font-size: 15px; color: #64748B; text-align: center; margin-bottom: 25px; }
    .section-title { font-size: 20px; font-weight: 700; color: #0F172A; margin-top: 15px; margin-bottom: 5px; }
    .chip { padding: 4px 10px; background-color: #F1F5F9; border-radius: 12px; font-size: 12px; font-weight: 600; color: #334155; margin-right: 5px; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

PAISES_VALIDOS = {
    "alemania", "paraguay", "francia", "suecia", "sudafrica", "canada", 
    "paises bajos", "marruecos", "portugal", "croacia", "españa", "austria", 
    "estados unidos", "bosnia-herz", "bosnia", "belgica", "senegal", "brasil", 
    "japon", "costa marfil", "costa de marfil", "noruega", "mexico", "ecuador", 
    "inglaterra", "congo", "argentina", "cabo verde", "australia", "egipto", 
    "suiza", "argelia", "colombia", "ghana"
}

def obtener_iniciales(nombre):
    """Genera iniciales compactas para usar como micro-avatar en la matriz (ej. Juan Perez -> JP)"""
    partes = nombre.split()
    if len(partes) >= 2:
        return (partes[0][0] + partes[1][0]).upper()
    return nombre[:2].upper()

def extraer_arbol_ganadores(df):
    equipos_seleccionados = set()
    for col_idx in range(6, len(df.columns)):
        valores = df.iloc[:, col_idx].dropna().astype(str).str.strip()
        for val in valores:
            val_lower = val.lower()
            if val_lower in PAISES_VALIDOS:
                equipos_seleccionados.add(val_lower)
    return equipos_seleccionados

@st.cache_data(ttl=15)
def calcular_quiniela():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        if respuesta.status_code != 200:
            return None, None, "Error al conectar con Google Drive.", {}
            
        xls = pd.ExcelFile(BytesIO(respuesta.content))
        df_res = pd.read_excel(xls, sheet_name='RESULTADOS', header=None)
        ganadores_reales = extraer_arbol_ganadores(df_res)
        
        lista_ranking = []
        datos_matriz = []
        
        hojas_excluidas = ['RESULTADOS', 'MURO', 'CALENDARIO']
        pestanas_jugadores = [p for p in xls.sheet_names if p.upper() not in hojas_excluidas and p.strip() != '']
        
        for p in pestanas_jugadores:
            df_part = pd.read_excel(xls, sheet_name=p, header=None)
            
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
            
            pronosticos_jugador = extraer_arbol_ganadores(df_part)
            aciertos = pronosticos_jugador.intersection(ganadores_reales)
            
            lista_ranking.append({
                "Posición": 0,
                "Hoja": p,
                "Participante": nombre_mostrar,
                "Iniciales": obtener_iniciales(nombre_mostrar),
                "Puntos Totales": len(aciertos)
            })
            
            for pais in PAISES_VALIDOS:
                datos_matriz.append({
                    "Participante": nombre_mostrar,
                    "Iniciales": obtener_iniciales(nombre_mostrar),
                    "Equipo": pais.title(),
                    "Estatus Real": "🟢 Avanzó" if pais in ganadores_reales else "⏳ Activo/Eliminado",
                    "Lo Eligió": pais in pronosticos_jugador
                })
            
        df_ranking = pd.DataFrame(lista_ranking)
        if not df_ranking.empty:
            df_ranking = df_ranking.sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
            df_ranking["Posición"] = df_ranking.index + 1
            
        df_matriz_completa = pd.DataFrame(datos_matriz)
        return df_ranking, df_matriz_completa, ganadores_reales, None
    except Exception as e:
        return None, None, set(), f"Error: {str(e)}"

# ==============================================================================
# INTERFAZ GRÁFICA COMPLEMENTARIA
# ==============================================================================
st.markdown('<div class="main-title">🏆 Quiniela Mundial 2026</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Vistas de Posiciones e Iniciales en la Llave</div>', unsafe_allow_html=True)

df_ranking, df_matriz, reales_globales, error = calcular_quiniela()

if error:
    st.error(error)
elif df_ranking is not None:
    
    # --------------------------------------------------------------------------
    # OPCIÓN 1: TABLA GENERAL DE POSICIONES
    # --------------------------------------------------------------------------
    st.markdown('<div class="section-title">📊 Opción 1: Tabla General de Posiciones</div>', unsafe_allow_html=True)
    st.dataframe(
        df_ranking[["Posición", "Participante", "Iniciales", "Puntos Totales"]], 
        use_container_width=True,
        column_config={
            "Posición": st.column_config.NumberColumn("Pos", format="%d°"),
            "Participante": st.column_config.TextColumn("Nombre"),
            "Iniciales": st.column_config.TextColumn("Avatar / Inicial"),
            "Puntos Totales": st.column_config.ProgressColumn("Aciertos", min_value=0, max_value=32, format="%d pts")
        },
        hide_index=True
    )
    
    st.write("---")

    # --------------------------------------------------------------------------
    # OPCIÓN 2: MATRIZ CON MICRO-AVATARES / INICIALES DENTRO DE LA LLAVE
    # --------------------------------------------------------------------------
    st.markdown('<div class="section-title">🔍 Opción 2: Distribución de Elecciones por País (Micro-Avatares)</div>', unsafe_allow_html=True)
    st.write("Mira rápidamente qué iniciales compartes o quiénes son tus rivales directos en cada equipo clasificado:")

    # Agrupamos por equipo para generar los bloques de "Quiénes lo eligieron" usando las iniciales
    df_elegidos = df_matriz[df_matriz["Lo Eligió"] == True]
    
    resumen_equipos = []
    for equipo, grupo in df_elegidos.groupby("Equipo"):
        estatus = grupo["Estatus Real"].iloc[0]
        # Creamos una cadena de iniciales para mostrar como micro-avatares
        iniciales_list = list(grupo["Iniciales"].unique())
        nombres_completos = ", ".join(grupo["Participante"].unique())
        
        resumen_equipos.append({
            "Equipo / País": equipo,
            "Estatus en Vivo": estatus,
            "Cantidad de Apuestas": len(iniciales_list),
            "Quiénes lo tienen en su Llave (Iniciales)": "  |  ".join([f"[{ini}]" for ini in iniciales_list]),
            "Nombres": nombres_completos
        })
        
    df_resumen_vis = pd.DataFrame(resumen_equipos)
    
    if not df_resumen_vis.empty:
        # Ordenar para poner arriba los países que tienen estatus de haber avanzado
        df_resumen_vis = df_resumen_vis.sort_values(by=["Estatus en Vivo", "Cantidad de Apuestas"], ascending=[False, False])
        
        st.dataframe(
            df_resumen_vis,
            use_container_width=True,
            column_config={
                "Equipo / País": st.column_config.TextColumn("País"),
                "Estatus en Vivo": st.column_config.TextColumn("Estatus"),
                "Cantidad de Apuestas": st.column_config.NumberColumn("Popularidad (Votos)"),
                "Quiénes lo tienen en su Llave (Iniciales)": st.column_config.TextColumn("Participantes (Micro-Avatares)"),
                "Nombres": st.column_config.TextColumn("Nombres Completos")
            },
            hide_index=True
        )
    else:
        st.info("No se encontraron elecciones registradas aún.")
