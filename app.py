"""
app.py - Dashboard interactivo para análisis de fatiga muscular con sEMG

Ejecutar con: streamlit run app.py

Requisitos:
    pip install streamlit numpy pandas scipy plotly
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Importar módulo de procesamiento
from src.procesador_emg import (
    detectar_canales_emg,
    cargar_emg_desde_bytes,
    cargar_fatiga_desde_bytes,
    sincronizar_senales_fatiga,
    aplicar_filtro_bandpass,
    analizar_ventanas,
    calcular_correlacion_fatiga,
    calcular_percentiles_fatiga,
    clasificar_semafaro
)


# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Análisis de Fatiga Muscular | sEMG",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema oscuro para Plotly
PLOTLY_TEMPLATE = "plotly_dark"

# Constantes
FS = 1259  # Frecuencia de muestreo (Hz)
VENTANA_S = 4.0  # Tamaño de ventana (segundos)
OVERLAP = 0.5  # Solapamiento (50%)


# ============================================================================
# SIDEBAR - CARGA DE ARCHIVOS
# ============================================================================
st.sidebar.title("💪 Análisis de Fatiga Muscular")
st.sidebar.markdown("---")

st.sidebar.subheader("📁 Carga de Datos")

# Uploader para archivo EMG
archivo_emg = st.sidebar.file_uploader(
    "Cargar señal EMG (CSV)",
    type=["csv", "txt"],
    help="Archivo CSV con señales electromiográficas del dataset"
)

# Uploader para archivo de fatiga (obligatorio)
archivo_fatiga = st.sidebar.file_uploader(
    "Cargar niveles de fatiga (CSV)",
    type=["csv", "txt"],
    help="Archivo CSV con columnas 'time' y 'label' (0,1,2)"
)

st.sidebar.markdown("---")

# Verificar que ambos archivos estén cargados
if archivo_emg is None or archivo_fatiga is None:
    st.info("👈 **Por favor, cargue ambos archivos en el panel lateral para comenzar el análisis**")
    st.markdown("""
    ### Instrucciones:
    
    1. En el panel **izquierdo**, cargue el archivo **CSV de señal EMG**
    2. Luego, cargue el archivo **CSV de niveles de fatiga**
    3. Seleccione el **canal EMG** a analizar
    4. Explore los resultados en tiempo real
    
    ### Formato esperado:
    
    **Archivo EMG:** Cualquier CSV del dataset (trial1.csv, trial2.csv, etc.)
    
    **Archivo de fatiga:** CSV con columnas `time` (segundos) y `label` (0=sin fatiga, 1=transición, 2=fatiga)
    """)
    st.stop()

# Cargar y procesar datos
with st.spinner("Cargando y procesando datos..."):
    # Cargar EMG
    df_emg, canales_emg, tiempo_emg = cargar_emg_desde_bytes(archivo_emg.read())
    
    # Cargar fatiga
    df_fatiga, _, _ = cargar_fatiga_desde_bytes(archivo_fatiga.read())
    
    # Sincronizar señales con fatiga
    df_completo = sincronizar_senales_fatiga(df_emg, df_fatiga)
    
    # Detectar canales EMG disponibles
    canales = detectar_canales_emg(df_completo)
    
    # Filtrar solo canales que no sean tiempo ni fatiga
    canales = [c for c in canales if c not in ['tiempo', 'nivel_fatiga']]

st.sidebar.success(f"✅ Datos cargados: {len(df_completo)} muestras")
st.sidebar.info(f"📊 Canales EMG detectados: {len(canales)}")


# ============================================================================
# SIDEBAR - PARÁMETROS Y SELECCIÓN
# ============================================================================
st.sidebar.subheader("🎯 Selección de Músculo")

if len(canales) == 0:
    st.error("No se detectaron canales EMG en el archivo. Verifique el formato.")
    st.stop()

canal_seleccionado = st.sidebar.selectbox("Canal a analizar", canales)

st.sidebar.subheader("⚙️ Parámetros de Procesamiento")
ventana_s = st.sidebar.slider(
    "Tamaño de ventana (segundos)", 
    min_value=1.0, 
    max_value=8.0, 
    value=VENTANA_S, 
    step=0.5,
    help="Ventana temporal para calcular MDF/MNF. Más grande = más suavizado"
)

overlap = st.sidebar.slider(
    "Solapamiento (%)", 
    min_value=0.0, 
    max_value=0.9, 
    value=OVERLAP, 
    step=0.1,
    format="%.0f%%",
    help="Porcentaje de solapamiento entre ventanas. Mayor = más resolución temporal"
)


# ============================================================================
# PROCESAMIENTO DE SEÑAL
# ============================================================================
with st.spinner("Procesando señal y calculando métricas..."):
    # Aplicar filtro pasa-banda
    senal_filtrada = aplicar_filtro_bandpass(
        df_completo[canal_seleccionado].values, 
        FS, 
        lowcut=20, 
        highcut=450, 
        order=4
    )
    df_completo[f'{canal_seleccionado}_filtrado'] = senal_filtrada
    
    # Análisis por ventanas
    tiempos_ventana, mdf_values, mnf_values, niveles_ventana = analizar_ventanas(
        df_completo, 
        f'{canal_seleccionado}_filtrado', 
        fs=FS, 
        ventana_s=ventana_s, 
        overlap=overlap
    )
    
    # Calcular correlación
    correlacion = calcular_correlacion_fatiga(mdf_values, niveles_ventana)
    
    # Calcular percentiles para semáforo
    p33, p66 = calcular_percentiles_fatiga(mdf_values, niveles_ventana)
    
    # Clasificación del estado final
    estado_final, color_final, emoji_final = clasificar_semafaro(mdf_values[-1], p33, p66)


# ============================================================================
# DASHBOARD PRINCIPAL - MÉTRICAS
# ============================================================================
st.title("💪 Análisis de Fatiga Muscular con sEMG")
st.markdown(f"**Músculo analizado:** `{canal_seleccionado}` | **Archivo EMG:** `{archivo_emg.name}`")

# Métricas en fila
col1, col2, col3, col4 = st.columns(4)

with col1:
    duracion = df_completo['tiempo'].iloc[-1]
    st.metric("Duración del registro", f"{duracion:.1f} s")

with col2:
    if not np.isnan(correlacion):
        color_corr = "🟢" if correlacion >= 0.7 else "🟡" if correlacion >= 0.4 else "🔴"
        st.metric("Correlación MDF vs Fatiga", f"{correlacion:.3f}", 
                  delta=f"{color_corr} {'Óptima' if correlacion >= 0.7 else 'Aceptable' if correlacion >= 0.4 else 'Baja'}",
                  help="Correlación de Pearson entre MDF y niveles de fatiga (objetivo ≥ 0.7)")
    else:
        st.metric("Correlación MDF vs Fatiga", "N/A")

with col3:
    st.markdown(f"""
    <div style="text-align: center">
        <span style="font-size: 48px">{emoji_final}</span><br>
        <span style="color: {color_final}; font-weight: bold">{estado_final}</span>
    </div>
    """, unsafe_allow_html=True)

with col4:
    # Progreso visual de fatiga
    if len(mdf_values) > 0:
        fatiga_norm = 1 - (mdf_values - np.nanmin(mdf_values)) / (np.nanmax(mdf_values) - np.nanmin(mdf_values))
        fatiga_actual = fatiga_norm[-1] if not np.isnan(fatiga_norm[-1]) else 0
        st.progress(float(fatiga_actual))
        st.caption(f"Nivel de fatiga actual: {fatiga_actual:.0%}")

st.markdown("---")


# ============================================================================
# GRÁFICO 1: SEÑAL FILTRADA CON NAVEGACIÓN TEMPORAL
# ============================================================================
st.subheader("📈 Señal sEMG Filtrada")

# Slider de navegación temporal
tiempo_max = df_completo['tiempo'].iloc[-1]
tiempo_seleccionado = st.slider(
    "Navegación temporal",
    min_value=0.0,
    max_value=float(tiempo_max),
    value=0.0,
    step=1.0,
    format="%.1f s",
    help="Mueve el slider para ver la señal en diferentes momentos del registro"
)

# Encontrar índice para el tiempo seleccionado
idx_actual = np.argmin(np.abs(df_completo['tiempo'].values - tiempo_seleccionado))
ventana_muestras = int(ventana_s * FS)
idx_inicio = max(0, idx_actual - ventana_muestras)
idx_fin = min(len(df_completo), idx_inicio + ventana_muestras * 2)

# Gráfico de señal filtrada con Plotly
fig_senal = go.Figure()

fig_senal.add_trace(go.Scatter(
    x=df_completo['tiempo'].iloc[idx_inicio:idx_fin],
    y=df_completo[f'{canal_seleccionado}_filtrado'].iloc[idx_inicio:idx_fin],
    mode='lines',
    name=canal_seleccionado,
    line=dict(color='#00BFFF', width=1.5),
    hovertemplate='Tiempo: %{x:.2f}s<br>Amplitud: %{y:.6f}V<extra></extra>'
))

# Añadir línea vertical en tiempo seleccionado
fig_senal.add_vline(
    x=tiempo_seleccionado, 
    line_dash="dash", 
    line_color="red",
    annotation_text=f"t = {tiempo_seleccionado:.1f}s",
    annotation_position="top"
)

fig_senal.update_layout(
    title=f"Señal filtrada - {canal_seleccionado} (Filtro Butterworth 20-450 Hz)",
    xaxis_title="Tiempo (segundos)",
    yaxis_title="Amplitud (Volts)",
    template=PLOTLY_TEMPLATE,
    height=400,
    hovermode='x unified'
)

st.plotly_chart(fig_senal, use_container_width=True)


# ============================================================================
# GRÁFICO 2: EVOLUCIÓN DE MDF Y MNF
# ============================================================================
st.subheader("📉 Evolución de Métricas Espectrales")

fig_metricas = go.Figure()

# MDF trace
fig_metricas.add_trace(go.Scatter(
    x=tiempos_ventana,
    y=mdf_values,
    mode='lines',
    name='MDF (Frecuencia Mediana)',
    line=dict(color='#00FF00', width=2),
    hovertemplate='Tiempo: %{x:.1f}s<br>MDF: %{y:.1f} Hz<extra></extra>'
))

# MNF trace
fig_metricas.add_trace(go.Scatter(
    x=tiempos_ventana,
    y=mnf_values,
    mode='lines',
    name='MNF (Frecuencia Media)',
    line=dict(color='#FFA500', width=2),
    hovertemplate='Tiempo: %{x:.1f}s<br>MNF: %{y:.1f} Hz<extra></extra>'
))

# Áreas de fatiga percibida
# Colorear fondos según nivel de fatiga
niveles_unicos = np.unique(niveles_ventana)
colores_fatiga = {0: 'rgba(0,255,0,0.1)', 1: 'rgba(255,165,0,0.1)', 2: 'rgba(255,0,0,0.1)'}
nombres_fatiga = {0: 'Sin fatiga', 1: 'Transición', 2: 'Fatiga'}

for nivel in niveles_unicos:
    if nivel >= 0:
        # Encontrar regiones donde el nivel es constante
        mask = niveles_ventana == nivel
        if np.any(mask):
            # Encontrar transiciones
            cambios = np.diff(mask.astype(int))
            inicios = np.where(cambios == 1)[0] + 1
            finales = np.where(cambios == -1)[0] + 1
            
            if mask[0]:
                inicios = np.insert(inicios, 0, 0)
            if mask[-1]:
                finales = np.append(finales, len(tiempos_ventana))
            
            for inicio, fin in zip(inicios, finales):
                fig_metricas.add_vrect(
                    x0=tiempos_ventana[inicio],
                    x1=tiempos_ventana[fin - 1],
                    fillcolor=colores_fatiga[nivel],
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                    annotation_text=nombres_fatiga[nivel] if inicio == inicios[0] else "",
                    annotation_position="top left"
                )

fig_metricas.update_layout(
    title="Evolución de MDF y MNF durante el ejercicio",
    xaxis_title="Tiempo (segundos)",
    yaxis_title="Frecuencia (Hz)",
    template=PLOTLY_TEMPLATE,
    height=450,
    hovermode='x unified',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)')
)

st.plotly_chart(fig_metricas, use_container_width=True)


# ============================================================================
# GRÁFICO 3: SEMÁFORO DE FATIGA
# ============================================================================
st.subheader("🚦 Indicador de Fatiga - Semáforo")

fig_semaforo = go.Figure()

# Crear colores para cada punto
colores_semaforo = []
for mdf in mdf_values:
    _, color, _ = clasificar_semafaro(mdf, p33, p66)
    colores_semaforo.append(color)

# Mapa de colores para Plotly
color_map = {'green': '#00FF00', 'orange': '#FFA500', 'red': '#FF0000', 'gray': '#808080'}
plotly_colors = [color_map.get(c, '#808080') for c in colores_semaforo]

fig_semaforo.add_trace(go.Scatter(
    x=tiempos_ventana,
    y=[1] * len(tiempos_ventana),
    mode='markers',
    marker=dict(
        size=15,
        color=plotly_colors,
        symbol='square'
    ),
    text=[clasificar_semafaro(m, p33, p66)[0] for m in mdf_values],
    hovertemplate='Tiempo: %{x:.1f}s<br>Estado: %{text}<extra></extra>'
))

# Añadir referencia de umbrales
fig_semaforo.add_hline(y=1, line_dash="solid", line_color="white", opacity=0.3)

fig_semaforo.update_layout(
    title="Estado de Fatiga por Ventana de Tiempo",
    xaxis_title="Tiempo (segundos)",
    yaxis_title="",
    template=PLOTLY_TEMPLATE,
    height=200,
    showlegend=False,
    yaxis=dict(
        tickmode='array',
        tickvals=[1],
        ticktext=['Estado'],
        range=[0.5, 1.5]
    )
)

st.plotly_chart(fig_semaforo, use_container_width=True)


# ============================================================================
# GRÁFICO 4: BARRA DE PROGRESO DE FATIGA
# ============================================================================
st.subheader("📊 Barra de Progreso de Fatiga")

# Normalizar MDF (invertido: menor MDF = más fatiga)
mdf_clean = mdf_values[~np.isnan(mdf_values)]
if len(mdf_clean) > 0:
    mdf_norm = (mdf_values - np.nanmin(mdf_values)) / (np.nanmax(mdf_values) - np.nanmin(mdf_values))
    fatiga_norm = 1 - mdf_norm
else:
    fatiga_norm = np.zeros_like(tiempos_ventana)

fig_progreso = go.Figure()

fig_progreso.add_trace(go.Scatter(
    x=tiempos_ventana,
    y=fatiga_norm,
    mode='lines',
    name='Nivel de Fatiga',
    fill='tozeroy',
    line=dict(color='#FF0000', width=2),
    fillcolor='rgba(255,0,0,0.3)',
    hovertemplate='Tiempo: %{x:.1f}s<br>Fatiga: %{y:.1%}<extra></extra>'
))

fig_progreso.add_hline(y=0.33, line_dash="dash", line_color="yellow", opacity=0.7, annotation_text="Fatiga Moderada")
fig_progreso.add_hline(y=0.66, line_dash="dash", line_color="orange", opacity=0.7, annotation_text="Alta Fatiga")

fig_progreso.update_layout(
    title="Evolución del Nivel de Fatiga (valores normalizados)",
    xaxis_title="Tiempo (segundos)",
    yaxis_title="Nivel de Fatiga",
    template=PLOTLY_TEMPLATE,
    height=350,
    hovermode='x unified',
    yaxis=dict(
        tickformat='.0%',
        range=[0, 1]
    )
)

st.plotly_chart(fig_progreso, use_container_width=True)


# ============================================================================
# TABLA RESUMEN
# ============================================================================
st.subheader("📋 Resumen por Etapa")

# Crear tabla resumen
df_resumen = pd.DataFrame({
    'Tiempo (s)': tiempos_ventana,
    'MDF (Hz)': [f"{m:.1f}" if not np.isnan(m) else "N/A" for m in mdf_values],
    'MNF (Hz)': [f"{m:.1f}" if not np.isnan(m) else "N/A" for m in mnf_values],
    'Fatiga Reportada': [int(n) if n >= 0 else "N/A" for n in niveles_ventana],
    'Estado': [clasificar_semafaro(m, p33, p66)[0] for m in mdf_values]
})

# Mostrar muestras representativas (cada ~10 ventanas)
step = max(1, len(df_resumen) // 30)
st.dataframe(df_resumen.iloc[::step], use_container_width=True, height=300)


# ============================================================================
# PIE DE PÁGINA - INTERPRETACIÓN
# ============================================================================
st.markdown("---")
st.markdown(f"""
### 📖 Interpretación de Resultados

| Elemento | Significado |
|----------|-------------|
| **MDF / MNF** | Frecuencias mediana y media del espectro EMG. Disminuyen con la fatiga muscular |
| **Correlación** | Relación entre MDF y fatiga percibida. **Objetivo ≥ 0.7** | 
| **Semáforo** | 🟢 Baja fatiga \| 🟡 Fatiga moderada \| 🔴 Alta fatiga |
| **Barra de progreso** | Evolución normalizada de la fatiga (0% = inicio, 100% = máxima fatiga) |

**Umbrales aplicados:** Percentil 33% = {p33:.1f} Hz | Percentil 66% = {p66:.1f} Hz
""")

st.caption(f"💪 Análisis de fatiga muscular con sEMG | Frecuencia muestreo: {FS} Hz | "
           f"Ventana: {ventana_s}s | Solapamiento: {overlap:.0%}")