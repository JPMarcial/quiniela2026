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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para una interfaz limpia, deportiva y profesional
st.markdown("""
    <style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 16px;
        color: #64748B;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .podium-1 { font-size: 24px; font-weight: bold; color: #D97706; }
    .podium-2 { font-size: 20px; font-weight: bold; color: #475569; }
    .podium-3 { font-size: 18px; font-weight: bold; color: #B45309; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ENLACE DIRECTO A GOOGLE DRIVE
# ==============================================================================
# Convertimos el enlace compartido en un link de descarga directa para openpyxl/pandas
FILE_ID = "1NSjLaSgIodnTtk2iFQFvlBkw7wOyqAOe"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"

# ==============================================================================
# 3. FUNCIONES DE PROCESAMIENTO DE DATOS
# ==============================================================================
def extraer_equipos_de_matriz(df):
    """
    Analiza la estructura de la hoja tipo llave del Mundial para extraer 
    todos los nombres de equipos únicos ingresados (predichos o reales).
    Ignora códigos de llaves tipo 'W74', 'W89', vacíos, textos fijos, etc.
    """
    equipos_detectados = set()
    palabras_ignorar = {
        'NOMBRE', 'WF', 'LF', 'MUNDIAL', 'XXIII', 'USA/MEX/CAN', '2026', 
        'FASE', 'HOJA1', 'RESULTADOS', 'ALEMANIA', 'FRANCIA', 'BRASIL', 
        'ARGENTINA', 'PORTUGAL', 'ESPAÑA', 'INGLATERRA', 'MEXICO'
    }
    
    for col in df.columns:
        valores = df[col].dropna().astype(str).str.strip()
        for val in valores:
            if (len(val) > 1 and 
                not val.startswith('W') and 
                not val.startswith('L') and 
                not val.replace(" ", "").isalnum() == False and
                val.upper() not in palabras_ignorar):
                equipos_detectados.add(val)
                
    return equipos_detectados

@st.cache_data(ttl=60)  # Actualiza los datos de Drive automáticamente cada 60 segundos
def cargar_y_calcular_quiniela():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=12)
        if respuesta.status_code != 200:
            return None, "No se pudo conectar correctamente con Google Drive."
            
        contenido_excel = respuesta.content
        xls = pd.ExcelFile(BytesIO(contenido_excel))
        pestanas = xls.sheet_names
        
        if 'RESULTADOS' not in pestanas:
            return None, "No se encontró la pestaña 'RESULTADOS' en el archivo de Google Drive."
            
        # 1. Obtener los equipos reales clasificados de la pestaña RESULTADOS
        df_resultados = pd.read_excel(xls, sheet_name='RESULTADOS')
        equipos_reales = extraer_equipos_de_matriz(df_resultados)
        
        # 2. Iterar por cada participante
        lista_ranking = []
        detalles_participantes = {}
        
        # Filtrar pestañas que no corresponden a participantes
        pestanas_participantes = [p for p in pestanas if p.upper() not in ['RESULTADOS', 'MURO', 'CALENDARIO'] and p.strip() != '']
        
        for p in pestanas_participantes:
            df_part = pd.read_excel(xls, sheet_name=p)
            
            # Obtener el nombre completo si está definido en la cabecera
            nombre_completo = p
            if not df_part.empty and df_part.columns[0] == 'NOMBRE':
                posible_nombre = str(df_part.iloc[0, 1]).strip()
                if posible_nombre and posible_nombre != 'nan':
                    nombre_completo = posible_nombre
            
            equipos_predichos = extraer_equipos_de_matriz(df_part)
            
            # Intersección: Equipos predichos que coinciden con los reales
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
            
        return df_ranking, detalles_participantes
        
    except Exception as e:
        return None, f"Error al procesar el archivo desde la nube: {str(e)}"

# ==============================================================================
# 4. INTERFAZ DE USUARIO PRINCIPAL
# ==============================================================================
st.markdown('<div class="main-title">🏆 Quiniela Mundial 2026 🏆</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Seguimiento en Vivo - Fase de Eliminación Directa</div>', unsafe_allow_html=True)

df_ranking, detalles = cargar_y_calcular_quiniela()

if df_ranking is not None and not df_ranking.empty:
    
    # Podio de Líderes
    col1, col2, col3 = st.columns(3)
    with col1:
        if len(df_ranking) >= 1:
            st.markdown(f"""
            <div class="metric-card">
                <p style="margin:0; font-size:14px; color:#64748B;">🥇 1ER LUGAR</p>
                <p class="podium-1">{df_ranking.iloc[0]['Participante']}</p>
                <h2 style="margin:0; color:#1E3A8A;">{df_ranking.iloc[0]['Aciertos Totales']} Pts</h2>
            </div>
            """, unsafe_allow_html=True)
            
    with col2:
        if len(df_ranking) >= 2:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #64748B;">
                <p style="margin:0; font-size:14px; color:#64748B;">🥈 2DO LUGAR</p>
                <p class="podium-2">{df_ranking.iloc[1]['Participante']}</p>
                <h2 style="margin:0; color:#475569;">{df_ranking.iloc[1]['Aciertos Totales']} Pts</h2>
            </div>
            """, unsafe_allow_html=True)
            
    with col3:
        if len(df_ranking) >= 3:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #B45309;">
                <p style="margin:0; font-size:14px; color:#64748B;">🥉 3ER LUGAR</p>
                <p class="podium-3">{df_ranking.iloc[2]['Participante']}</p>
                <h2 style="margin:0; color:#B45309;">{df_ranking.iloc[2]['Aciertos Totales']} Pts</h2>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")

    # Distribución en dos columnas de la Tabla General y Auditoría
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
        st.caption("🔄 Los marcadores se refrescan en automático con los cambios del Drive.")
        
    with right_col:
        st.subheader("🔍 Auditoría de Aciertos")
        participante_sel = st.selectbox(
            "Selecciona un participante para auditar sus aciertos:",
            options=df_ranking["Iniciales"].tolist(),
            format_func=lambda x: f"{x} - {detalles[x]['nombre']}"
        )
        
        if participante_sel:
            p_info = detalles[participante_sel]
            st.write(f"**Estatus de:** {p_info['nombre']}")
            
            if p_info['aciertos']:
                st.success(f"✔️ **Aciertos confirmados ({len(p_info['aciertos'])}):**")
                st.write(", ".join(sorted(list(p_info['aciertos']))))
            else:
                st.warning("Aún no registra aciertos confirmados en esta fase.")
                
            with st.expander("Ver árbol de predicciones completo"):
                st.write(", ".join(sorted(list(p_info['predicciones']))) if p_info['predicciones'] else "Sin predicciones legibles.")
else:
    st.error(df_ranking if df_ranking is not None else "Error de conexión con el archivo. Verifica los permisos de Drive.")
