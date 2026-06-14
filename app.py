import streamlit as st
import pandas as pd
import requests

from io import BytesIO
from openpyxl import load_workbook
from datetime import datetime

ultima_actualizacion = datetime.now().strftime(
    "%d/%m/%Y %H:%M"
)

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Quiniela Mundial 2026",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Quiniela Mundial 2026")

import time

inicio = time.time()

st.info(
    "⚽ La información se actualiza desde Google Drive. La carga inicial puede tardar algunos segundos."
)
st.caption(
    f"Última actualización: {ultima_actualizacion}"
)

pagina = st.sidebar.radio(
    "Menú",
    [
    "🏆 Ranking",
    "👤 Participantes",
    "⚽ Partidos",
    "🗓️ Calendario"
]
)

# ==========================================
# GOOGLE DRIVE
# ==========================================

FILE_ID = "1svfBlcw4oOEltibwpv1c8I4h6sHmeq7z"

URL_DRIVE = (
    f"https://docs.google.com/uc?export=download&id={FILE_ID}"
)

@st.cache_data(ttl=60)
def cargar_excel():

    respuesta = requests.get(URL_DRIVE)

    if respuesta.status_code != 200:
        return None

    return respuesta.content

# ==========================================
# FUNCIÓN PARA LEER RESULTADO
# ==========================================

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

@st.cache_data(ttl=86400)
def cargar_participantes():

    contenido_excel = cargar_excel()

    wb_local = load_workbook(
        BytesIO(contenido_excel),
        data_only=True
    )

    participantes_local = {}

    for hoja in wb_local.sheetnames:

        if hoja.upper() in ["RESULTADOS", "CALENDARIO"]:
            continue

        ws = wb_local[hoja]

        nombre = ws["C2"].value

        desempate_local = ws["J15"].value
        desempate_visitante = ws["L15"].value

        pronosticos = []

        for fila in range(6, 200):

            local = ws[f"B{fila}"].value
            visitante = ws[f"F{fila}"].value

            if local is None or visitante is None:
                continue

            pronosticos.append(
                {
                    "fila": fila,
                    "Partido": f"{local} vs {visitante}",
                    "Pronóstico": leer_resultado(ws, fila)
                }
            )

        participantes_local[nombre] = {
            "pronosticos": pronosticos,
            "desempate_local": desempate_local,
            "desempate_visitante": desempate_visitante
        }

    return participantes_local

# ==========================================
# LEER EXCEL DESDE GOOGLE DRIVE
# ==========================================

try:

    contenido_excel = cargar_excel()

    if contenido_excel is None:

        st.error(
            "No se pudo descargar el archivo desde Google Drive."
        )

        st.stop()

    wb = load_workbook(
        BytesIO(contenido_excel),
        data_only=True
    )

except Exception as e:

    st.error(
        f"No se pudo abrir el archivo desde Drive: {e}"
    )

    st.stop()

# ==========================================
# RESULTADOS OFICIALES
# ==========================================

if "RESULTADOS" not in wb.sheetnames:

    st.error(
        "No existe la hoja RESULTADOS"
    )

    st.stop()

ws_resultados = wb["RESULTADOS"]

participantes = cargar_participantes()

for nombre, datos in participantes.items():

    for p in datos["pronosticos"]:

        fila = p["fila"]

        resultado_oficial = leer_resultado(
            ws_resultados,
            fila
        )

        p["Resultado Oficial"] = resultado_oficial

        p["Acierto"] = (
            resultado_oficial is not None
            and p["Pronóstico"] == resultado_oficial
        )


# ==========================================
# CALCULAR PUNTOS
# ==========================================

puntos = {}

for nombre, datos in participantes.items():

    total = 0

    for p in datos["pronosticos"]:

        if p["Acierto"]:
            total += 1

    puntos[nombre] = total

# ==========================================
# RANKING
# ==========================================
st.write(f"Tiempo de carga: {round(time.time() - inicio, 2)} segundos")

if pagina == "🏆 Ranking":

    ranking = pd.DataFrame(
        [
            {
                "Participante": nombre,
                "Puntos": puntos[nombre],
               "Desempate":
(
    f"{int(float(participantes[nombre]['desempate_local']))}-{int(float(participantes[nombre]['desempate_visitante']))}"
    if participantes[nombre]['desempate_local'] not in [None, ""]
    and participantes[nombre]['desempate_visitante'] not in [None, ""]
    else "-"
)
            }
            for nombre in participantes
        ]
    )

    ranking = ranking.sort_values(
        by="Puntos",
        ascending=False
    )

    ranking = ranking.reset_index(drop=True)

    from datetime import date

