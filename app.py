import time
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st
from openpyxl import load_workbook

# Configuración inicial de la página
st.set_page_config(
    page_title="Quiniela Mundial 2026", page_icon="⚽", layout="wide"
)

inicio = time.time()
zona_cdmx = ZoneInfo("America/Mexico_City")
ultima_actualizacion = datetime.now(zona_cdmx).strftime("%d/%m/%Y %H:%M")

st.title("⚽ Quiniela Mundial 2026")
st.info(
    "⚽ Pronósticos desde Google Drive y Marcadores EN VIVO en tiempo real."
)
st.caption(f"Página actualizada: {ultima_actualizacion} (hora CDMX)")

pagina = st.sidebar.radio(
    "Menú", ["🏆 Ranking", "👤 Participantes", "⚽ Partidos", "🗓️ Calendario"]
)

# ==========================================
# CONFIGURACIÓN FUENTES DE DATOS
# ==========================================
FILE_ID = "1svfBlcw4oOEltibwpv1c8I4h6sHmeq7z"
URL_DRIVE = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# API Pública y Gratuita del Mundial (Sincronizada al minuto)
URL_API_MUNDIAL = (
    "https://fixturedownload.com/feed/json/fifa-world-cup-2026"
)


# ==========================================
# FUNCIONES DE CARGA Y CACHÉ
# ==========================================


@st.cache_data(ttl=60)  # Se actualiza cada minuto en vivo
def obtener_marcadores_api():
    """Consulta la API pública de resultados en tiempo real"""
    try:
        respuesta = requests.get(URL_API_MUNDIAL, timeout=10)
        if respuesta.status_code == 200:
            partidos = respuesta.json()
            diccionario_resultados = {}

            for p in partidos:
                # Normalizamos nombres de equipos para evitar problemas de mayúsculas/minúsculas
                local = str(p["HomeTeam"]).strip().lower()
                visita = str(p["AwayTeam"]).strip().lower()
                clave_partido = f"{local} vs {visita}"

                goles_local = p["HomeTeamScore"]
                goles_visita = p["AwayTeamScore"]

                resultado_texto = None
                marcador_str = "vs"
                estado = "Programado"

                # Si los goles no son null, el partido se jugó o está en vivo
                if goles_local is not None and goles_visita is not None:
                    marcador_str = f"{goles_local} - {goles_visita}"
                    estado = "Finalizado"
                    if goles_local > goles_visita:
                        resultado_texto = "Local"
                    elif goles_visita > goles_local:
                        resultado_texto = "Visitante"
                    else:
                        resultado_texto = "Empate"

                # Guardamos la fecha nativa de la API para la sección calendario
                fecha_api = None
                if p.get("Date"):
                    try:
                        # La API suele mandar fechas en formato ISO UTC
                        fecha_api = datetime.fromisoformat(
                            p["Date"].replace("Z", "+00:00")
                        )
                    except:
                        pass

                diccionario_resultados[clave_partido] = {
                    "resultado": resultado_texto,
                    "marcador": marcador_str,
                    "estado": estado,
                    "fecha_utc": fecha_api,
                    "local_original": p["HomeTeam"],
                    "visita_original": p["AwayTeam"],
                }
            return diccionario_resultados
    except Exception as e:
        st.sidebar.error(f"Error API Marcadores: {e}")
    return {}


@st.cache_data(ttl=60)
def descargar_excel_drive():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=10)
        if respuesta.status_code == 200:
            return respuesta.content
    except Exception as e:
        st.error(f"Error al descargar Excel de Drive: {e}")
    return None


def leer_resultado_quiniela(ws, fila):
    c = str(ws[f"C{fila}"].value).strip().lower()
    d = str(ws[f"D{fila}"].value).strip().lower()
    e = str(ws[f"E{fila}"].value).strip().lower()
    if c == "x":
        return "Local"
    elif d == "x":
        return "Empate"
    elif e == "x":
        return "Visitante"
    return None


@st.cache_data(ttl=60)
def procesar_todo(contenido_excel, resultados_api):
    """Procesa el Excel de los amigos y cruza los datos con la API en un solo paso"""
    wb = load_workbook(BytesIO(contenido_excel), data_only=True)
    participantes_local = {}

    for hoja in wb.sheetnames:
        # Ya no necesitamos procesar hojas de resultados manuales
        if hoja.upper() in ["RESULTADOS", "CALENDARIO", "DATOS_ENVIVO"]:
            continue

        ws = wb[hoja]
        nombre = ws["C2"].value or hoja
        desempate_local = ws["J15"].value or 0
        desempate_visita = ws["L15"].value or 0

        pronosticos = []
        for fila in range(6, 200):
            local = ws[f"B{fila}"].value
            visitante = ws[f"F{fila}"].value

            if local is None or visitante is None:
                continue

            partido_str = f"{str(local).strip().lower()} vs {str(visitante).strip().lower()}"
            pronostico_jugador = leer_resultado_quiniela(ws, fila)

            # Cruzamos con los datos en vivo de la API
            info_api = resultados_api.get(
                partido_str, {"resultado": None, "marcador": "vs"}
            )
            resultado_oficial = info_api["resultado"]

            pronosticos.append(
                {
                    "Partido": f"{local} vs {visitante}",
                    "Pronóstico": pronostico_jugador,
                    "Resultado Oficial": resultado_oficial,
                    "Marcador Real": info_api["marcador"],
                    "Acierto": (
                        resultado_oficial is not None
                        and pronostico_jugador == resultado_oficial
                    ),
                }
            )

        participantes_local[nombre] = {
            "pronosticos": pronosticos,
            "desempate_local": desempate_local,
            "desempate_visitante": desempate_visita,
        }

    return participantes_local


