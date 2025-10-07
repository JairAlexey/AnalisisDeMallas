"""
Configuración global de la aplicación
"""

import os
from pathlib import Path

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
SRC_DIR = PROJECT_ROOT / "src"

# Configuración de la aplicación Streamlit
STREAMLIT_CONFIG = {
    "page_title": "Reformulador de Carreras Universitarias",
    "page_icon": "🎓",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Configuración del modelo de ML
ML_CONFIG = {
    "sentence_model": "paraphrase-multilingual-MiniLM-L12-v2",
    "tfidf_max_features": 1000,
    "tfidf_ngram_range": (1, 3),
    "default_similarity_threshold": 0.7,
    "default_n_clusters": 10,
    "random_state": 42
}

# Configuración de colores y estilos
UI_CONFIG = {
    "colors": {
        "primary": "#667eea",
        "secondary": "#764ba2",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#17a2b8"
    },
    "gradients": {
        "main": "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
        "sidebar": "linear-gradient(180deg, #667eea 0%, #764ba2 100%)"
    }
}

# Configuración de archivos
FILE_CONFIG = {
    "data_file": "universidades.json",
    "model_cache": "model_cache.pkl",
    "results_dir": "output",
    "allowed_extensions": [".json", ".csv", ".xlsx"]
}

# Configuración de análisis
ANALYSIS_CONFIG = {
    "min_cluster_size": 2,
    "max_clusters": 20,
    "similarity_range": (0.5, 0.9),
    "min_subject_similarity": 0.6,
    "common_subjects_threshold": 0.5
}

# Mensajes de la aplicación
MESSAGES = {
    "welcome": "¡Bienvenido al Reformulador de Carreras Universitarias!",
    "loading": "Cargando datos y modelos...",
    "processing": "Procesando análisis de carreras...",
    "success": "✅ Análisis completado exitosamente",
    "error_data": "❌ Error al cargar los datos",
    "error_model": "❌ Error al cargar el modelo",
    "no_data": "No se encontraron datos para analizar"
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_file": "app.log"
}

# Crear directorios necesarios
def ensure_directories():
    """Crea los directorios necesarios si no existen"""
    directories = [DATA_DIR, OUTPUT_DIR]
    for directory in directories:
        directory.mkdir(exist_ok=True)

# Inicializar configuración
ensure_directories()