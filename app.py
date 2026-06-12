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

    ranking.index = range(
        1,
        len(ranking) + 1
    )

    st.subheader("Tabla General")

    st.dataframe(
        ranking,
        use_container_width=True
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

    st.dataframe(
        df,
        use_container_width=True
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

    st.dataframe(
        pd.DataFrame(datos_partido),
        use_container_width=True
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
                    "Hora (CDMX)": hora
                }
            )

        st.subheader(
            "Calendario de partidos"
        )

        st.dataframe(
            pd.DataFrame(calendario),
            use_container_width=True
        )


