import time
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo
import openpyxl
import pandas as pd
import requests
import streamlit as st
from openpyxl import load_workbook

# Configuración inicial de la página
st.set_page_config(
    page_title="Quiniela Mundial 2026", page_icon="⚽", layout="wide"
)

inicio = time.time()

ultima_actualizacion = datetime.now(ZoneInfo("America/Mexico_City")).strftime(
    "%d/%m/%Y %H:%M"
)

st.title("⚽ Quiniela Mundial 2026")
st.info(
    "⚽ La información se actualiza desde Google Drive. La carga inicial puede tardar algunos segundos."
)
st.caption(f"Página actualizada: {ultima_actualizacion} (hora CDMX)")

pagina = st.sidebar.radio(
    "Menú", ["🏆 Ranking", "👤 Participantes", "⚽ Partidos", "🗓️ Calendario"]
)

# ==========================================
# CONFIGURACIÓN GOOGLE DRIVE
# ==========================================
FILE_ID = "1svfBlcw4oOEltibwpv1c8I4h6sHmeq7z" 

URL_DRIVE = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# ==========================================
# FUNCIONES DE CARGA Y CACHÉ (60 segundos)
# ==========================================


@st.cache_data(ttl=60)
def descargar_archivo_drive():
    try:
        respuesta = requests.get(URL_DRIVE)
        if respuesta.status_code == 200:
            return respuesta.content
    except Exception as e:
        st.error(f"Error al conectar con Google Drive: {e}")
    return None


def leer_resultado(ws, fila):
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
def procesar_datos_quiniela(contenido_excel):
    """Procesa todo el libro de Excel en una sola lectura cacheada"""
    wb = load_workbook(BytesIO(contenido_excel), data_only=True)

    # 1. Leer Resultados Oficiales
    ws_resultados = wb["RESULTADOS"] if "RESULTADOS" in wb.sheetnames else None

    # 2. Leer Participantes
    participantes_local = {}
    for hoja in wb.sheetnames:
        if hoja.upper() in ["RESULTADOS", "CALENDARIO"]:
            continue

        ws = wb[hoja]
        nombre = ws["C2"].value
        desempate_local = ws["J15"].value
        desempate_visitante = ws["L15"].value

        pronosticos = []
        for fila in range(6, 200):
            local = ws[f"B{fila}"].value
            visitante = ws[f"F{fila}"].value

            if local is None or visitante is None:
                continue

            pronostico_jugador = leer_resultado(ws, fila)
            resultado_oficial = (
                leer_resultado(ws_resultados, fila)
                if ws_resultados
                else None
            )

            pronosticos.append(
                {
                    "fila": fila,
                    "Partido": f"{local} vs {visitante}",
                    "Pronóstico": pronostico_jugador,
                    "Resultado Oficial": resultado_oficial,
                    "Acierto": (
                        resultado_oficial is not None
                        and pronostico_jugador == resultado_oficial
                    ),
                }
            )

        participantes_local[nombre] = {
            "pronosticos": pronosticos,
            "desempate_local": desempate_local,
            "desempate_visitante": desempate_visitante,
        }

    # 3. Leer Calendario
    calendario_lista = []
    if "CALENDARIO" in wb.sheetnames:
        ws_cal = wb["CALENDARIO"]
        for fila in range(2, 500):
            partido = ws_cal[f"A{fila}"].value
            if partido is None:
                continue

            fecha = ws_cal[f"B{fila}"].value
            hora = ws_cal[f"C{fila}"].value
            resultado_final = ws_cal[f"D{fila}"].value or " "

            # Formatear fecha
            if hasattr(fecha, "date"):
                fecha_dt = fecha
                fecha_str = fecha.strftime("%d/%m/%Y")
            else:
                fecha_dt = None
                fecha_str = str(fecha)

            # Formatear hora
            if hasattr(hora, "strftime"):
                hora_str = hora.strftime("%H:%M")
            else:
                hora_str = str(hora)

            calendario_lista.append(
                {
                    "Partido": partido,
                    "Fecha_DT": fecha_dt,  # Guardamos el objeto datetime para comparar 'hoy'
                    "Fecha": fecha_str,
                    "Hora (CDMX)": hora_str,
                    "Resultado Final": resultado_final,
                }
            )

    return participantes_local, calendario_lista


