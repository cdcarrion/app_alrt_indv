# Demo: Monitoreo de perfil individual

**Pestaña 1 — Análisis individual**
Dos bloques para arrastrar el archivo del cliente: uno para la base PES,
otro para la base Personas (CSV o Excel). El archivo esperado es el
histórico del cliente: una fila por corte (columna `fecha`) y una columna
por variable. Al subirlo, la app muestra:
- La tabla completa que subiste.
- La tendencia de score y días mora en el tiempo (si esas columnas están).
- El descriptivo del corte más reciente: las 6 variables clave con ✅/⚠️
  automático, y el resto de columnas del archivo como "otras variables"
  (informativas, sin bandera automática).

**Pestaña 2 — Bitácora**
Arrastras tu bitácora (id, fecha de recepción y entrega del mail, variables
que deterioran, justificativo) — la sigues llenando a mano en Excel como
hasta ahora, aquí solo la subes. La app muestra casos registrados, tiempo
de respuesta promedio, y un gráfico de qué variables se repiten más como
causa de deterioro. Si no subes nada, muestra datos de ejemplo.

## Cómo correrla

```
pip install -r requirements.txt
python -m streamlit run app_perfil.py
```

Ya vienen generados 3 archivos de ejemplo para probar arrastrándolos:
`historico_pes_ejemplo.csv`, `historico_personas_ejemplo.csv` y
`bitacora_perfiles.csv`. Si quieres regenerarlos con otros valores:
`python generar_datos_demo_perfil.py`.

## Ajustar a tu caso real

- `logica_perfil.py` → diccionario `VARIABLES_CLAVE`: cambia los umbrales
  a los reales de cada modelo. Si PES y Personas deben tener variables
  clave distintas (no solo umbrales distintos), se puede separar ese
  diccionario por modelo — avísame y lo ajusto.
- Tu archivo real solo necesita una columna `fecha` y las columnas de
  variables que quieras ver — cualquier columna que no esté en
  `VARIABLES_CLAVE` se muestra igual, como "otra variable".
