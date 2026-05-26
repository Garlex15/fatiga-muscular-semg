"""
procesador_emg.py - Lógica matemática para análisis de fatiga muscular

Contiene todas las funciones de procesamiento de señales EMG:
- Filtros digitales
- Métricas espectrales (MDF, MNF)
- Análisis temporal por ventanas
- Correlación estadística
"""

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, welch
from scipy.interpolate import interp1d
import io


# ============================================================================
# CONSTANTES
# ============================================================================
FS_DEFAULT = 1259  # Frecuencia de muestreo por defecto (Hz)
VENTANA_DEFAULT = 4.0  # Tamaño de ventana en segundos
OVERLAP_DEFAULT = 0.5  # Solapamiento (50%)
LOW_CUT = 20.0  # Frecuencia de corte baja (Hz)
HIGH_CUT = 450.0  # Frecuencia de corte alta (Hz)
FILTER_ORDER = 4  # Orden del filtro Butterworth
NFFT_DEFAULT = 4096  # Puntos para FFT


# ============================================================================
# FUNCIONES DE CARGA Y DETECCIÓN
# ============================================================================

def detectar_canales_emg(df):
    """
    Detecta automáticamente las columnas que contienen señales EMG en un DataFrame.
    
    Parámetros:
    -----------
    df : pandas.DataFrame
        DataFrame con los datos cargados desde CSV
        
    Retorna:
    --------
    list : Lista de nombres de columnas que son canales EMG
    """
    canales = []
    
    for col in df.columns:
        col_lower = col.lower()
        # Detectar columnas que contienen señales EMG
        if '[v]' in col_lower or 'emg' in col_lower:
            canales.append(col)
        # También detectar nombres específicos de músculos
        elif any(muscle in col_lower for muscle in ['biceps', 'deltoid', 'deltoide']):
            canales.append(col)
    
    # Si no se detectaron canales, intentar tomar todas las columnas excepto la primera (tiempo)
    if len(canales) == 0 and len(df.columns) > 1:
        # Asumir que la primera columna es tiempo y el resto son canales
        canales = df.columns[1:].tolist()
    
    return canales


def cargar_emg_desde_bytes(contenido_bytes):
    """
    Carga un archivo CSV desde bytes y lo convierte en DataFrame limpio.
    Maneja el formato especial del dataset (múltiples columnas de tiempo).
    
    Parámetros:
    -----------
    contenido_bytes : bytes
        Contenido del archivo CSV en bytes
        
    Retorna:
    --------
    tuple: (df_clean, canales, tiempo_array)
        - df_clean: DataFrame con columnas 'tiempo' y señales
        - canales: Lista de nombres de canales EMG
        - tiempo: Array de tiempo en segundos
    """
    # Leer CSV con pandas
    df_raw = pd.read_csv(io.BytesIO(contenido_bytes))
    
    # Identificar columnas de tiempo (las que contienen "X [s]")
    tiempo_cols = [col for col in df_raw.columns if 'X [s]' in col]
    
    # Identificar columnas de señal (las que terminan con [V])
    senal_cols = [col for col in df_raw.columns if '[V]' in col]
    
    if len(tiempo_cols) == 0:
        # Formato simple: primera columna es tiempo
        tiempo = df_raw.iloc[:, 0].values
        senales = df_raw.iloc[:, 1:].values
        nombres = df_raw.columns[1:].tolist()
    else:
        # Formato complejo: usar primera columna de tiempo como referencia
        tiempo = df_raw[tiempo_cols[0]].values
        
        # Extraer señales
        senales = []
        nombres = []
        for col in senal_cols:
            senales.append(df_raw[col].values)
            # Limpiar nombre: eliminar sufijos y espacios
            nombre_limpio = col.replace(': EMG', '').replace('[V]', '').strip()
            nombres.append(nombre_limpio)
        
        senales = np.array(senales).T
    
    # Crear DataFrame limpio
    df_clean = pd.DataFrame({'tiempo': tiempo})
    for i, nombre in enumerate(nombres):
        df_clean[nombre] = senales[:, i] if senales.ndim > 1 else senales
    
    return df_clean, nombres, tiempo


