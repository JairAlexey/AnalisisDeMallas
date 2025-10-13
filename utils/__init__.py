"""
Paquete de utilidades para el proyecto de Reformulador de Carreras Universitarias

Este módulo contiene funciones auxiliares utilizadas en diferentes partes del
proyecto para procesamiento de datos, operaciones de texto, manipulación de 
estructuras de datos y otras tareas generales.
"""

# Importar funciones principales para facilitar su acceso
try:
    from .text_processing import (
        normalize_text,
        calculate_similarity,
        extract_keywords,
        remove_stopwords
    )
except ImportError:
    print("Warning: No se pudo importar desde text_processing")

try:
    from .data_utils import (
        load_json_data,
        save_json_data,
        flatten_curriculum,
        get_all_subjects
    )
except ImportError:
    print("Warning: No se pudo importar desde data_utils")

try:
    from .visualization import (
        create_similarity_heatmap,
        create_cluster_visualization,
        format_curriculum_display
    )
except ImportError:
    print("Warning: No se pudo importar desde visualization - verifique que el archivo existe")

try:
    from .embedding_utils import (
        get_embedding,
        calculate_cosine_similarity,
        batch_embed_documents
    )
except ImportError:
    print("Warning: No se pudo importar desde embedding_utils")

try:
    from .curriculum_analysis import (
        group_similar_subjects,
        identify_core_subjects,
        compare_curricula,
        generate_recommendations
    )
except ImportError:
    print("Warning: No se pudo importar desde curriculum_analysis")

# Versión del módulo
__version__ = '0.1.0'
