"""
Demo: Monitoreo de perfil individual.

Pestaña 1 - Análisis individual: arrastras la base histórica del cliente
(PES o Personas, cada una con sus propias variables) y ves un descriptivo
del corte más reciente, con banderas de alerta simples.

Pestaña 2 - Bitácora: subes tu bitácora (se sigue llenando a mano, fuera
de la app) y ves, agregado, qué variables aparecen más seguido como causa
de deterioro en todos los casos revisados.

Ejecutar:
    streamlit run app_perfil.py
"""

import streamlit as st

from logica_perfil import (
    VARIABLES_CLAVE,
    cargar_bitacora,
    descriptivo_desde_historico,
    frecuencia_variables,
    leer_base_historica,
    leer_bitacora,
    tiempo_respuesta_promedio_dias,
)

st.set_page_config(page_title="Monitoreo de perfil individual", page_icon="🧾", layout="centered")

tab_individual, tab_bitacora = st.tabs(["🧾 Análisis individual", "📋 Bitácora"])


def mostrar_descriptivo(descriptivo: dict, modelo: str) -> None:
    fecha_txt = f" · corte {descriptivo['fecha_corte']}" if descriptivo.get("fecha_corte") is not None else ""
    st.markdown(f"### Descriptivo — {modelo}{fecha_txt}")
    st.caption(f"{descriptivo['n_periodos']} periodos cargados en el archivo")
    st.markdown(f"**{descriptivo['n_alertas']} de {descriptivo['n_total']}** variables clave en alerta")

    for var in descriptivo["variables"]:
        if var["nombre"] == "vive_con_familiares":
            st.write(f"ℹ️ **{var['etiqueta']}:** {var['valor']}")
        elif var["alerta"]:
            st.error(f"⚠️ **{var['etiqueta']}:** {var['valor']}")
        else:
            st.success(f"✅ **{var['etiqueta']}:** {var['valor']}")

    if descriptivo["adicionales"]:
        with st.expander("Otras variables del último corte"):
            for nombre, valor in descriptivo["adicionales"]:
                st.write(f"- {nombre}: {valor}")

    st.caption(
        "Este descriptivo organiza las variables — la interpretación y el "
        "justificativo los sigue haciendo el analista."
    )


# --- Pestaña 1: análisis individual ------------------------------------

with tab_individual:
    st.title("Análisis individual")
    st.caption("Arrastra la base histórica del cliente para ver su descriptivo.")

    col_pes, col_personas = st.columns(2)
    with col_pes:
        st.markdown("##### Base PES")
        archivo_pes = st.file_uploader(
            "Arrastra el archivo del cliente (PES)", type=["csv", "xlsx"], key="up_pes"
        )
    with col_personas:
        st.markdown("##### Base Personas")
        archivo_personas = st.file_uploader(
            "Arrastra el archivo del cliente (Personas)", type=["csv", "xlsx"], key="up_personas"
        )

    if archivo_pes and archivo_personas:
        st.warning("Sube un archivo a la vez (PES o Personas) para ver su descriptivo.")
    elif archivo_pes or archivo_personas:
        archivo = archivo_pes or archivo_personas
        modelo = "PES" if archivo_pes else "Personas"

        df_historico = leer_base_historica(archivo)
        st.markdown(f"##### Historial cargado — {modelo}")
        st.dataframe(df_historico, hide_index=True, use_container_width=True)

        columnas = {c.strip().lower(): c for c in df_historico.columns}
        if "fecha" in columnas and "score" in columnas and "dias_mora" in columnas:
            st.markdown("##### Tendencia")
            c1, c2 = st.columns(2)
            serie = df_historico.sort_values(columnas["fecha"]).set_index(columnas["fecha"])
            c1.line_chart(serie[[columnas["score"]]])
            c2.line_chart(serie[[columnas["dias_mora"]]])

        st.divider()
        descriptivo = descriptivo_desde_historico(df_historico)
        mostrar_descriptivo(descriptivo, modelo)
    else:
        st.info("Sube un archivo en alguno de los dos bloques para ver el descriptivo.")

# --- Pestaña 2: bitácora -------------------------------------------------

with tab_bitacora:
    st.title("Bitácora de monitoreo")
    st.caption("Sube tu bitácora para ver, agregado, dónde y por qué hay más alertas.")

    archivo_bitacora = st.file_uploader(
        "Arrastra la bitácora (CSV o Excel)", type=["csv", "xlsx"], key="up_bitacora"
    )

    if archivo_bitacora:
        bitacora = leer_bitacora(archivo_bitacora)
    else:
        bitacora = cargar_bitacora(".")
        st.caption("Mostrando datos de ejemplo — sube tu bitácora para ver la tuya.")

    col1, col2 = st.columns(2)
    col1.metric("Casos registrados", len(bitacora))
    tiempo_prom = tiempo_respuesta_promedio_dias(bitacora)
    col2.metric("Tiempo de respuesta promedio", f"{tiempo_prom} días" if tiempo_prom else "—")

    st.markdown("##### Variables más frecuentes en el deterioro")
    frecuencias = frecuencia_variables(bitacora)
    if frecuencias.empty:
        st.info("No hay registros para calcular la frecuencia.")
    else:
        etiquetas = {k: v["etiqueta"] for k, v in VARIABLES_CLAVE.items()}
        frecuencias.index = [etiquetas.get(v, v) for v in frecuencias.index]
        st.bar_chart(frecuencias)

    with st.expander("Ver todos los registros"):
        st.dataframe(bitacora, hide_index=True, use_container_width=True)
