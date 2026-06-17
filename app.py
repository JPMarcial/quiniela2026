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
st.info("📊 Puntuaciones y resultados gestionados desde tu Excel de Google Drive.")
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
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ==========================================


@st.cache_data(ttl=60)
def descargar_excel_drive():
    try:
        respuesta = requests.get(URL_DRIVE, timeout=10)
        if respuesta.status_code == 200:
            return respuesta.content
    except Exception as e:
        st.error(f"Error al descargar Excel de Drive: {e}")
    return None


def leer_resultado(ws, fila):
    """Lee las columnas C, D y E para determinar el pronóstico/resultado (X)"""
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
    wb = load_workbook(BytesIO(contenido_excel), data_only=True)

    # 1. Leer pestaña de RESULTADOS OFICIALES
    resultados_oficiales = {}
    if "RESULTADOS" in wb.sheetnames:
        ws_res = wb["RESULTADOS"]
        for fila in range(6, 200):
            local = ws_res[f"B{fila}"].value
            visitante = ws_res[f"F{fila}"].value
            if local is None or visitante is None:
                continue
            partido_clave = f"{str(local).strip().lower()} vs {str(visitante).strip().lower()}"
            res_oficial = leer_resultado(ws_res, fila)
            resultados_oficiales[partido_clave] = res_oficial

    # 2. Leer Participantes y sus pronósticos
    participantes_local = {}
    for hoja in wb.sheetnames:
        if hoja.upper() in ["RESULTADOS", "CALENDARIO"]:
            continue

        ws = wb[hoja]
        nombre = ws["C2"].value or hoja
        desempate_local = ws["J15"].value or 0
        desempate_visitante = ws["L15"].value or 0

        pronosticos = []
        for fila in range(6, 200):
            local = ws[f"B{fila}"].value
            visitante = ws[f"F{fila}"].value

            if local is None or visitante is None:
                continue

            partido_clave = f"{str(local).strip().lower()} vs {str(visitante).strip().lower()}"
            pronostico_jugador = leer_resultado(ws, fila)
            resultado_oficial = resultados_oficiales.get(partido_clave, None)

            pronosticos.append(
                {
                    "Partido": f"{local} vs. {visitante}",
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

    # 3. Leer pestaña de CALENDARIO
    calendario_lista = []
    if "CALENDARIO" in wb.sheetnames:
        ws_cal = wb["CALENDARIO"]
        for fila in range(2, 500):
            partido = ws_cal[f"A{fila}"].value
            if partido is None:
                continue

            fecha = ws_cal[f"B{fila}"].value
            hora = ws_cal[f"C{fila}"].value
            resultado_final = ws_cal[f"D{fila}"].value or "vs"

            # Formatear fecha de forma segura
            if hasattr(fecha, "strftime"):
                fecha_str = fecha.strftime("%d/%m/%Y")
            else:
                fecha_str = str(fecha)

            # Formatear hora de forma segura
            if hasattr(hora, "strftime"):
                hora_str = hora.strftime("%H:%M")
            else:
                hora_str = str(hora)

            calendario_lista.append(
                {
                    "Fecha": fecha_str,
                    "Hora (CDMX)": hora_str,
                    "Partido": partido,
                    "Resultado Final": resultado_final,
                }
            )

    return participantes_local, calendario_lista


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
contenido_drive = descargar_excel_drive()

if contenido_drive is None:
    st.error("No se pudo descargar el archivo desde Google Drive.")
    st.stop()

# Procesamos los datos leyendo el archivo
participantes, calendario = procesar_datos_quiniela(contenido_drive)

# Calcular puntos por participante
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

    st.subheader("Tabla General de la Quiniela")
    st.table(ranking_df)

elif pagina == "👤 Participantes":
    jugador = st.selectbox("Selecciona participante", list(participantes.keys()))
    st.subheader(f"Pronósticos de {jugador}")

    df = pd.DataFrame(participantes[jugador]["pronosticos"])
    df = df[["Partido", "Pronóstico", "Resultado Oficial", "Acierto"]]
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
                        "Resultado Oficial": p["Resultado Oficial"],
                        "¿Acertó?": "✅" if p["Acierto"] else "❌",
                    }
                )

    st.dataframe(
        pd.DataFrame(datos_partido), use_container_width=True, hide_index=True
    )

elif pagina == "🗓️ Calendario":
    st.subheader("🗓️ Calendario del Torneo")
    if calendario:
        df_cal = pd.DataFrame(calendario)
        st.dataframe(df_cal, use_container_width=True, hide_index=True)
    else:
        st.info("No se encontró información en la pestaña CALENDARIO.")