# ==========================================
# CARGA PRINCIPAL DE DATOS
# ==========================================
contenido = descargar_archivo_drive()

if contenido is None:
    st.error("No se pudo descargar o abrir el archivo desde Google Drive.")
    st.stop()

# Procesamos toda la data junta de forma eficiente
participantes, calendario = procesar_datos_quiniela(contenido)

# Calcular puntos por participante
puntos = {}
for nombre, datos in participantes.items():
    total = sum(1 for p in datos["pronosticos"] if p["Acierto"])
    puntos[nombre] = total

# Mostrar tiempo de ejecución
st.write(f"Tiempo de carga: {round(time.time() - inicio, 2)} segundos")

# ==========================================
# RENDERIZADO DE PÁGINAS
# ==========================================

if pagina == "🏆 Ranking":
    # Construcción del dataframe de Ranking
    datos_ranking = []
    for nombre in participantes:
        dl = participantes[nombre]["desempate_local"]
        dv = participantes[nombre]["desempate_visitante"]
        desempate_str = (
            f"{int(float(dl))}-{int(float(dv))}"
            if dl not in [None, ""] and dv not in [None, ""]
            else "-"
        )

        datos_ranking.append(
            {
                "Participante": nombre,
                "Puntos": puntos[nombre],
                "Desempate (Chequia vs México)": desempate_str,
            }
        )

    ranking = pd.DataFrame(datos_ranking).sort_values(
        by="Puntos", ascending=False
    )
    ranking = ranking.reset_index(drop=True)

    st.subheader("📅 Partidos para hoy")

    # Avance del torneo y partidos de hoy usando la data ya procesada
    total_partidos = len(calendario)
    partidos_jugados = sum(
        1 for c in calendario if c["Resultado Final"] not in [None, " ", ""]
    )

    if total_partidos > 0:
        porcentaje = round(partidos_jugados * 100 / total_partidos, 1)
        st.markdown(
            f"**⚽ Avance del torneo:** {partidos_jugados}/{total_partidos} partidos ({porcentaje}%)"
        )
    else:
        st.markdown("**⚽ Avance del torneo:** 0/0 partidos (0%)")

    hoy = datetime.now(ZoneInfo("America/Mexico_City")).date()
    partidos_hoy = []

    for c in calendario:
        if c["Fecha_DT"] and c["Fecha_DT"].date() == hoy:
            partido = c["Partido"]
            res = c["Resultado Final"]

            if res not in [None, " ", ""]:
                equipos = partido.split(" vs ")
                texto = (
                    f"⚽ {equipos[0]} {res} {equipos[1]}"
                    if len(equipos) == 2
                    else f"⚽ {partido} ({res})"
                )
            else:
                texto = f"🕒 {c['Hora (CDMX)']} - {partido}"

            partidos_hoy.append(texto)

    if not partidos_hoy:
        st.info("No hay partidos programados para hoy.")
    else:
        for p in partidos_hoy:
            st.write(p)

    st.divider()
    st.subheader("Tabla General")
    st.table(ranking)

elif pagina == "👤 Participantes":
    jugador = st.selectbox("Selecciona participante", list(participantes.keys()))
    st.subheader(f"Pronósticos de {jugador}")

    df = pd.DataFrame(participantes[jugador]["pronosticos"])
    df = df.drop(columns=["fila"], errors="ignore")
    df = df.reset_index(drop=True)

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
            if p["Partido"] == partido_seleccionado:
                datos_partido.append(
                    {
                        "Participante": nombre,
                        "Pronóstico": p["Pronóstico"],
                        "Resultado Oficial": p["Resultado Oficial"],
                    }
                )

    df_partido = pd.DataFrame(datos_partido).reset_index(drop=True)
    st.dataframe(df_partido, use_container_width=True, hide_index=True)

elif pagina == "🗓️ Calendario":
    st.subheader("Calendario de partidos")
    if not calendario:
        st.warning("No hay datos en el calendario.")
    else:
        df_cal = pd.DataFrame(calendario).drop(
            columns=["Fecha_DT"], errors="ignore"
        )
        st.dataframe(df_cal, use_container_width=True, hide_index=True)
