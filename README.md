# Análisis de Fatiga Muscular con sEMG

Dashboard interactivo para análisis de fatiga muscular usando señales electromiográficas superficiales (sEMG) del dataset de Cerqueira et al. (2024).

## Requisitos

- Python 3.10 o superior
- Streamlit
- NumPy, Pandas, SciPy, Plotly

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/ACgar/fatiga-muscular-semg.git
cd fatiga-muscular-semg
```
2. Crear entorno virtual (opcional pero recomendado):

conda create -n fatiga python=3.10
conda activate fatiga

3. Instalar dependencias
pip install -r requirements.txt

4. Ejecutar la aplicación
streamlit run app.py



```markdown
# Análisis de Fatiga Muscular con sEMG

Dashboard interactivo para análisis de fatiga muscular usando señales electromiográficas superficiales (sEMG) del dataset de Cerqueira et al. (2024).

## 📁 Estructura del proyecto

```
fatiga_muscular_c/
│
├── app.py                          # Aplicación principal Streamlit
├── requirements.txt                # Dependencias del proyecto
├── README.md                       # Este archivo
│
├── src/
│   ├── __init__.py                 # Inicialización del módulo
│   └── procesador_emg.py           # Filtros, MDF, MNF, correlación
│
└── data/                           # Carpeta para archivos de muestra (opcional)
    └── sample/
```

## ⚙️ Requisitos

- Python 3.10 o superior
- Streamlit
- NumPy, Pandas, SciPy, Plotly

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/ACgar/fatiga-muscular-semg.git
cd fatiga-muscular-semg
```

### 2. Crear entorno virtual (opcional pero recomendado)

```bash
conda create -n fatiga python=3.10
conda activate fatiga
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📊 Cómo usar la aplicación

1. **Cargar archivo EMG**: Selecciona un archivo CSV del dataset (ej. `trial1.csv`)
2. **Cargar archivo de fatiga**: Selecciona el archivo de fatiga correspondiente (mismo nombre, carpeta `self_perceived_fatigue_index`)
3. **Seleccionar músculo**: Elige el canal EMG que quieres analizar
4. **Explorar resultados**: Usa los gráficos interactivos para ver la evolución de la fatiga

## 📈 Funcionalidades

- Carga de archivos CSV (señal EMG + etiquetas de fatiga)
- Filtro Butterworth pasa-banda (20-450 Hz, orden 4)
- Cálculo de Frecuencia Mediana (MDF) y Frecuencia Media (MNF)
- Análisis por ventanas deslizantes (4s, 50% solapamiento)
- Correlación de Pearson entre MDF y fatiga percibida
- Indicador visual tipo semáforo:
  - 🟢 Baja fatiga
  - 🟡 Fatiga moderada
  - 🔴 Alta fatiga
- Gráficos interactivos con Plotly (zoom, paneo, lectura de valores)

## 📖 Dataset

Este proyecto utiliza el dataset público de Cerqueira et al. (2024):

- **Artículo:** *A Comprehensive Dataset of Surface Electromyography and Self-Perceived Fatigue Levels for Muscle Fatigue Analysis*
- **Revista:** Sensors, 2024
- **Disponible en:** Zenodo

## 👥 Autores

**Equipo 5 - Análisis de Biopotenciales Neuro-Musculares**

- Alexander Cinta Garmendia
- Silvana Cruz Severa
- Karol Franzoni Nolasco
- Eluzai González Hernández

**Académico:** Ismael Kelly Pérez

## 📅 Fecha

Mayo 2026

## 📄 Nota

Este proyecto es con fines académicos. El dataset original tiene su propia licencia (consultar Zenodo).
```

---

## Cómo actualizar tu README en GitHub

### Opción 1: Desde GitHub (más fácil)

1. Ve a tu repositorio: `https://github.com/ACgar/fatiga-muscular-semg`
2. Haz clic en el archivo `README.md`
3. Haz clic en el ícono del lápiz (✏️) arriba a la derecha
4. **Borra todo el contenido actual**
5. **Copia y pega** el nuevo contenido que te di
6. Desplázate hacia abajo y haz clic en **"Commit changes"**

### Opción 2: Desde tu computadora (si tienes Git configurado)

1. Abre tu archivo `README.md` en VS Code
2. Reemplaza el contenido con el que te di
3. Guarda el archivo (`Ctrl + S`)
4. En la terminal, ejecuta:

```bash
git add README.md
git commit -m "Mejora README con instrucciones completas"
git push origin main
```
