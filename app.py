import io
import math
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Climix | Temperatura de Huánuco",
    page_icon="🌡️",
    layout="wide",
)

COL_FECHA = "Fecha"
COL_ANIO = "Año"
COL_MES = "Mes"
COL_MIN = "Temperatura mínima"
COL_MAX = "Temperatura máxima"
COL_PROM = "Temperatura promedio"
MAX_ARCHIVO_BYTES = 10 * 1024 * 1024
MAX_REGISTROS = 100_000


st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        --climix-bg: #0b1220;
        --climix-panel: #111d2d;
        --climix-panel-raised: #162438;
        --climix-border: rgba(148, 190, 216, 0.15);
        --climix-text: #e6f0f7;
        --climix-muted: #96aabd;
        --climix-blue: #38bdf8;
        --climix-turquoise: #21d4b0;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 86% 0%, rgba(20, 184, 166, 0.09), transparent 34%),
            radial-gradient(ellipse at 8% 4%, rgba(56, 189, 248, 0.11), transparent 30%),
            var(--climix-bg);
        color: var(--climix-text);
    }
    [data-testid="stHeader"] {
        background: rgba(11, 18, 32, 0.82);
        border-bottom: 1px solid rgba(148, 190, 216, 0.08);
    }
    .block-container {
        max-width: 1440px;
        padding: 2.2rem 2.4rem 2.8rem;
    }
    [data-testid="stVerticalBlock"] { gap: 1.2rem; }
    h1, h2, h3, p, label { font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    h2 { letter-spacing: -0.025em; }
    hr { border-color: rgba(148, 190, 216, 0.12); margin: 1.5rem 0; }

    .climix-hero {
        position: relative;
        overflow: hidden;
        padding: clamp(1.5rem, 3vw, 2.6rem);
        border: 1px solid rgba(125, 211, 252, 0.22);
        border-radius: 24px;
        background: linear-gradient(118deg, rgba(20, 39, 61, 0.98), rgba(13, 31, 48, 0.96) 58%, rgba(10, 47, 55, 0.92));
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }
    .climix-hero::before, .climix-hero::after {
        position: absolute;
        content: "";
        pointer-events: none;
        border: 1px solid rgba(103, 232, 249, 0.12);
        border-radius: 50%;
    }
    .climix-hero::before { width: 330px; height: 330px; right: -88px; top: -190px; }
    .climix-hero::after { width: 230px; height: 230px; right: -34px; top: -140px; }
    .hero-topline, .hero-location { display: flex; align-items: center; gap: 0.65rem; }
    .hero-topline { justify-content: space-between; margin-bottom: 2.1rem; }
    .hero-brand { display: flex; align-items: center; gap: 0.65rem; color: #f4fbff; font-size: 1rem; font-weight: 800; letter-spacing: 0.16em; }
    .brand-mark {
        display: grid; place-items: center; width: 2rem; height: 2rem;
        border: 1px solid rgba(125, 211, 252, 0.38); border-radius: 10px;
        color: #9be7ff; background: linear-gradient(145deg, rgba(56,189,248,.2), rgba(33,212,176,.12));
        font-size: 1.05rem; letter-spacing: 0;
    }
    .hero-status {
        padding: 0.42rem 0.72rem; border: 1px solid rgba(45, 212, 191, 0.25);
        border-radius: 999px; color: #a7f3df; background: rgba(13, 148, 136, 0.12);
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
    }
    .hero-eyebrow { margin: 0 0 0.45rem; color: #7dd3fc; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.18em; }
    .climix-hero h1 { margin: 0; color: #f3f9fd; font-size: clamp(2rem, 4vw, 3.1rem); font-weight: 720; letter-spacing: -0.045em; line-height: 1.08; }
    .hero-copy { max-width: 650px; margin: 0.8rem 0 1.25rem; color: #b7c8d7; font-size: 1.02rem; line-height: 1.65; }
    .hero-location { color: #a8becd; font-size: 0.82rem; }
    .hero-location span:first-child { color: #42d9bd; font-size: 1rem; }

    div[data-testid="stAlert"] {
        border: 1px solid rgba(56, 189, 248, 0.24);
        border-left: 3px solid var(--climix-blue);
        border-radius: 14px;
        background: linear-gradient(100deg, rgba(18, 54, 76, 0.68), rgba(17, 38, 56, 0.72));
        color: #c6d9e7;
    }
    div[data-testid="stAlert"] p { line-height: 1.6; }

    .section-heading { margin: 0.2rem 0 0.2rem; }
    .section-kicker { margin: 0 0 0.38rem; color: #49c7e9; font-size: 0.68rem; font-weight: 750; letter-spacing: 0.16em; }
    .section-heading h2 { margin: 0; color: var(--climix-text); font-size: 1.42rem; font-weight: 680; }
    .section-heading p { margin: 0.4rem 0 0; color: var(--climix-muted); font-size: 0.9rem; }

    div[data-testid="stMetric"] {
        min-height: 142px;
        padding: 1.3rem 1.45rem;
        border: 1px solid var(--climix-border);
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(22, 36, 56, 0.96), rgba(15, 28, 44, 0.96));
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255,255,255,.035);
    }
    [data-testid="stMetricLabel"] { color: #a9bdce !important; font-size: 0.82rem !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #f1f8fc !important; font-size: clamp(1.8rem, 2.8vw, 2.35rem) !important; font-weight: 700 !important; letter-spacing: -0.045em; }
    [data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

    div[data-testid="stSlider"] label, div[data-testid="stSelectbox"] label { color: #c3d1dc !important; font-weight: 600 !important; }
    div[data-testid="stSlider"] [data-baseweb="slider"] { padding-top: 0.3rem; }
    div[data-testid="stSlider"] [role="slider"] { border: 3px solid #dff7ff; box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.18); }
    div[data-testid="stSlider"] [data-testid="stTickBar"] { background: rgba(148, 190, 216, 0.2); }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border: 1px solid rgba(148, 190, 216, 0.2); border-radius: 11px; background: #142238;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within { border-color: var(--climix-blue); box-shadow: 0 0 0 2px rgba(56,189,248,.13); }

    div[data-testid="stPlotlyChart"] {
        overflow: hidden; padding: 0.65rem 0.7rem 0.3rem;
        border: 1px solid var(--climix-border); border-radius: 18px;
        background: linear-gradient(145deg, rgba(17, 29, 45, 0.9), rgba(13, 25, 40, 0.94));
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.14);
    }
    div[data-testid="stDataFrame"] {
        overflow: hidden; border: 1px solid var(--climix-border); border-radius: 15px;
        background: rgba(17, 29, 45, 0.86);
    }
    div[data-testid="stDataFrame"] [role="grid"] { background: transparent; }
    div[data-testid="stCaptionContainer"] p { color: #8499aa; }

    @media (max-width: 760px) {
        .block-container { padding: 1.1rem 1rem 2rem; }
        .climix-hero { border-radius: 18px; }
        .hero-topline { margin-bottom: 1.5rem; }
        .hero-status { font-size: 0.58rem; }
        .hero-copy { font-size: 0.94rem; }
        div[data-testid="stMetric"] { min-height: 115px; padding: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ALIAS_COLUMNAS = {
    COL_FECHA: {"fecha", "date", "datetime"},
    COL_MIN: {
        "temperaturaminima",
        "temperaturamin",
        "tempminima",
        "tempmin",
        "tempminc",
        "tmin",
        "tminc",
        "t2mmin",
        "temperaturaminimac",
        "minima",
    },
    COL_MAX: {
        "temperaturamaxima",
        "temperaturamax",
        "tempmaxima",
        "tempmax",
        "tempmaxc",
        "tmax",
        "tmaxc",
        "t2mmax",
        "temperaturamaximac",
        "maxima",
    },
    COL_PROM: {
        "temperaturapromedio",
        "temperaturaprom",
        "temperaturamedia",
        "temppromedio",
        "temppromedioc",
        "tempmedia",
        "tempmeanc",
        "tempavgc",
        "tmean",
        "tmeanc",
        "tavg",
        "tavgc",
        "t2mavg",
        "promedio",
        "media",
    },
}


def normalizar_encabezado(valor):
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = texto.lower().replace("°", " ")
    texto = re.sub(r"\b(?:c|celsius)\b", " ", texto)
    return re.sub(r"[^a-z0-9]+", "", texto)


def convertir_numero(valor):
    if pd.isna(valor):
        return float("nan")
    if isinstance(valor, (int, float, np.number)):
        return float(valor)

    texto = str(valor).strip().replace("\u00a0", "").replace(" ", "")
    if not texto:
        return float("nan")
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return float("nan")


def parsear_fechas(serie):
    try:
        return pd.to_datetime(serie, errors="coerce", dayfirst=True, format="mixed")
    except (TypeError, ValueError):
        # Compatibilidad con versiones anteriores de pandas.
        return pd.to_datetime(serie, errors="coerce", dayfirst=True)


def leer_registros_csv(contenido):
    if not contenido:
        raise ValueError("El archivo está vacío.")
    if len(contenido) > MAX_ARCHIVO_BYTES:
        raise ValueError("El archivo supera el límite de 10 MB.")

    tabla = None
    errores_lectura = []
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            tabla = pd.read_csv(
                io.BytesIO(contenido),
                sep=None,
                engine="python",
                encoding=codificacion,
                on_bad_lines="error",
            )
            break
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            errores_lectura.append(error)

    if tabla is None:
        raise ValueError(
            "No se pudo leer el CSV. Verifica los encabezados y el separador de las columnas."
        ) from errores_lectura[-1]
    if tabla.empty:
        raise ValueError("El CSV tiene encabezados, pero no contiene registros.")
    if len(tabla) > MAX_REGISTROS:
        raise ValueError(f"El archivo supera el límite de {MAX_REGISTROS:,} registros.")

    columnas_encontradas = {}
    columnas_repetidas = []
    for columna in tabla.columns:
        # pandas agrega sufijos como .1 cuando el CSV repite un encabezado.
        nombre_sin_sufijo = re.sub(r"\.\d+$", "", str(columna))
        normalizada = normalizar_encabezado(nombre_sin_sufijo)
        canonica = next(
            (nombre for nombre, alias in ALIAS_COLUMNAS.items() if normalizada in alias),
            None,
        )
        if canonica:
            if canonica in columnas_encontradas:
                columnas_repetidas.append(canonica)
            else:
                columnas_encontradas[canonica] = columna

    requeridas = [COL_FECHA, COL_MIN, COL_MAX]
    faltantes = [nombre for nombre in requeridas if nombre not in columnas_encontradas]
    if faltantes:
        nombres = ", ".join(f"`{nombre}`" for nombre in faltantes)
        raise ValueError(
            f"Faltan columnas obligatorias: {nombres}. Descarga la plantilla para ver el formato."
        )
    if columnas_repetidas:
        repetidas = ", ".join(sorted(set(columnas_repetidas)))
        raise ValueError(f"Hay más de una columna para estas variables: {repetidas}.")

    datos = pd.DataFrame(
        {
            nombre: tabla[columna].copy()
            for nombre, columna in columnas_encontradas.items()
        }
    )
    datos[COL_FECHA] = parsear_fechas(datos[COL_FECHA].astype("string").str.strip())
    for nombre in (COL_MIN, COL_MAX, COL_PROM):
        if nombre in datos:
            datos[nombre] = datos[nombre].map(convertir_numero)

    errores = []
    fechas_invalidas = datos[COL_FECHA].isna()
    if fechas_invalidas.any():
        filas = ", ".join(str(i + 2) for i in datos.index[fechas_invalidas][:5])
        errores.append(f"fechas vacías o inválidas en la(s) fila(s) {filas}")

    for nombre in (COL_MIN, COL_MAX, COL_PROM):
        if nombre not in datos:
            continue
        valores = datos[nombre]
        invalidos = valores.isna() | ~valores.map(math.isfinite)
        if invalidos.any():
            filas = ", ".join(str(i + 2) for i in datos.index[invalidos][:5])
            errores.append(f"valores vacíos o no numéricos en `{nombre}` (fila(s) {filas})")
        fuera_de_rango = valores.notna() & ((valores < -90) | (valores > 60))
        if fuera_de_rango.any():
            filas = ", ".join(str(i + 2) for i in datos.index[fuera_de_rango][:5])
            errores.append(f"valores fuera del rango de -90 a 60 °C en `{nombre}` (fila(s) {filas})")

    min_mayor_max = (
        datos[COL_MIN].notna()
        & datos[COL_MAX].notna()
        & (datos[COL_MIN] > datos[COL_MAX])
    )
    if min_mayor_max.any():
        filas = ", ".join(str(i + 2) for i in datos.index[min_mayor_max][:5])
        errores.append(f"la temperatura mínima supera a la máxima en la(s) fila(s) {filas}")

    if COL_PROM in datos:
        promedio_fuera = (
            datos[COL_PROM].notna()
            & datos[COL_MIN].notna()
            & datos[COL_MAX].notna()
            & ((datos[COL_PROM] < datos[COL_MIN]) | (datos[COL_PROM] > datos[COL_MAX]))
        )
        if promedio_fuera.any():
            filas = ", ".join(str(i + 2) for i in datos.index[promedio_fuera][:5])
            errores.append(f"el promedio está fuera del intervalo mínimo-máximo en la(s) fila(s) {filas}")

    fechas_duplicadas = datos[COL_FECHA].notna() & datos[COL_FECHA].duplicated(keep=False)
    if fechas_duplicadas.any():
        filas = ", ".join(str(i + 2) for i in datos.index[fechas_duplicadas][:5])
        errores.append(f"hay fechas duplicadas en la(s) fila(s) {filas}; usa una fila por fecha")

    if errores:
        raise ValueError("No se cargó el archivo: " + "; ".join(errores) + ".")

    if COL_PROM not in datos:
        datos[COL_PROM] = (datos[COL_MIN] + datos[COL_MAX]) / 2
    datos[COL_ANIO] = datos[COL_FECHA].dt.year.astype(int)
    datos[COL_MES] = datos[COL_FECHA].dt.month.astype(int)
    return datos.sort_values(COL_FECHA).reset_index(drop=True)


RUTA_CSV_NASA_POWER = (
    Path(__file__).resolve().parent
    / "datos"
    / "climix_nasa_power_huanuco_2015_2025_limpio.csv"
)


@st.cache_data
def cargar_datos_automaticos(ruta_csv, version_archivo):
    # version_archivo invalida la caché si cambia el CSV del proyecto.
    return leer_registros_csv(Path(ruta_csv).read_bytes())


if not RUTA_CSV_NASA_POWER.is_file():
    st.error(
        "No se encontró el CSV de NASA POWER. Verifica que exista en "
        f"`{RUTA_CSV_NASA_POWER.relative_to(Path(__file__).resolve().parent)}`."
    )
    st.stop()

try:
    df = cargar_datos_automaticos(
        str(RUTA_CSV_NASA_POWER), RUTA_CSV_NASA_POWER.stat().st_mtime_ns
    )
except (OSError, ValueError) as error:
    st.error(f"No se pudo cargar el CSV local de NASA POWER: {error}")
    st.stop()

# Encabezado visual
st.markdown(
    """
    <section class="climix-hero">
        <div class="hero-topline">
            <div class="hero-brand"><span class="brand-mark">◒</span> CLIMIX</div>
            <span class="hero-status">DATOS NASA POWER</span>
        </div>
        <p class="hero-eyebrow">CLIMA · DATOS · CONTEXTO</p>
        <h1>Temperaturas de Huánuco</h1>
        <p class="hero-copy">Explora la evolución diaria de la temperatura estimada para una celda de NASA POWER y compara periodos en una vista interactiva.</p>
        <div class="hero-location"><span>●</span> Huánuco, Perú <span>·</span> Punto/celda NASA POWER · Serie diaria 2015–2025</div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.info(
    "**Fuente y alcance:** NASA POWER, serie diaria de un punto/celda en Huánuco "
    "(-9.9306, -76.2422), basada en el reanálisis MERRA-2. Representa la celda "
    "asociada a esas coordenadas; no describe todo el departamento de Huánuco ni "
    "son mediciones directas de una estación meteorológica. T2M_AVG es el promedio "
    "derivado de T2M_MIN y T2M_MAX."
)

st.divider()

# Selector de rango: se conserva el periodo de consulta existente.
st.markdown(
    '<div class="section-heading"><div class="section-kicker">01 / EXPLORAR</div>'
    '<h2>Consulta de registros</h2><p>Elige el periodo para actualizar los indicadores y la serie diaria.</p></div>',
    unsafe_allow_html=True,
)
años_disponibles = sorted(df[COL_ANIO].unique().tolist())
if len(años_disponibles) > 1:
    periodo = st.select_slider(
        "Selecciona el periodo de consulta:",
        options=años_disponibles,
        value=(años_disponibles[0], años_disponibles[-1]),
    )
else:
    anio_unico = st.selectbox("Año de consulta:", años_disponibles)
    periodo = (anio_unico, anio_unico)
datos_filtrados = df[df[COL_ANIO].between(periodo[0], periodo[1])]

# Indicadores del periodo seleccionado
st.markdown(
    '<div class="section-heading"><div class="section-kicker">02 / RESUMEN DEL PERIODO</div>'
    '<h2>Indicadores de temperatura</h2><p>Valores calculados para el rango de años seleccionado.</p></div>',
    unsafe_allow_html=True,
)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Temperatura mínima",
        f"{datos_filtrados[COL_MIN].min():.1f} °C",
        border=True,
    )
with col2:
    st.metric(
        "Temperatura máxima",
        f"{datos_filtrados[COL_MAX].max():.1f} °C",
        border=True,
    )
with col3:
    st.metric(
        "Temperatura promedio",
        f"{datos_filtrados[COL_PROM].mean():.1f} °C",
        border=True,
    )

st.divider()

# Gráfico diario interactivo
st.markdown(
    '<div class="section-heading"><div class="section-kicker">03 / SERIE HISTÓRICA DIARIA</div>'
    '<h2>Variación diaria de temperatura</h2><p>Temperaturas mínima, máxima y promedio para cada fecha del periodo.</p></div>',
    unsafe_allow_html=True,
)
datos_grafico = datos_filtrados.sort_values(COL_FECHA).copy()
etiquetas_fecha = [fecha.strftime("%d/%m/%Y") for fecha in datos_grafico[COL_FECHA]]

fig = go.Figure()
for columna, nombre, color in (
    (COL_MIN, "Temperatura mínima", "#38BDF8"),
    (COL_MAX, "Temperatura máxima", "#21D4B0"),
    (COL_PROM, "Temperatura promedio", "#B9D8EC"),
):
    fig.add_trace(
        go.Scatter(
            x=datos_grafico[COL_FECHA],
            y=datos_grafico[columna],
            customdata=etiquetas_fecha,
            name=nombre,
            mode="lines",
            line={"color": color, "width": 2.8},
            hovertemplate=(
                f"<b>%{{customdata}}</b><br>{nombre}: "
                "%{y:.1f} °C<extra></extra>"
            ),
        )
    )

fig.update_layout(
    template="plotly_dark",
    height=440,
    margin={"l": 14, "r": 18, "t": 22, "b": 14},
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font={"family": "Inter, ui-sans-serif, system-ui, sans-serif", "color": "#AFC2D1", "size": 12},
    hovermode="x unified",
    hoverlabel={"bgcolor": "#132337", "bordercolor": "#31536A", "font": {"color": "#F1F8FC"}},
    legend={"title": {"text": "Indicadores"}, "orientation": "h", "y": -0.2, "font": {"color": "#C1D2DE"}},
    xaxis={
        "title": "Año",
        "tick0": "2015-01-01",
        "dtick": "M12",
        "tickformat": "%Y",
        "showgrid": False,
        "automargin": True,
        "tickfont": {"color": "#91A8BA"},
        "title_font": {"color": "#AFC2D1"},
        "linecolor": "rgba(148, 190, 216, 0.2)",
        "ticks": "outside",
    },
    yaxis={
        "title": "Temperatura (°C)",
        "gridcolor": "rgba(148, 190, 216, 0.12)",
        "zeroline": False,
        "tickfont": {"color": "#91A8BA"},
        "title_font": {"color": "#AFC2D1"},
    },
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

st.divider()

# Comparación anual y diferencia de promedios
st.markdown(
    '<div class="section-heading"><div class="section-kicker">04 / COMPARAR</div>'
    '<h2>Comparación de periodos</h2><p>Contrasta los promedios de dos años y revisa la diferencia resultante.</p></div>',
    unsafe_allow_html=True,
)
col_a, col_b = st.columns(2)
with col_a:
    año_a = st.selectbox("Primer periodo:", años_disponibles, index=0)
with col_b:
    año_b = st.selectbox("Segundo periodo:", años_disponibles, index=len(años_disponibles) - 1)

comparacion = df[df[COL_ANIO].isin([año_a, año_b])]
resumen = (
    comparacion.groupby(COL_ANIO)
    .agg({COL_MIN: "mean", COL_MAX: "mean", COL_PROM: "mean"})
    .round(2)
)
st.dataframe(resumen, width="stretch")

if año_a != año_b:
    diferencia = resumen.loc[año_b, COL_PROM] - resumen.loc[año_a, COL_PROM]
    st.metric(
        f"Diferencia del promedio: {año_b} respecto a {año_a}",
        f"{diferencia:+.2f} °C",
        border=True,
    )

st.divider()
st.caption(
    f"CLIMIX | NASA POWER / MERRA-2 · {len(df):,} registros diarios · "
    "estimaciones de una celda para Huánuco, no mediciones de estación."
)
