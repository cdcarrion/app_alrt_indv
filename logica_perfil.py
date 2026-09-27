"""
Lógica de negocio de "Monitoreo de perfil individual" -- separada de la
interfaz para poder probarla sin Streamlit.

Cubre las 2 ideas descritas:
1. Subes la base histórica de un cliente (PES o Personas, cada una con sus
   propias variables) y se arma un descriptivo del corte más reciente, con
   reglas simples de alerta, para ver de un vistazo si hay deterioro.
2. Subes la bitácora (se sigue llenando a mano, fuera de la app) y se
   analiza agregado: qué variables aparecen más seguido como causa de
   deterioro en todos los casos revisados.
"""

from pathlib import Path

import pandas as pd

MODELOS = ["PES", "Personas"]

# Variables clave que se resumen con una regla simple de alerta.
# AJUSTA LOS UMBRALES a los reales de cada modelo cuando los tengas
# definidos -- estos son valores de ejemplo para que la demo funcione.
# regla:
#   "menor_es_alerta" -> alerta si el valor es MENOR al umbral
#   "mayor_es_alerta" -> alerta si el valor es MAYOR al umbral
#   "contexto"        -> se muestra, pero no dispara alerta por sí sola
VARIABLES_CLAVE = {
    "score": {"etiqueta": "Score", "tipo": "numero", "umbral": 500, "regla": "menor_es_alerta"},
    "dias_mora": {"etiqueta": "Días mora", "tipo": "numero", "umbral": 30, "regla": "mayor_es_alerta"},
    "saldo_pasivo": {
        "etiqueta": "Saldo cuentas del pasivo",
        "tipo": "numero",
        "umbral": 50,
        "regla": "menor_es_alerta",
    },
    "tarjetas_vigentes": {
        "etiqueta": "Tarjetas vigentes",
        "tipo": "entero",
        "umbral": 1,
        "regla": "menor_es_alerta",
    },
    "operaciones_vigentes": {
        "etiqueta": "Operaciones vigentes",
        "tipo": "entero",
        "umbral": 1,
        "regla": "menor_es_alerta",
    },
    "vive_con_familiares": {
        "etiqueta": "Vive con familiares",
        "tipo": "si_no",
        "umbral": None,
        "regla": "contexto",
    },
}


def evaluar_variable(nombre: str, valor) -> dict:
    """Aplica la regla simple de alerta a una variable clave."""
    cfg = VARIABLES_CLAVE[nombre]
    alerta = False
    if valor is not None and cfg["regla"] == "menor_es_alerta":
        alerta = valor < cfg["umbral"]
    elif valor is not None and cfg["regla"] == "mayor_es_alerta":
        alerta = valor > cfg["umbral"]
    return {"nombre": nombre, "etiqueta": cfg["etiqueta"], "valor": valor, "alerta": alerta}


def construir_descriptivo(valores_clave: dict, variables_adicionales: list[tuple[str, str]]) -> dict:
    """Arma el descriptivo de un cliente: variables clave evaluadas +
    variables adicionales (informativas, sin regla de alerta porque no
    sabemos su umbral de antemano)."""
    evaluadas = [
        evaluar_variable(nombre, valor)
        for nombre, valor in valores_clave.items()
        if nombre in VARIABLES_CLAVE
    ]
    n_alertas = sum(1 for e in evaluadas if e["alerta"])
    return {
        "variables": evaluadas,
        "n_alertas": n_alertas,
        "n_total": len(evaluadas),
        "adicionales": variables_adicionales,
    }


# --- Idea 1: base histórica de un cliente (PES o Personas) -------------


def leer_base_historica(archivo) -> pd.DataFrame:
    """Lee el archivo que arrastró el usuario (CSV o Excel). 'archivo' es
    el objeto que entrega st.file_uploader (trae .name)."""
    if archivo.name.lower().endswith(".csv"):
        return pd.read_csv(archivo)
    return pd.read_excel(archivo)


def descriptivo_desde_historico(df: pd.DataFrame) -> dict:
    """A partir de la base histórica de un cliente (una fila por corte),
    arma el descriptivo con el corte más reciente. Las columnas que
    coinciden con VARIABLES_CLAVE se evalúan con su regla; el resto queda
    como variables adicionales (informativas)."""
    columnas = {c.strip().lower(): c for c in df.columns}

    if "fecha" in columnas:
        df = df.sort_values(columnas["fecha"])
    ultima = df.iloc[-1]

    valores_clave = {clave: ultima[col] for clave, col in columnas.items() if clave in VARIABLES_CLAVE}
    otras = [c for c in df.columns if c.strip().lower() not in VARIABLES_CLAVE and c.strip().lower() != "fecha"]

    descriptivo = construir_descriptivo(valores_clave, [(c, ultima[c]) for c in otras])
    descriptivo["fecha_corte"] = ultima[columnas["fecha"]] if "fecha" in columnas else None
    descriptivo["n_periodos"] = len(df)
    return descriptivo


# --- Idea 2: bitácora de monitoreo (se llena a mano, se sube a la app) --

COLUMNAS_BITACORA = ["id", "fecha_recibido", "fecha_entrega", "variables_deterioro", "justificativo"]


def _ruta_bitacora(carpeta: str) -> Path:
    return Path(carpeta) / "bitacora_perfiles.csv"


def cargar_bitacora(carpeta: str = ".") -> pd.DataFrame:
    """Carga la bitácora de ejemplo del disco (fallback para la demo
    cuando el usuario todavía no ha subido la suya)."""
    ruta = _ruta_bitacora(carpeta)
    if not ruta.exists():
        return pd.DataFrame(columns=COLUMNAS_BITACORA)
    return leer_bitacora(ruta.open("rb"), ruta.name)


def leer_bitacora(archivo, nombre_archivo: str | None = None) -> pd.DataFrame:
    """Lee la bitácora subida por el usuario (CSV o Excel) y normaliza las
    2 columnas de fecha."""
    nombre = nombre_archivo or getattr(archivo, "name", "")
    if nombre.lower().endswith(".csv"):
        df = pd.read_csv(archivo, dtype=str)
    else:
        df = pd.read_excel(archivo, dtype=str)
    df["fecha_recibido"] = pd.to_datetime(df["fecha_recibido"], errors="coerce")
    df["fecha_entrega"] = pd.to_datetime(df["fecha_entrega"], errors="coerce")
    return df


def frecuencia_variables(bitacora: pd.DataFrame) -> pd.Series:
    """Cuenta cuántas veces aparece cada variable en la columna
    variables_deterioro (separadas por ';'), de más a menos frecuente."""
    if bitacora.empty or "variables_deterioro" not in bitacora:
        return pd.Series(dtype=int)
    partes = bitacora["variables_deterioro"].dropna().str.split(";")
    explotadas = partes.explode().str.strip()
    explotadas = explotadas[explotadas != ""]
    return explotadas.value_counts()


def tiempo_respuesta_promedio_dias(bitacora: pd.DataFrame):
    """Promedio de días entre fecha_recibido y fecha_entrega. None si no
    hay datos suficientes."""
    if bitacora.empty:
        return None
    dias = (bitacora["fecha_entrega"] - bitacora["fecha_recibido"]).dt.days.dropna()
    if dias.empty:
        return None
    return round(dias.mean(), 1)
