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

inicio = time.time()

st.info(
    "⚽ La información se actualiza desde Google Drive. La carga inicial puede tardar algunos segundos."
)
st.caption(f"Página actualizada: {ultima_actualizacion} (hora CDMX)")

pagina = st.sidebar.radio(
    "Menú", ["🏆 Ranking", "👤 Participantes", "⚽ Partidos", "🗓️ Calendario"]
)

# ==========================================
# GOOGLE DRIVE 
# ==========================================

FILE_ID = "1svfBlcw4oOEltibwpv1c8I4h6sHmeq7z"
URL_DRIVE = f"https://docs.google.com/uc?export=download&id={FILE_ID}"


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
# FUNCIÓN AUXILIAR PARA DETERMINAR PRONÓSTICO
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
    # read_only=False pero usando iter_rows optimiza la velocidad manteniendo la compatibilidad
    wb_local = load_workbook(BytesIO(contenido_excel), data_only=True)

    if "RESULTADOS" not in wb_local.sheetnames:
        return None, None

    # 1. Mapear resultados oficiales de forma instantánea a un diccionario indexado por fila
    ws_resultados = wb_local["RESULTADOS"]
    resultados_oficiales = {}
    
    # Leemos desde la fila 6 hasta la 200 en un solo paso de memoria
    for fila_idx, row in enumerate(ws_resultados.iter_rows(min_row=6, max_row=200, min_col=2, max_col=6, values_only=True), start=6):
        local, c, d, e, visitante = row[0], row[1], row[2], row[3], row[4]
        if local is None or visitante is None:
            continue
        resultados_oficiales[fila_idx] = determinar_resultado_celdas(c, d, e)

    # 2. Procesar participantes de forma masiva
    participantes_local = {}

    for hoja in wb_local.sheetnames:
        if hoja.upper() in ["RESULTADOS", "CALENDARIO"]:
            continue

        ws = wb_local[hoja]
        nombre = ws["C2"].value or hoja
        desempate_local = ws["J15"].value
        desempate_visitante = ws["L15"].value

        pronosticos = []
        
        # Iteración ultra rápida sobre las filas de pronósticos del jugador
        for fila_idx, row in enumerate(ws.iter_rows(min_row=6, max_row=200, min_col=2, max_col=6, values_only=True), start=6):
            local, c, d, e, visitante = row[0], row[1], row[2], row[3], row[4]
            if local is None or visitante is None:
                continue

            resultado_oficial = resultados_oficiales.get(fila_idx)
            pronostico_jugador = determinar_resultado_celdas(c, d, e)

            es_acierto = (
                resultado_oficial is not None
                and pronostico_jugador == resultado_oficial
            )

            estatus_visual = "⌛ Pautado"
            if resultado_oficial is not None:
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

    return participantes_local, wb_local


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================

contenido_excel = cargar_excel()

if contenido_excel is None:
    st.error("No se pudo descargar el archivo desde Google Drive.")
    st.stop()

participantes, wb = procesar_todo_el_excel(contenido_excel)

if participantes is None:
    st.error("No existe la hoja RESULTADOS en el archivo.")
    st.stop()

# Calcular puntos de forma directa y limpia
puntos = {nombre: sum(1 for p in datos["pronosticos"] if p["Acierto"]) for nombre, datos in participantes.items()}

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
                "Desempate (Chequia vs México)": (
                    f"{int(float(participantes[nombre]['desempate_local']))}-{int(float(participantes[nombre]['desempate_visitante']))}"
                    if participantes[nombre]["desempate_local"] not in [None, ""]
                    and participantes[nombre]["desempate_visitante"] not in [None, ""]
                    else "-"
                ),
            }
            for nombre in participantes
        ]
    )

    ranking = ranking.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    st.subheader("📅 Partidos para hoy")

    total_partidos = 0
    partidos_jugados = 0
    partidos_hoy = []
    hoy = datetime.now(ZoneInfo("America/Mexico_City")).date()

    if "CALENDARIO" in wb.sheetnames:
        ws_cal = wb["CALENDARIO"]

        # Optimizamos también la lectura del Calendario completo en un solo viaje
        for row in ws_cal.iter_rows(min_row=2, max_row=500, min_col=1, max_col=4, values_only=True):
            partido, fecha, hora, resultado = row[0], row[1], row[2], row[3]
            if partido is None:
                continue

            total_partidos += 1
            if resultado not in [None, ""]:
                partidos_jugados += 1

            try:
                if hasattr(fecha, "date"):
                    fecha_partido = fecha.date()
                else:
                    continue

                if fecha_partido == hoy:
                    if resultado not in [None, ""]:
                        equipos = partido.split(" vs ")
                        if len(equipos) == 2:
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
            except:
                pass

    porcentaje = round(partidos_jugados * 100 / total_partidos, 1) if total_partidos > 0 else 0

    st.markdown(
        f"**⚽ Avance del torneo:** {partidos_jugados}/{total_partidos} partidos ({porcentaje}%)"
    )

    if len(partidos_hoy) == 0:
        st.info("No hay partidos programados para hoy.")
    else:
        for p in partidos_hoy:
            st.write(p)

    st.divider()
    st.subheader("Tabla General")
    st.table(ranking)

# ==========================================
# PARTICIPANTES
# ==========================================

elif pagina == "👤 Participantes":
    jugador = st.selectbox("Selecciona participante", list(participantes.keys()))
    st.subheader(f"Pronósticos de {jugador}")

    df = pd.DataFrame(participantes[jugador]["pronosticos"])
    df = df.drop(columns=["fila", "Acierto"], errors="ignore").reset_index(drop=True)
    df = df[["Partido", "Pronóstico", "Resultado Oficial", "Estatus"]]
    st.dataframe(df, use_container_width=True, hide_index=True)

# ==========================================
# PARTIDOS
# ==========================================

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
                        "¿Acertó?": "✅ SÍ" if p["Acierto"] else "❌ NO",
                    }
                )

    st.dataframe(pd.DataFrame(datos_partido).reset_index(drop=True), use_container_width=True, hide_index=True)

# ==========================================
# CALENDARIO
# ==========================================

elif pagina == "🗓️ Calendario":
    if "CALENDARIO" not in wb.sheetnames:
        st.warning("No existe la hoja CALENDARIO")
    else:
        ws_cal = wb["CALENDARIO"]
        calendario = []

        for row in ws_cal.iter_rows(min_row=2, max_row=500, min_col=1, max_col=4, values_only=True):
            partido, fecha, hora, resultado_final = row[0], row[1], row[2], row[3]
            if partido is None:
                continue

            resultado_final = resultado_final if resultado_final is not None else " "

            try:
                fecha = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else str(fecha)
            except:
                pass

            try:
                hora = hora.strftime("%H:%M") if hasattr(hora, "strftime") else str(hora)
            except:
                pass

            calendario.append(
                {
                    "Partido": partido,
                    "Fecha": fecha,
                    "Hora (CDMX)": hora,
                    "Resultado Final": resultado_final,
                }
            )

        st.subheader("Calendario de partidos")
        st.dataframe(pd.DataFrame(calendario).reset_index(drop=True), use_container_width=True, hide_index=True)
