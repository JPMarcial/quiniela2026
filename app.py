import time
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st
from openpyxl import load_workbook

ultima_actualizacion = datetime.now(ZoneInfo("America/Mexico_City")).strftime(
    "%d/%m/%Y %H:%M"
)

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Quiniela Mundial 2026", page_icon="⚽", layout="wide"
)

st.title("⚽ Quiniela Mundial 2026")

# CSS para aumentar tamaño de letra en tablas y textos de partidos
st.markdown(
    """
    <style>
    .stDataFrame div[data-testid="stTable"] td, 
    .stDataFrame div[data-testid="stTable"] th,
    div[data-testid="stDataFrameVisualizer"] [role="gridcell"],
    div[data-testid="stDataFrameVisualizer"] [role="columnheader"] {
        font-size: 19px !important;
    }
    
    .partido-hoy {
        font-size: 20px !important;
        font-weight: 500;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

inicio = time.time()

st.info(
    "⚽ La información se actualiza desde Google Drive y la API de fútbol en tiempo real."
)
st.caption(f"Página actualizada: {ultima_actualizacion} (hora CDMX)")

# Revisar si en la URL se incluyó el parámetro ?admin=true
es_admin = st.query_params.get("admin") == "true"

if es_admin:
    opciones_menu = ["🏆 Ranking", "👤 Participantes", "⚽ Partidos", "🗓️ Calendario", "🔧 API TEST", "🤖 Resultados API"]
else:
    opciones_menu = ["🏆 Ranking", "👤 Participantes", "⚽ Partidos", "🗓️ Calendario"]

pagina = st.sidebar.radio("Menú", opciones_menu)

# ==========================================
# CONFIGURACIÓN DE FUENTES DE DATOS
# ==========================================

FILE_ID = "1svfBlcw4oOEltibwpv1c8I4h6sHmeq7z"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"
API_KEY = "b0ddb5d580614b7ba76872163c286ed1"

# Diccionario de traducción estricto
TRADUCCION_EQUIPOS = {
    "Mexico": "México", "South Africa": "Sudáfrica", "South Korea": "Corea del Sur", "Czechia": "República Checa",
    "Canada": "Canadá", "Bosnia and Herzegovina": "Bosnia y Herzegovina", "United States": "Estados Unidos",
    "Paraguay": "Paraguay", "Qatar": "Catar", "Switzerland": "Suiza", "Brazil": "Brasil", "Morocco": "Marruecos",
    "Haiti": "Haití", "Scotland": "Escocia", "Australia": "Australia", "Turkey": "Turquía", "Germany": "Alemania",
    "Curacao": "Curazao", "Netherlands": "Países Bajos", "Japan": "Japón", "Ivory Coast": "Costa de Marfil",
    "Ecuador": "Ecuador", "Sweden": "Suecia", "Tunisia": "Túnez", "Spain": "España", "Cape Verde": "Cabo Verde",
    "Cape Verde Islands": "Cabo Verde", "Belgium": "Bélgica", "Egypt": "Egipto", "Saudi Arabia": "Arabia Saudita",
    "Uruguay": "Uruguay", "Iran": "Irán", "New Zealand": "Nueva Zelanda", "France": "Francia", "Senegal": "Senegal",
    "Iraq": "Irak", "Norway": "Noruega", "Argentina": "Argentina", "Algeria": "Argelia", "Austria": "Austria",
    "Jordan": "Jordania", "Portugal": "Portugal", "DR Congo": "RD Congo", "England": "Inglaterra",
    "Croatia": "Croacia", "Ghana": "Ghana", "Panama": "Panamá", "Uzbekistan": "Uzbekistán", "Colombia": "Colombia"
}

@st.cache_data(ttl=60)
def cargar_excel():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=10)
        if respuesta.status_code == 200:
            return respuesta.content
    except Exception as e:
        st.error(f"Error al descargar Excel de Drive: {e}")
    return None

# ==========================================
# CONSUMO DE AUTOMATIZACIÓN (API)
# ==========================================

@st.cache_data(ttl=60)
def obtener_resultados_api():
    dict_resultados = {}
    headers = {"X-Auth-Token": API_KEY}
    try:
        respuesta = requests.get("https://api.football-data.org/v4/competitions/WC/matches", headers=headers, timeout=10)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            for partido in datos.get("matches", []):
                local_api = partido["homeTeam"]["name"]
                visitante_api = partido["awayTeam"]["name"]
                
                local = TRADUCCION_EQUIPOS.get(local_api, local_api)
                visitante = TRADUCCION_EQUIPOS.get(visitante_api, visitante_api)
                
                estado = partido["status"]
                goles_local = partido["score"]["fullTime"]["home"]
                goles_visitante = partido["score"]["fullTime"]["away"]
                
                clave_partido = f"{str(local).strip().lower()} vs {str(visitante).strip().lower()}"
                
                if estado in ["IN_PLAY", "PAUSED"] and goles_local is not None and goles_visitante is not None:
                    dict_resultados[clave_partido] = f"LIVE:{goles_local}-{goles_visitante}"
                elif estado == "FINISHED" and goles_local is not None and goles_visitante is not None:
                    if goles_local > goles_visitante:
                        dict_resultados[clave_partido] = "Local"
                    elif goles_local < goles_visitante:
                        dict_resultados[clave_partido] = "Visitante"
                    else:
                        dict_resultados[clave_partido] = "Empate"
    except Exception as e:
        pass
    return dict_resultados

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def determinar_resultado_celdas(c, d, e):
    c_str = str(c).strip().lower() if c is not None else ""
    d_str = str(d).strip().lower() if d is not None else ""
    e_str = str(e).strip().lower() if e is not None else ""

    if c_str == "x":
        return "Local"
    elif d_str == "x":
        return "Empate"
    elif e_str == "x":
        return "Visitante"
    return None


@st.cache_data(ttl=60)  
def procesar_todo_el_excel(contenido_excel):
    wb_local = load_workbook(BytesIO(contenido_excel), data_only=True, read_only=True)

    if "RESULTADOS" not in wb_local.sheetnames:
        return None, None

    resultados_automatizados = obtener_resultados_api()

    ws_resultados = wb_local["RESULTADOS"]
    resultados_oficiales = {}
    
    for fila_idx, row in enumerate(ws_resultados.iter_rows(min_row=6, max_row=500, min_col=2, max_col=6, values_only=True), start=6):
        if len(row) < 5:
            continue
        local, c, d, e, visitante = row[0], row[1], row[2], row[3], row[4]
        if local is None or visitante is None:
            continue
            
        clave_busqueda = f"{str(local).strip().lower()} vs {str(visitante).strip().lower()}"
        
        if clave_busqueda in resultados_automatizados:
            resultados_oficiales[fila_idx] = resultados_automatizados[clave_busqueda]
        else:
            resultados_oficiales[fila_idx] = determinar_resultado_celdas(c, d, e)

    participantes_local = {}
    calendario_local = []

    for hoja in wb_local.sheetnames:
        if hoja.upper() == "RESULTADOS":
            continue
            
        if hoja.upper() == "CALENDARIO":
            ws_cal = wb_local[hoja]
            for row in ws_cal.iter_rows(min_row=2, max_row=500, min_col=1, max_col=4, values_only=True):
                if len(row) < 4 or row[0] is None:
                    continue
                calendario_local.append({
                    "partido": row[0],
                    "fecha": row[1],
                    "hora": row[2],
                    "resultado": row[3]
                })
            continue

        ws = wb_local[hoja]
        nombre = hoja
        desempate_local = "-"
        desempate_visitante = "-"
        
        for r_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=15, min_col=3, max_col=12, values_only=True), start=2):
            if r_idx == 2 and len(row) > 0:
                nombre = row[0] or hoja
            if r_idx == 15 and len(row) >= 10:
                desempate_local = row[7]       
                desempate_visitante = row[9]   

        pronosticos = []
        for fila_idx, row in enumerate(ws.iter_rows(min_row=6, max_row=500, min_col=2, max_col=6, values_only=True), start=6):
            if len(row) < 5:
                continue
            local, c, d, e, visitante = row[0], row[1], row[2], row[3], row[4]
            if local is None or visitante is None:
                continue

            resultado_oficial = resultados_oficiales.get(fila_idx)
            pronostico_jugador = determinar_resultado_celdas(c, d, e)

            es_acierto = (
                resultado_oficial is not None
                and not str(resultado_oficial).startswith("LIVE:")
                and pronostico_jugador == resultado_oficial
            )

            estatus_visual = "⌛ Pautado"
            if resultado_oficial is not None:
                if str(resultado_oficial).startswith("LIVE:"):
                    estatus_visual = "🔴 En Juego"
                else:
                    estatus_visual = "✅ ¡Acertó!" if es_acierto else "❌ Falló"

            pronosticos.append(
                {
                    "fila": fila_idx,
                    "Partido": f"{local} vs {visitante}",
                    "Pronóstico": pronostico_jugador,
                    "Resultado Oficial": resultado_oficial,
                    "Estatus": estatus_visual,
                    "Acierto": es_acierto,
                }
            )

        participantes_local[nombre] = {
            "pronosticos": pronosticos,
            "desempate_local": desempate_local,
            "desempate_visitante": desempate_visitante,
        }

    return participantes_local, calendario_local


# ==========================================
# RENDERS DE PÁGINAS
# ==========================================

contenido_excel = cargar_excel()

if contenido_excel is None:
    st.error("No se pudo descargar el archivo desde Google Drive.")
    st.stop()

participantes, calendario_datos = procesar_todo_el_excel(contenido_excel)

if participantes is None:
    st.error("No existe la hoja RESULTADOS en el archivo.")
    st.stop()

puntos = {nombre: sum(1 for p in datos["pronosticos"] if p["Acierto"]) for nombre, datos in participantes.items()}

st.write(f"Tiempo de carga: {round(time.time() - inicio, 2)} segundos")

if pagina == "🏆 Ranking":
    ranking_datos = []
    for nombre in participantes:
        dl = participantes[nombre]['desempate_local']
        dv = participantes[nombre]['desempate_visitante']
        
        try:
            val_dl = f"{int(float(dl))}" if dl not in [None, "", "-"] else "-"
            val_dv = f"{int(float(dv))}" if dv not in [None, "", "-"] else "-"
            desempate_txt = f"{val_dl}-{val_dv}" if val_dl != "-" and val_dv != "-" else "-"
        except:
            desempate_txt = f"{dl}-{dv}" if dl or dv else "-"

        ranking_datos.append({
            "Participante": nombre,
            "Puntos": puntos[nombre],
            "Desempate (Chequia vs México)": desempate_txt
        })

    ranking = pd.DataFrame(ranking_datos)
    ranking = ranking.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    total_partidos = 0
    partidos_jugados = 0
    partidos_hoy = []
    hoy = datetime.now(ZoneInfo("America/Mexico_City")).date()

    if calendario_datos:
        resultados_api = obtener_resultados_api()
        for c_partido in calendario_datos:
            partido = c_partido["partido"]
            fecha = c_partido["fecha"]
            hora = c_partido["hora"]
            resultado = c_partido["resultado"]

            if resultado not in [None, ""]:
                partidos_jugados += 1
            total_partidos += 1

            try:
                clave_busqueda = f"{str(partido).strip().lower()}"
                api_status = resultados_api.get(clave_busqueda, "")
                
                # 🔥 CORRECCIÓN INCONDICIONAL: Si la API reporta el partido vivo, ignoramos la validación de fecha del Excel. ¡Se muestra porque se muestra!
                if str(api_status).startswith("LIVE:"):
                    marcador_vivo = api_status.split(":")[1]
                    g_local, g_vis = marcador_vivo.split("-")
                    if " vs " in str(partido).lower():
                        equipos = str(partido).split(" vs ")
                        texto = f"🔴 **EN JUEGO:** {equipos[0]} **{g_local} - {g_vis}** {equipos[1]}"
                    else:
                        texto = f"🔴 **EN JUEGO:** {partido} ({marcador_vivo})"
                    partidos_hoy.append(texto)
                    continue  # Saltamos al siguiente partido para evitar duplicados

                # Para partidos pautados o ya terminados, usamos la fecha limpia del excel
                if hasattr(fecha, "date"):
                    fecha_partido = fecha.date()
                elif isinstance(fecha, str):
                    # Intento de parsear si viene como texto simple "YYYY-MM-DD" o "DD/MM/YYYY"
                    try:
                        fecha_partido = datetime.strptime(fecha.split()[0], "%Y-%m-%d").date()
                    except:
                        try:
                            fecha_partido = datetime.strptime(fecha.split()[0], "%d/%m/%Y").date()
                        except:
                            continue
                else:
                    continue

                if fecha_partido == hoy:
                    if resultado not in [None, ""]:
                        if " vs " in str(partido).lower():
                            equipos = str(partido).split(" vs ")
                            texto = f"⚽ {equipos[0]} {resultado} {equipos[1]}"
                        else:
                            texto = f"⚽ {partido} ({resultado})"
                    else:
                        texto = (
                            f"🕒 {hora.strftime('%H:%M')} - {partido}"
                            if hasattr(hora, "strftime")
                            else f"{hora} - {partido}"
                        )
                    partidos_hoy.append(texto)
            except Exception as e:
                pass

    porcentaje = round(partidos_jugados * 100 / total_partidos, 1) if total_partidos > 0 else 0

    puntaje_maximo = ranking["Puntos"].max() if not ranking.empty else -1
    puntaje_minimo = ranking["Puntos"].min() if not ranking.empty else -1
    
    if puntaje_maximo != -1:
        filtro_lideres = ranking[ranking["Puntos"] == puntaje_maximo]["Participante"].tolist()
        primeros_nombres_lideres = [str(n).strip().split()[0] for n in filtro_lideres]
        
        if len(primeros_nombres_lideres) > 1:
            texto_lideres = ", ".join(primeros_nombres_lideres[:-1]) + " y " + primeros_nombres_lideres[-1]
            etiqueta_lider = "🔥 Líderes Actuales"
        else:
            texto_lideres = primeros_nombres_lideres[0]
            etiqueta_lider = "🔥 Líder Actual"
    else:
        texto_lideres = "-"
        etiqueta_lider = "🔥 Líder Actual"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="⚽ Partidos Jugados", value=f"{partidos_jugados} / {total_partidos}")
    with col2:
        st.metric(label="📈 Avance del Torneo", value=f"{porcentaje}%")
    with col3:
        st.metric(label=etiqueta_lider, value=texto_lideres)

    st.divider()
    st.subheader("📅 Partidos para hoy")
    if len(partidos_hoy) == 0:
        st.info("No hay partidos programados para hoy.")
    else:
        for p in partidos_hoy:
            st.markdown(f'<p class="partido-hoy">{p}</p>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Tabla General")

    if puntaje_maximo != -1:
        def agregar_emoji(r):
            if str(r["Participante"]).strip() == "Victor Vazquez":
                return f"🐌 {r['Participante']}"
            if r["Puntos"] == puntaje_maximo:
                return f"👑 {r['Participante']}"
            elif r["Puntos"] == puntaje_minimo and puntaje_minimo != puntaje_maximo:
                return f"🐌 {r['Participante']}"
            return r["Participante"]

        ranking["Participante"] = ranking.apply(agregar_emoji, axis=1)

    def resaltar_estilo_premium(row):
        if puntaje_maximo != -1 and row["Puntos"] == puntaje_maximo:
            return ['background-color: #fffbeb; color: #b45309; font-weight: bold;'] * len(row)
        elif puntaje_minimo != -1 and row["Puntos"] == puntaje_minimo and puntaje_minimo != puntaje_maximo:
            return ['background-color: #fdf2f8; color: #9d174d; font-style: italic;'] * len(row)
        return [''] * len(row)

    ranking_estilizado = ranking.style.apply(resaltar_estilo_premium, axis=1)
    st.dataframe(ranking_estilizado, use_container_width=True, hide_index=True)

    st.divider()
    with st.chat_message("assistant", avatar="👷‍♂️"):
        st.markdown("**¡Hola! Se aceptan ideas o sugerencias para mejorar la página.**")

elif pagina == "👤 Participantes":
    jugador = st.selectbox("Selecciona participante", list(participantes.keys()))
    st.subheader(f"Pronósticos de {jugador}")

    df = pd.DataFrame(participantes[jugador]["pronosticos"])
    df = df.drop(columns=["fila", "Acierto"], errors="ignore").reset_index(drop=True)
    df = df[["Partido", "Pronóstico", "Resultado Oficial", "Estatus"]]

    def color_estatus(val):
        if "✅" in str(val):
            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
        elif "❌" in str(val):
            return 'background-color: #f8d7da; color: #721c24;'
        elif "🔴" in str(val):
            return 'background-color: #fff3cd; color: #856404; font-weight: bold;'
        return ''

    df_estilizado = df.style.map(color_estatus, subset=["Estatus"])
    st.dataframe(df_estilizado, use_container_width=True, hide_index=True)

elif pagina == "⚽ Partidos":
    primer_jugador = list(participantes.keys())[0]
    lista_partidos = [p["Partido"] for p in participantes[primer_jugador]["pronosticos"]]

    partido_seleccionado = st.selectbox("Selecciona partido", lista_partidos)
    datos_partido = []

    for nombre, datos in participantes.items():
        for p in datos["pronosticos"]:
            if p["Partido"] == partido_seleccionado:
                datos_partido.append(
                    {
                        "Participante": nombre,
                        "Pronóstico": p["Pronóstico"],
                        "Resultado Oficial": p["Resultado Oficial"],
                        "¿Acertó?": "✅ SÍ" if p["Acierto"] else ("🔴 EN JUEGO" if "LIVE:" in str(p["Resultado Oficial"]) else "❌ NO"),
                    }
                )

    st.dataframe(pd.DataFrame(datos_partido).reset_index(drop=True), use_container_width=True, hide_index=True)

elif pagina == "🗓️ Calendario":
    if not calendario_datos:
        st.warning("No existe o está vacía la hoja CALENDARIO")
    else:
        calendario_tabla = []
        for c_partido in calendario_datos:
            partido = c_partido["partido"]
            fecha = c_partido["fecha"]
            hora = c_partido["hora"]
            resultado_final = c_partido["resultado"] if c_partido["resultado"] is not None else " "

            try:
                fecha = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else str(fecha)
            except:
                pass

            try:
                hora = hora.strftime("%H:%M") if hasattr(hora, "strftime") else str(hora)
            except:
                pass

            calendario_tabla.append(
                {
                    "Partido": partido,
                    "Fecha": fecha,
                    "Hora (CDMX)": hora,
                    "Resultado Final": resultado_final,
                }
            )

        st.subheader("Calendario de partidos")
        st.dataframe(pd.DataFrame(calendario_tabla).reset_index(drop=True), use_container_width=True, hide_index=True)

elif pagina == "🔧 API TEST":
    st.subheader("Prueba de API Mundial")
    headers = {"X-Auth-Token": API_KEY}
    try:
        respuesta = requests.get("https://api.football-data.org/v4/matches", headers=headers)
        st.write(f"Status: {respuesta.status_code}")
        datos = respuesta.json()

        for partido in datos.get("matches", []):
            local_api = partido["homeTeam"]["name"]
            visitante_api = partido["awayTeam"]["name"]
            
            local = TRADUCCION_EQUIPOS.get(local_api, local_api)
            visitante = TRADUCCION_EQUIPOS.get(visitante_api, visitante_api)
            estado = partido["status"]
            goles_local = partido["score"]["fullTime"]["home"]
            goles_visitante = partido["score"]["fullTime"]["away"]
        
            st.write(f"{local} vs {visitante} | {estado} | {goles_local}-{goles_visitante}")
    except Exception as e:
        st.error(f"Error: {e}")

elif pagina == "🤖 Resultados API":
    st.subheader("Resultados desde API")
    headers = {"X-Auth-Token": API_KEY}
    respuesta = requests.get("https://api.football-data.org/v4/competitions/WC/matches", headers=headers)
    datos = respuesta.json()

    st.write("Status:", respuesta.status_code)
    
    if "matches" not in datos:
        st.error("La API no devolvió partidos")
        st.write(datos)
        st.stop()
    
    resultados = []
    for partido in datos["matches"]:
        local_api = partido["homeTeam"]["name"]
        visitante_api = partido["awayTeam"]["name"]

        local = TRADUCCION_EQUIPOS.get(local_api, local_api)
        visitante = TRADUCCION_EQUIPOS.get(visitante_api, visitante_api)
        estado = partido["status"]
        goles_local = partido["score"]["fullTime"]["home"]
        goles_visitante = partido["score"]["fullTime"]["away"]

        resultado_quiniela = ""
        if estado == "FINISHED":
            if goles_local > goles_visitante:
                resultado_quiniela = "Local"
            elif goles_local < goles_visitante:
                resultado_quiniela = "Visitante"
            else:
                resultado_quiniela = "Empate"
        elif estado in ["IN_PLAY", "PAUSED"]:
            resultado_quiniela = "EN JUEGO"
        
        resultados.append({
            "Partido": f"{local} vs {visitante}",
            "Estado": estado,
            "Marcador": f"{goles_local}-{goles_visitante}" if goles_local is not None else "",
            "Resultado Quiniela": resultado_quiniela
        })

    st.dataframe(pd.DataFrame(resultados), use_container_width=True, hide_index=True)
