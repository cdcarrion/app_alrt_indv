"""
Genera datos de ejemplo (ILUSTRATIVOS, no reales) para probar la demo de
monitoreo de perfil individual:
- historico_pes_ejemplo.csv / historico_personas_ejemplo.csv: el histórico
  de UN cliente (para arrastrar en la pestaña "Análisis individual").
- bitacora_perfiles.csv: la bitácora de varios casos (para la pestaña
  "Bitácora").

Uso:
    python generar_datos_demo_perfil.py
"""

import random
from datetime import timedelta

import pandas as pd

random.seed(7)

VARIABLES = [
    "score",
    "dias_mora",
    "saldo_pasivo",
    "tarjetas_vigentes",
    "operaciones_vigentes",
]
# "score" y "dias_mora" aparecen más seguido a propósito, para que el
# gráfico de frecuencia se vea con un patrón claro en la demo.
PESOS = [3, 3, 2, 1, 1]

JUSTIFICATIVOS = [
    "Deterioro por mora reciente en otra entidad.",
    "Score bajó por nueva consulta de crédito.",
    "Reducción de saldo disponible en cuenta del pasivo.",
    "Cierre de productos vigentes con el banco.",
]


def id_ficticio(i: int) -> str:
    return f"{1700000000 + i}"


def generar_bitacora(n: int = 25) -> pd.DataFrame:
    inicio = pd.Timestamp("2026-05-01")
    filas = []
    for i in range(n):
        fecha_recibido = inicio + timedelta(days=random.randint(0, 110))
        fecha_entrega = fecha_recibido + timedelta(days=random.randint(1, 5))
        n_vars = random.choice([1, 1, 2, 2, 3])
        vars_caso = random.choices(VARIABLES, weights=PESOS, k=n_vars)
        vars_caso = sorted(set(vars_caso))  # sin duplicados dentro del mismo caso
        filas.append(
            {
                "id": id_ficticio(i),
                "fecha_recibido": fecha_recibido.strftime("%Y-%m-%d"),
                "fecha_entrega": fecha_entrega.strftime("%Y-%m-%d"),
                "variables_deterioro": ";".join(vars_caso),
                "justificativo": random.choice(JUSTIFICATIVOS),
            }
        )
    return pd.DataFrame(filas)


def generar_historico_cliente(extra_columnas: dict, n_meses: int = 12) -> pd.DataFrame:
    """Histórico mensual de UN cliente, con una tendencia de deterioro leve
    para que el descriptivo y la tendencia se vean con algo que contar."""
    fechas = pd.date_range(end="2026-08-31", periods=n_meses, freq="ME")
    score = 750.0
    dias_mora = 0.0
    saldo_pasivo = 900.0
    tarjetas = 3
    filas = []
    for i, fecha in enumerate(fechas):
        score = max(300, score + random.uniform(-28, 6))
        dias_mora = max(0, dias_mora + random.uniform(-1, 7))
        saldo_pasivo = max(0, saldo_pasivo * (1 + random.uniform(-0.09, 0.02)))
        if i == n_meses - 2:
            tarjetas = max(0, tarjetas - 1)  # cierra una tarjeta hacia el final
        fila = {
            "fecha": fecha.strftime("%Y-%m-%d"),
            "score": round(score),
            "dias_mora": round(dias_mora),
            "saldo_pasivo": round(saldo_pasivo, 2),
            "tarjetas_vigentes": tarjetas,
            "operaciones_vigentes": 2,
            "vive_con_familiares": "Sí",
        }
        fila.update(extra_columnas)
        filas.append(fila)
    return pd.DataFrame(filas)


if __name__ == "__main__":
    bitacora = generar_bitacora()
    bitacora.to_csv("bitacora_perfiles.csv", index=False)
    print(f"Listo: bitacora_perfiles.csv ({len(bitacora)} registros de ejemplo)")

    historico_pes = generar_historico_cliente(
        {"sector": "FARMACÉUTICO", "calificacion_buro": "B"}
    )
    historico_personas = generar_historico_cliente(
        {"relacion_laboral": "Dependiente", "calificacion_buro": "C"}
    )
    historico_pes.to_csv("historico_pes_ejemplo.csv", index=False)
    historico_personas.to_csv("historico_personas_ejemplo.csv", index=False)
    print("Listo: historico_pes_ejemplo.csv, historico_personas_ejemplo.csv")
    print("Último corte PES:")
    print(historico_pes.tail(1).to_string(index=False))
