"""
Módulo de procesamiento de señales EMG para análisis de fatiga muscular

Este módulo contiene las funciones necesarias para:
- Filtrado de señales electromiográficas
- Cálculo de métricas espectrales (MDF y MNF)
- Análisis por ventanas deslizantes
- Correlación con fatiga percibida
- Clasificación visual tipo semáforo
"""

from .procesador_emg import (
    detectar_canales_emg,
    cargar_emg_desde_bytes,
    cargar_fatiga_desde_bytes,
    sincronizar_senales_fatiga,
    aplicar_filtro_bandpass,
    calcular_mdf,
    calcular_mnf,
    analizar_ventanas,
    calcular_correlacion_fatiga,
    calcular_percentiles_fatiga,
    clasificar_semafaro
)

__all__ = [
    'detectar_canales_emg',
    'cargar_emg_desde_bytes',
    'cargar_fatiga_desde_bytes',
    'sincronizar_senales_fatiga',
    'aplicar_filtro_bandpass',
    'calcular_mdf',
    'calcular_mnf',
    'analizar_ventanas',
    'calcular_correlacion_fatiga',
    'calcular_percentiles_fatiga',
    'clasificar_semafaro'
]