def cargar_fatiga_desde_bytes(contenido_bytes):
    """
    Carga un archivo CSV de fatiga desde bytes.
    
    Parámetros:
    -----------
    contenido_bytes : bytes
        Contenido del archivo CSV en bytes
        
    Retorna:
    --------
    tuple: (df_fatiga, tiempos, niveles)
        - df_fatiga: DataFrame con columnas 'tiempo' y 'nivel_fatiga'
        - tiempos: Array de tiempos
        - niveles: Array de niveles de fatiga (0, 1, 2)
    """
    df = pd.read_csv(io.BytesIO(contenido_bytes))
    
    # Identificar columnas de tiempo y label
    if 'time' in df.columns:
        df.rename(columns={'time': 'tiempo'}, inplace=True)
    if 'label' in df.columns:
        df.rename(columns={'label': 'nivel_fatiga'}, inplace=True)
    
    # Si las columnas no tienen nombres estándar, asumir primera = tiempo, segunda = nivel
    if 'tiempo' not in df.columns and len(df.columns) >= 1:
        df.rename(columns={df.columns[0]: 'tiempo'}, inplace=True)
    if 'nivel_fatiga' not in df.columns and len(df.columns) >= 2:
        df.rename(columns={df.columns[1]: 'nivel_fatiga'}, inplace=True)
    
    return df, df['tiempo'].values, df['nivel_fatiga'].values


def sincronizar_senales_fatiga(df_emg, df_fatiga):
    """
    Sincroniza las señales EMG con las etiquetas de fatiga.
    Interpola las etiquetas a la frecuencia de EMG.
    
    Parámetros:
    -----------
    df_emg : pandas.DataFrame
        DataFrame con señales EMG (debe tener columna 'tiempo')
    df_fatiga : pandas.DataFrame
        DataFrame con fatiga (debe tener columnas 'tiempo' y 'nivel_fatiga')
        
    Retorna:
    --------
    pandas.DataFrame: DataFrame EMG con columna adicional 'nivel_fatiga'
    """
    tiempo_emg = df_emg['tiempo'].values
    tiempo_fatiga = df_fatiga['tiempo'].values
    niveles = df_fatiga['nivel_fatiga'].values
    
    # Interpolar etiquetas a la frecuencia de EMG
    f_interp = interp1d(
        tiempo_fatiga, niveles, 
        kind='nearest', 
        fill_value=(niveles[0], niveles[-1]), 
        bounds_error=False
    )
    niveles_interp = f_interp(tiempo_emg)
    
    df_emg['nivel_fatiga'] = niveles_interp
    return df_emg


# ============================================================================
# FUNCIONES DE FILTRADO
# ============================================================================

def butter_bandpass(lowcut, highcut, fs, order=4):
    """
    Diseña un filtro Butterworth pasa-banda.
    
    Parámetros:
    -----------
    lowcut : float
        Frecuencia de corte baja (Hz)
    highcut : float
        Frecuencia de corte alta (Hz)
    fs : float
        Frecuencia de muestreo (Hz)
    order : int
        Orden del filtro
        
    Retorna:
    --------
    tuple: (b, a) Coeficientes del filtro
    """
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a


