# Análisis de Fatiga Muscular con sEMG

Dashboard interactivo para análisis de fatiga muscular usando señales electromiográficas superficiales (sEMG) del dataset de Cerqueira et al. (2024).

## ⚙️ Requisitos

- Python 3.10 o superior
- Streamlit
- NumPy
- Pandas
- SciPy
- Plotly

## 🚀 Instalación y ejecución

1. Clonar el repositorio:
git clone https://github.com/ACgar/fatiga-muscular-semg.git
cd fatiga-muscular-semg

2. Crear entorno virtual (opcional pero recomendado):
conda create -n fatiga python=3.10
conda activate fatiga

3. Instalar dependencias:
pip install -r requirements.txt

4. Ejecutar la aplicación:
streamlit run app.py

La aplicación se abrirá automáticamente en tu navegador en http://localhost:8501

## 📊 Cómo usar la aplicación

1. Cargar archivo EMG: Selecciona un archivo CSV del dataset (ejemplo: trial1.csv)
2. Cargar archivo de fatiga: Selecciona el archivo de fatiga correspondiente (mismo nombre, carpeta self_perceived_fatigue_index)
3. Seleccionar músculo: Elige el canal EMG que quieres analizar
4. Explorar resultados: Usa los gráficos interactivos para ver la evolución de la fatiga

## 📈 Funcionalidades

- Carga de archivos CSV (señal EMG y etiquetas de fatiga)
- Filtro Butterworth pasa-banda (20-450 Hz, orden 4)
- Cálculo de Frecuencia Mediana (MDF) y Frecuencia Media (MNF)
- Análisis por ventanas deslizantes (4 segundos, 50 por ciento de solapamiento)
- Correlación de Pearson entre MDF y fatiga percibida
- Indicador visual tipo semáforo: verde para baja fatiga, amarillo para fatiga moderada, rojo para alta fatiga
- Gráficos interactivos con Plotly (zoom, paneo, lectura de valores al pasar el mouse)

## 📖 Dataset

Este proyecto utiliza el dataset público de Cerqueira et al. (2024):
- Artículo: A Comprehensive Dataset of Surface Electromyography and Self-Perceived Fatigue Levels for Muscle Fatigue Analysis
- Revista: Sensors, 2024
- Disponible en: Zenodo

## 👥 Autores

Equipo 5 - Análisis de Biopotenciales Neuro-Musculares
- Alexander Cinta Garmendia
- Silvana Cruz Severa
- Karol Franzoni Nolasco
- Eluzai González Hernández

Académico: Ismael Kelly Pérez

## 📅 Fecha

Mayo 2026

## 📄 Nota

Este proyecto es con fines académicos. El dataset original tiene su propia licencia (consultar Zenodo).
