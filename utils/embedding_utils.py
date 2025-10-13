"""
Utilidades para trabajar con embeddings de texto
"""

import numpy as np
from typing import List, Dict, Any, Union
import os
import pickle
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intentar importar sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence_transformers no está disponible. Algunas funcionalidades estarán limitadas.")
    logger.warning("Instale con: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Cache para el modelo de embeddings
_model_cache = {}

def get_embedding_model(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    """
    Obtiene un modelo de embeddings, cargándolo desde caché si ya existe.
    
    Args:
        model_name: Nombre del modelo de sentence-transformers a utilizar
        
    Returns:
        Modelo de sentence-transformers o None si no está disponible
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        logger.error("sentence_transformers no está instalado. No se puede cargar el modelo.")
        return None
        
    if model_name not in _model_cache:
        try:
            _model_cache[model_name] = SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Error al cargar el modelo {model_name}: {e}")
            return None
            
    return _model_cache[model_name]

def get_embedding(text: str, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> np.ndarray:
    """
    Obtiene el embedding de un texto usando un modelo de sentence-transformers.
    
    Args:
        text: Texto a convertir en embedding
        model_name: Nombre del modelo de sentence-transformers a utilizar
        
    Returns:
        Vector de embedding
    """
    if not text:
        return np.zeros(384)  # Devolver un vector de ceros con la dimensionalidad por defecto
    
    model = get_embedding_model(model_name)
    if model is None:
        return np.zeros(384)
        
    try:
        return model.encode(text)
    except Exception as e:
        logger.error(f"Error al generar embedding: {e}")
        return np.zeros(384)

def calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calcula la similitud del coseno entre dos embeddings.
    
    Args:
        embedding1: Primer vector de embedding
        embedding2: Segundo vector de embedding
        
    Returns:
        Similitud del coseno (entre 0 y 1)
    """
    # Verificar que los embeddings no sean nulos
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    # Verificar si algún vector es de ceros
    if np.all(embedding1 == 0) or np.all(embedding2 == 0):
        return 0.0
    
    # Calcular similitud del coseno
    try:
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        return dot_product / (norm1 * norm2)
    except Exception as e:
        logger.error(f"Error al calcular similitud de coseno: {e}")
        return 0.0

def batch_embed_documents(documents: List[str], 
                         model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", 
                         use_cache: bool = True, 
                         cache_file: str = None) -> np.ndarray:
    """
    Convierte una lista de documentos a embeddings de forma eficiente.
    
    Args:
        documents: Lista de textos a convertir en embeddings
        model_name: Nombre del modelo de sentence-transformers
        use_cache: Si es True, intenta cargar/guardar embeddings desde/en caché
        cache_file: Nombre del archivo de caché (opcional)
        
    Returns:
        Matriz de embeddings (n_documentos, dimensión_embedding)
    """
    if not documents:
        return np.zeros((0, 384))
        
    # Configurar ruta de caché
    if cache_file is None and use_cache:
        cache_dir = Path(os.getenv("TEMP", ".")) / "model_cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = cache_dir / f"embeddings_cache_{model_name.replace('-', '_')}.pkl"
    
    # Intentar cargar desde caché
    embeddings = None
    if use_cache and cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                if 'documents' in cache_data and 'embeddings' in cache_data:
                    # Verificar si los documentos coinciden
                    if cache_data['documents'] == documents:
                        return cache_data['embeddings']
        except Exception as e:
            logger.error(f"Error al cargar caché: {e}")
    
    # Generar embeddings
    model = get_embedding_model(model_name)
    if model is None:
        # Si no hay modelo, devolver matriz de ceros
        return np.zeros((len(documents), 384))
        
    try:
        embeddings = model.encode(documents)
    
        # Guardar en caché
        if use_cache and cache_file:
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump({'documents': documents, 'embeddings': embeddings}, f)
            except Exception as e:
                logger.error(f"Error al guardar caché: {e}")
    
        return embeddings
    except Exception as e:
        logger.error(f"Error al generar embeddings: {e}")
        return np.zeros((len(documents), 384))