def aplicar_filtro_bandpass(senal, fs, lowcut=20, highcut=450, order=4):
    """
    Aplica filtro Butterworth pasa-banda a la señal.
    
    Parámetros:
    -----------
    senal : numpy.ndarray
        Señal a filtrar
    fs : float
        Frecuencia de muestreo (Hz)
    lowcut : float
        Frecuencia de corte baja (Hz)
    highcut : float
        Frecuencia de corte alta (Hz)
    order : int
        Orden del filtro
        
    Retorna:
    --------
    numpy.ndarray: Señal filtrada
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    senal_filtrada = filtfilt(b, a, senal)
    return senal_filtrada


# ============================================================================
# FUNCIONES DE MÉTRICAS ESPECTRALES
# ============================================================================

def calcular_mdf(senal, fs, nfft=4096):
    """
    Calcula la Frecuencia Mediana (MDF) según la definición del artículo.
    MDF = frecuencia que divide el espectro en dos mitades iguales.
    
    Parámetros:
    -----------
    senal : numpy.ndarray
        Señal EMG (una ventana)
    fs : float
        Frecuencia de muestreo (Hz)
    nfft : int
        Número de puntos para FFT
        
    Retorna:
    --------
    tuple: (mdf, freqs, psd)
        - mdf: Frecuencia Mediana en Hz
        - freqs: Array de frecuencias
        - psd: Densidad espectral de potencia
    """
    # Calcular espectro usando Welch
    freqs, psd = welch(senal, fs=fs, nperseg=nfft//2, nfft=nfft)
    
    # Calcular potencia acumulada
    potencia_acum = np.cumsum(psd)
    potencia_total = potencia_acum[-1]
    
    # Encontrar frecuencia donde se alcanza el 50% de la potencia total
    mitad_potencia = potencia_total / 2
    idx_mdf = np.where(potencia_acum >= mitad_potencia)[0]
    
    if len(idx_mdf) > 0:
        mdf = freqs[idx_mdf[0]]
    else:
        mdf = np.nan
    
    return mdf, freqs, psd


def calcular_mnf(senal, fs, nfft=4096):
    """
    Calcula la Frecuencia Media (MNF).
    MNF = (sum(f_i * P_i)) / (sum(P_i))
    
    Parámetros:
    -----------
    senal : numpy.ndarray
        Señal EMG (una ventana)
    fs : float
        Frecuencia de muestreo (Hz)
    nfft : int
        Número de puntos para FFT
        
    Retorna:
    --------
    float: Frecuencia Media en Hz
    """
    freqs, psd = welch(senal, fs=fs, nperseg=nfft//2, nfft=nfft)
    
    numerador = np.sum(freqs * psd)
    denominador = np.sum(psd)
    
    if denominador > 0:
        mnf = numerador / denominador
    else:
        mnf = np.nan
    
    return mnf


# ============================================================================
# ANÁLISIS POR VENTANAS
# ============================================================================

def analizar_ventanas(df_emg, canal, fs=1259, ventana_s=4.0, overlap=0.5):
    """
    Analiza la señal por ventanas deslizantes.
    
    Parámetros:
    -----------
    df_emg : pandas.DataFrame
        DataFrame con señales EMG (debe tener columnas 'tiempo' y el canal)
    canal : str
        Nombre del canal a analizar
    fs : float
        Frecuencia de muestreo (Hz)
    ventana_s : float
        Tamaño de ventana en segundos
    overlap : float
        Solapamiento entre ventanas (0 a 1)
        
    Retorna:
    --------
    tuple: (tiempos, mdf_values, mnf_values, niveles_ventana)
        - tiempos: Tiempos centrales de cada ventana
        - mdf_values: Valores MDF por ventana
        - mnf_values: Valores MNF por ventana
        - niveles_ventana: Nivel de fatiga predominante por ventana
    """
    ventana_muestras = int(ventana_s * fs)
    paso_muestras = int(ventana_muestras * (1 - overlap))
    
    senal = df_emg[canal].values
    tiempos = df_emg['tiempo'].values
    
    tiempos_ventana = []
    mdf_values = []
    mnf_values = []
    niveles_ventana = []
    
    # Verificar si existe columna de fatiga
    tiene_fatiga = 'nivel_fatiga' in df_emg.columns
    if tiene_fatiga:
        niveles = df_emg['nivel_fatiga'].values
    else:
        niveles = np.zeros_like(senal)
    
    for inicio in range(0, len(senal) - ventana_muestras, paso_muestras):
        fin = inicio + ventana_muestras
        ventana = senal[inicio:fin]
        
        # Tiempo central de la ventana
        t_central = np.mean(tiempos[inicio:fin])
        tiempos_ventana.append(t_central)
        
        # Nivel de fatiga predominante en la ventana
        if tiene_fatiga:
            niveles_vent = niveles[inicio:fin]
            nivel_predominante = np.round(np.mean(niveles_vent))
        else:
            nivel_predominante = -1  # Sin datos de fatiga
        niveles_ventana.append(nivel_predominante)
        
        # Calcular métricas solo si la ventana tiene actividad
        if np.std(ventana) > 1e-7:
            mdf, _, _ = calcular_mdf(ventana, fs)
            mnf = calcular_mnf(ventana, fs)
            mdf_values.append(mdf)
            mnf_values.append(mnf)
        else:
            mdf_values.append(np.nan)
            mnf_values.append(np.nan)
    
    return (np.array(tiempos_ventana), 
            np.array(mdf_values), 
            np.array(mnf_values), 
            np.array(niveles_ventana))


# ============================================================================
# CORRELACIÓN Y CLASIFICACIÓN
# ============================================================================

def calcular_correlacion_fatiga(mdf_values, niveles_ventana):
    """
    Calcula la correlación de Pearson entre MDF y niveles de fatiga.
    
    Parámetros:
    -----------
    mdf_values : numpy.ndarray
        Valores de MDF por ventana
    niveles_ventana : numpy.ndarray
        Niveles de fatiga por ventana
        
    Retorna:
    --------
    float: Coeficiente de correlación de Pearson (NaN si no es posible)
    """
    # Filtrar valores válidos (no NaN y nivel >= 0)
    mascara = ~np.isnan(mdf_values) & (niveles_ventana >= 0)
    
    if np.sum(mascara) < 3:
        return np.nan
    
    correlacion = np.corrcoef(mdf_values[mascara], niveles_ventana[mascara])[0, 1]
    return correlacion


def calcular_percentiles_fatiga(mdf_values, niveles_ventana):
    """
    Calcula percentiles 33% y 66% basados en valores MDF en diferentes niveles de fatiga.
    
    Parámetros:
    -----------
    mdf_values : numpy.ndarray
        Valores de MDF por ventana
    niveles_ventana : numpy.ndarray
        Niveles de fatiga por ventana
        
    Retorna:
    --------
    tuple: (p33, p66)
        - p33: Percentil 33% (límite bajo - fatiga alta)
        - p66: Percentil 66% (límite alto - fatiga baja)
    """
    mascara = ~np.isnan(mdf_values) & (niveles_ventana >= 0)
    mdf_filtrados = mdf_values[mascara]
    
    if len(mdf_filtrados) > 0:
        p33 = np.percentile(mdf_filtrados, 33)
        p66 = np.percentile(mdf_filtrados, 66)
    else:
        p33 = 50.0  # Valores por defecto
        p66 = 100.0
    
    return p33, p66


def clasificar_semafaro(mdf_actual, p33, p66):
    """
    Clasifica el nivel de fatiga según semáforo basado en MDF.
    
    Parámetros:
    -----------
    mdf_actual : float
        Valor actual de MDF
    p33 : float
        Percentil 33% (fatiga alta)
    p66 : float
        Percentil 66% (fatiga baja)
        
    Retorna:
    --------
    tuple: (texto, color, emoji)
        - texto: Descripción del estado
        - color: Color en inglés
        - emoji: Emoji representativo
    """
    if np.isnan(mdf_actual):
        return "Sin datos", "gray", "⚪"
    elif mdf_actual >= p66:
        return "Baja Fatiga", "green", "🟢"
    elif mdf_actual >= p33:
        return "Fatiga Moderada", "orange", "🟡"
    else:
        return "Alta Fatiga", "red", "🔴"