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
    wb_local = load_workbook(BytesIO(contenido_excel), data_only=True, read_only=True)

    if "RESULTADOS" not in wb_local.sheetnames:
        return None, None

    # 1. Mapear resultados oficiales de forma instantánea
    ws_resultados = wb_local["RESULTADOS"]
    resultados_oficiales = {}
    
    for fila_idx, row in enumerate(ws_resultados.iter_rows(min_row=6, max_row=200, min_col=2, max_col=6, values_only=True), start=6):
        if len(row) < 5:
            continue
        local, c, d, e, visitante = row[0], row[1], row[2], row[3], row[4]
        if local is None or visitante is None:
            continue
        resultados_oficiales[fila_idx] = determinar_resultado_celdas(c, d, e)

    # 2. Procesar participantes y extraer datos del Calendario en estructuras simples
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
        for fila_idx, row in enumerate(ws.iter_rows(min_row=6, max_row=200, min_col=2, max_col=6, values_only=True), start=6):
            if len(row) < 5:
                continue
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

    return participantes_local, calendario_local


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================

contenido_excel = cargar_excel()

if contenido_excel is None:
    st.error("No se pudo descargar el archivo desde Google Drive.")
    st.stop()

participantes, calendario_datos = procesar_todo_el_excel(contenido_excel)

if participantes is None:
    st.error("No existe la hoja RESULTADOS en el archivo.")
    st.stop()

# Calcular puntos
puntos = {nombre: sum(1 for p in datos["pronosticos"] if p["Acierto"]) for nombre, datos in participantes.items()}

# ==========================================
# RANKING
# ==========================================
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

    # Procesar métricas de avance
    total_partidos = 0
    partidos_jugados = 0
    partidos_hoy = []
    hoy = datetime.now(ZoneInfo("America/Mexico_City")).date()

    if calendario_datos:
        for c_partido in calendario_datos:
            partido = c_partido["partido"]
            fecha = c_partido["fecha"]
            hora = c_partido["hora"]
            resultado = c_partido["resultado"]

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

    # CÁLCULO DE LÍDER(ES) CON PRIMER NOMBRE SOLO
    puntaje_maximo = ranking["Puntos"].max() if not ranking.empty else -1
    
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

    # Tarjetas de Métricas Destacadas
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
            st.write(p)

    st.divider()
    st.subheader("Tabla General")

    # SOLO ORO: Ilumina únicamente a los que tengan el primer lugar absoluto o compartido
    def resaltar_solo_oro(row):
        if row["Puntos"] == puntaje_maximo and puntaje_maximo != -1:
            return ['background-color: #ffd700; color: #000000; font-weight: bold;'] * len(row)
        return [''] * len(row)

    ranking_estilizado = ranking.style.apply(resaltar_solo_oro, axis=1)
    st.dataframe(ranking_estilizado, use_container_width=True, hide_index=True)

# ==========================================
# PARTICIPANTES
# ==========================================

elif pagina == "👤 Participantes":
    jugador = st.selectbox("Selecciona participante", list(participantes.keys()))
    st.subheader(f"Pronósticos de {jugador}")

    df = pd.DataFrame(participantes[jugador]["pronosticos"])
    df = df.drop(columns=["fila", "Acierto"], errors="ignore").reset_index(drop=True)
    df = df[["Partido", "Pronóstico", "Resultado Oficial", "Estatus"]]

    # Formato Condicional para los aciertos (Verde) y fallos (Rojo)
    def color_estatus(val):
        if "✅" in str(val):
            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
        elif "❌" in str(val):
            return 'background-color: #f8d7da; color: #721c24;'
        return ''

    # ✨ CORRECCIÓN AQUÍ: Se cambió .applymap() por .map() compatible con Pandas 2.x
    df_estilizado = df.style.map(color_estatus, subset=["Estatus"])
    st.dataframe(df_estilizado, use_container_width=True, hide_index=True)

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