# ==========================================
# EJECUCIÓN PRINCIPAL DE CARGA
# ==========================================
contenido_drive = descargar_excel_drive()
marcadores_en_vivo = obtener_marcadores_api()

if contenido_drive is None:
    st.error("No se pudo obtener el archivo de pronósticos desde Google Drive.")
    st.stop()

# Procesamos toda la info cruzada
participantes = procesar_todo(contenido_drive, marcadores_en_vivo)

# Calcular tabla de posiciones de la quiniela
puntos = {}
for nombre, datos in participantes.items():
    puntos[nombre] = sum(1 for p in datos["pronosticos"] if p["Acierto"])

st.write(f"⏱️ Tiempo de respuesta: {round(time.time() - inicio, 2)} segundos")

# ==========================================
# VISTAS / PÁGINAS DE LA APP
# ==========================================

if pagina == "🏆 Ranking":
    datos_ranking = []
    for nombre in participantes:
        dl = participantes[nombre]["desempate_local"]
        dv = participantes[nombre]["desempate_visitante"]
        datos_ranking.append(
            {
                "Participante": nombre,
                "Puntos": puntos[nombre],
                "Desempate": f"{int(float(dl))}-{int(float(dv))}",
            }
        )

    ranking_df = pd.DataFrame(datos_ranking).sort_values(
        by="Puntos", ascending=False
    )
    ranking_df = ranking_df.reset_index(drop=True)

    # Métricas de avance del torneo directo desde la API
    total_juegos = len(marcadores_en_vivo)
    jugados = sum(
        1 for x in marcadores_en_vivo.values() if x["estado"] == "Finalizado"
    )
    porcentaje = round(jugados * 100 / total_juegos, 1) if total_juegos else 0

    st.markdown(
        f"**⚽ Avance del torneo:** {jugados}/{total_juegos} partidos ({porcentaje}%)"
    )

    # Filtro de partidos para el día de hoy (Hora local CDMX)
    st.subheader("📅 Partidos para hoy")
    hoy = datetime.now(zona_cdmx).date()
    hay_partidos_hoy = False

    for clave, info in marcadores_en_vivo.items():
        if info["fecha_utc"]:
            # Convertimos la hora UTC de la API a hora de CDMX
            fecha_cdmx = info["fecha_utc"].astimezone(zona_cdmx)
            if fecha_cdmx.date() == hoy:
                hay_partidos_hoy = True
                if info["estado"] == "Finalizado":
                    st.write(
                        f"⚽ {info['local_original']} **{info['marcador']}** {info['visita_original']} ✓"
                    )
                else:
                    st.write(
                        f"🕒 {fecha_cdmx.strftime('%H:%M')} - {info['local_original']} vs {info['visita_original']}"
                    )

    if not hay_partidos_hoy:
        st.info("No hay partidos programados para hoy.")

    st.divider()
    st.subheader("Tabla General de la Quiniela")
    st.table(ranking_df)

elif pagina == "👤 Participantes":
    jugador = st.selectbox("Selecciona participante", list(participantes.keys()))
    st.subheader(f"Pronósticos de {jugador}")

    df = pd.DataFrame(participantes[jugador]["pronosticos"])
    # Reordenamos columnas para una vista más estética
    df = df[
        ["Partido", "Pronóstico", "Marcador Real", "Resultado Oficial", "Acierto"]
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)

elif pagina == "⚽ Partidos":
    primer_jugador = list(participantes.keys())[0]
    lista_partidos = [
        p["Partido"] for p in participantes[primer_jugador]["pronosticos"]
    ]

    partido_seleccionado = st.selectbox("Selecciona partido", lista_partidos)
    datos_partido = []

    for nombre, datos in participantes.items():
        for p in datos["pronosticos"]:
            if p["Partido"].lower() == partido_seleccionado.lower():
                datos_partido.append(
                    {
                        "Participante": nombre,
                        "Pronóstico": p["Pronóstico"],
                        "Marcador Real": p["Marcador Real"],
                        "¿Acertó?": "✅" if p["Acierto"] else "❌",
                    }
                )

    st.dataframe(
        pd.DataFrame(datos_partido), use_container_width=True, hide_index=True
    )

elif pagina == "🗓️ Calendario":
    st.subheader("🗓️ Calendario Completo del Mundial")

    lista_calendario = []
    for info in marcadores_en_vivo.values():
        fecha_str = "Por definir"
        hora_str = "--:--"
        if info["fecha_utc"]:
            dt_cdmx = info["fecha_utc"].astimezone(zona_cdmx)
            fecha_str = dt_cdmx.strftime("%d/%m/%Y")
            hora_str = dt_cdmx.strftime("%H:%M")

        lista_calendario.append(
            {
                "Fecha": fecha_str,
                "Hora (CDMX)": hora_str,
                "Partido": f"{info['local_original']} vs {info['visita_original']}",
                "Marcador": info["marcador"],
                "Estado": info["estado"],
            }
        )

    st.dataframe(
        pd.DataFrame(lista_calendario), use_container_width=True, hide_index=True
    )
