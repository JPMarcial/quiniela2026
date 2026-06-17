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
# GOOGLE DRIVE (OPTIMIZADO PARA TIEMPO DE CARGA)
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


@st.cache_data(ttl=60)  # ⚡ OPTIMIZACIÓN: Cambiado de 86400 a 60 para actualizar en tiempo real sin romper el caché
def procesar_todo_el_excel(contenido_excel):
    wb_local = load_workbook(BytesIO(contenido_excel), data_only=True)

    if "RESULTADOS" not in wb_local.sheetnames:
        return None, None

    ws_resultados = wb_local["RESULTADOS"]
    participantes_local = {}

    for hoja in wb_local.sheetnames:
        if hoja.upper() in ["RESULTADOS", "CALENDARIO"]:
            continue

        ws = wb_local[hoja]
        nombre = ws["C2"].value or hoja

        desempate_local = ws["J15"].value
        desempate_visitante = ws["L15"].value

        pronosticos = []
        for fila in range(6, 200):
            local = ws[f"B{fila}"].value
            visitante = ws[f"F{fila}"].value

            if local is None or visitante is None:
                continue

            resultado_oficial = leer_resultado(ws_resultados, fila)
            pronostico_jugador = leer_resultado(ws, fila)

            es_acierto = (
                resultado_oficial is not None
                and pronostico_jugador == resultado_oficial
            )

            # 📊 OPTIMIZACIÓN VISUAL: Taches y palomitas asignados directamente aquí
            estatus_visual = "⌛ Pautado"
            if resultado_oficial is not None:
                estatus_visual = "✅ ¡Acertó!" if es_acierto else "❌ Falló"

            pronosticos.append(
                {
                    "fila": fila,
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
# EJECUCIÓN PRINCIPAL (UNA SOLA LECTURA DE STREAM)
# ==========================================

contenido_excel = cargar_excel()

if contenido_excel is None:
    st.error("No se pudo descargar el archivo desde Google Drive.")
    st.stop()

participantes, wb = procesar_todo_el_excel(contenido_excel)

if participantes is None:
    st.error("No existe la hoja RESULTADOS en el archivo.")
    st.stop()

# Calcular puntos
puntos = {}
for nombre, datos in participantes.items():
    puntos[nombre] = sum(1 for p in datos["pronosticos"] if p["Acierto"])

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
                    if participantes[nombre]["desempate_local"]
                    not in [None, ""]
                    and participantes[nombre]["desempate_visitante"]
                    not in [None, ""]
                    else "-"
                ),
            }
            for nombre in participantes
        ]
    )

    ranking = ranking.sort_values(by="Puntos", ascending=False)
    ranking = ranking.reset_index(drop=True)

    from datetime import date

    st.subheader("📅 Partidos para hoy")

    total_partidos = 0
    partidos_jugados = 0

    if "CALENDARIO" in wb.sheetnames:
        ws_cal = wb["CALENDARIO"]

        for fila in range(2, 500):
            partido = ws_cal[f"A{fila}"].value
            if partido is None:
                continue

            total_partidos += 1
            resultado = ws_cal[f"D{fila}"].value

            if resultado not in [None, ""]:
                partidos_jugados += 1

    porcentaje = (
        round(partidos_jugados * 100 / total_partidos, 1)
        if total_partidos > 0
        else 0
    )

    st.markdown(
        f"**⚽ Avance del torneo:** {partidos_jugados}/{total_partidos} partidos ({porcentaje}%)"
    )

    from datetime import datetime
    from zoneinfo import ZoneInfo

    hoy = datetime.now(ZoneInfo("America/Mexico_City")).date()
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
                    # ✨ TU LÓGICA DIRECTA: Balón (⚽) si tiene resultado, Reloj (🕒) si está pendiente
                    if resultado not in [None, ""]:
                        equipos = partido.split(" vs ")

                        if len(equipos) == 2:
                            local = equipos[0]
                            visitante = equipos[1]
                            texto = f"⚽ {local} {resultado} {visitante}"
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
    jugador = st.selectbox(
        "Selecciona participante", list(participantes.keys())
    )
    st.subheader(f"Pronósticos de {jugador}")

    df = pd.DataFrame(participantes[jugador]["pronosticos"])
    df = df.drop(columns=["fila", "Acierto"], errors="ignore")
    df = df.reset_index(drop=True)

    # Reordenamiento de columnas agregando la nueva columna 'Estatus' (✅ / ❌)
    df = df[["Partido", "Pronóstico", "Resultado Oficial", "Estatus"]]
    st.dataframe(df, use_container_width=True, hide_index=True)

# ==========================================
# PARTIDOS
# ==========================================

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
                        "¿Acertó?": "✅ SÍ" if p["Acierto"] else "❌ NO",  # 📊 Agregado visual aquí también
                    }
                )

    df_partido = pd.DataFrame(datos_partido)
    df_partido = df_partido.reset_index(drop=True)

    st.dataframe(df_partido, use_container_width=True, hide_index=True)

# ==========================================
# CALENDARIO
# ==========================================

elif pagina == "🗓️ Calendario":
    if "CALENDARIO" not in wb.sheetnames:
        st.warning("No existe la hoja CALENDARIO")
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
                    "Resultado Final": resultado_final,
                }
            )

        st.subheader("Calendario de partidos")
        df_cal = pd.DataFrame(calendario)
        df_cal = df_cal.reset_index(drop=True)

        st.dataframe(df_cal, use_container_width=True, hide_index=True)