st.subheader("📅 Partidos para hoy")

hoy = date.today()

partidos_hoy = []

if "CALENDARIO" in wb.sheetnames:

    ws_cal = wb["CALENDARIO"]

    for fila in range(2, 500):

        partido = ws_cal[f"A{fila}"].value

        if partido is None:
            continue

        fecha = ws_cal[f"B{fila}"].value
        hora = ws_cal[f"C{fila}"].value
        resultado = ws_cal[f"D{fila}"].value

        try:

            if hasattr(fecha, "date"):
                fecha_partido = fecha.date()
            else:
                continue

            if fecha_partido == hoy:

                if resultado not in [None, ""]:

                    equipos = partido.split(" vs ")

                    if len(equipos) == 2:

                        local = equipos[0]
                        visitante = equipos[1]

                        texto = (
                            f"⚽ {local} {resultado} {visitante}"
                        )

                    else:

                        texto = f"⚽ {partido} ({resultado})"

                else:

                    texto = (
                        f"🕒 {hora.strftime('%H:%M')} - {partido}"
                        if hasattr(hora, "strftime")
                        else f"{hora} - {partido}"
                    )

                partidos_hoy.append(texto)

        except:
            pass

if len(partidos_hoy) == 0:

    st.info(
        "No hay partidos programados para hoy."
    )

else:

    for p in partidos_hoy:

        st.write(p)

st.divider()

    st.subheader("Tabla General")

    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# PARTICIPANTES
# ==========================================

elif pagina == "👤 Participantes":

    jugador = st.selectbox(
        "Selecciona participante",
        list(participantes.keys())
    )

    st.subheader(
        f"Pronósticos de {jugador}"
    )

    df = pd.DataFrame(
    participantes[jugador]["pronosticos"]
    )

    df = df.drop(
        columns=["fila"],
        errors="ignore"
    )

    df = df.reset_index(drop=True)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# PARTIDOS
# ==========================================

elif pagina == "⚽ Partidos":

    primer_jugador = list(
        participantes.keys()
    )[0]

    lista_partidos = [
        p["Partido"]
        for p in participantes[primer_jugador]["pronosticos"]
    ]

    partido_seleccionado = st.selectbox(
        "Selecciona partido",
        lista_partidos
    )

    datos_partido = []

    for nombre, datos in participantes.items():

        for p in datos["pronosticos"]:

            if p["Partido"] == partido_seleccionado:

                datos_partido.append(
                    {
                        "Participante": nombre,
                        "Pronóstico": p["Pronóstico"],
                        "Resultado Oficial": p["Resultado Oficial"]
                    }
                )

    df_partido = pd.DataFrame(datos_partido)

    df_partido = df_partido.reset_index(drop=True)

    st.dataframe(
        df_partido,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# CALENDARIO
# ==========================================

elif pagina == "🗓️ Calendario":

    if "CALENDARIO" not in wb.sheetnames:

        st.warning(
            "No existe la hoja CALENDARIO"
        )

    else:

        ws_cal = wb["CALENDARIO"]

        calendario = []

        for fila in range(2, 500):

            partido = ws_cal[f"A{fila}"].value

            if partido is None:
                continue

            fecha = ws_cal[f"B{fila}"].value
            hora = ws_cal[f"C{fila}"].value
            resultado_final = ws_cal[f"D{fila}"].value
            if resultado_final is None:
                resultado_final = " "

            if fecha is not None:
                try:
                    fecha = fecha.strftime("%d/%m/%Y")
                except:
                    fecha = str(fecha)

            if hora is not None:
                try:
                    hora = hora.strftime("%H:%M")
                except:
                    hora = str(hora)

            calendario.append(
                {
                    "Partido": partido,
                    "Fecha": fecha,
                    "Hora (CDMX)": hora,
                    "Resultado Final": resultado_final
                }
            )

        st.subheader(
            "Calendario de partidos"
        )

        df_cal = pd.DataFrame(calendario)

        df_cal = df_cal.reset_index(drop=True)

        st.dataframe(
            df_cal,
            use_container_width=True,
            hide_index=True
        )


