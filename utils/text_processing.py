"""
Utilidades para procesamiento de texto y análisis de similitud
"""

import re
import unicodedata
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

def normalize_text(text: str) -> str:
    """
    Normaliza un texto: convierte a minúsculas, elimina tildes y caracteres especiales,
    y sustituye abreviaturas comunes.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Convertir a minúsculas
    text = text.lower()
    
    # Eliminar tildes
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')
    
    # Sustituir abreviaturas comunes
    abreviaturas = {
        "ing.": "ingenieria",
        "mat.": "matematica",
        "prog.": "programacion",
        "sist.": "sistemas",
        "comp.": "computacion",
        "lab.": "laboratorio",
        "calc.": "calculo",
        "est.": "estadistica",
        "adm.": "administracion",
        "econ.": "economia",
        "prac.": "practica",
        "tec.": "tecnologia",
        "prog.": "programacion",
        "alg.": "algoritmos"
    }
    
    for abrev, completo in abreviaturas.items():
        text = re.sub(rf'\b{abrev}\b', completo, text)
    
    # Eliminar caracteres especiales y números
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # Eliminar espacios múltiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def remove_stopwords(text: str, stopwords: List[str] = None) -> str:
    """
    Elimina palabras vacías (stopwords) de un texto.
    
    Args:
        text: Texto del cual eliminar stopwords
        stopwords: Lista de stopwords a eliminar. Si es None, se usa una lista predeterminada
        
    Returns:
        Texto sin stopwords
    """
    if not stopwords:
        # Lista básica de stopwords en español
        stopwords = ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'de', 
                     'del', 'a', 'en', 'por', 'para', 'con', 'sin', 'sobre', 'entre', 
                     'que', 'se', 'su', 'sus', 'como', 'pero', 'mas', 'si', 'no', 
                     'al', 'este', 'esta', 'estos', 'estas', 'aquel', 'aquella', 
                     'aquellos', 'aquellas']
    
    words = text.split()
    filtered_words = [word for word in words if word.lower() not in stopwords]
    return ' '.join(filtered_words)

def extract_keywords(text: str, n: int = 5) -> List[str]:
    """
    Extrae las n palabras más relevantes de un texto.
    
    Args:
        text: Texto del cual extraer palabras clave
        n: Número de palabras clave a extraer
        
    Returns:
        Lista de palabras clave
    """
    # Normalizar texto
    text = normalize_text(text)
    
    # Eliminar stopwords
    text = remove_stopwords(text)
    
    # Contar frecuencia de palabras
    words = text.split()
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Ignorar palabras muy cortas
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Ordenar por frecuencia
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Devolver las n palabras más frecuentes
    return [word for word, _ in sorted_words[:n]]

def calculate_similarity(text1: str, text2: str, method: str = "jaccard") -> float:
    """
    Calcula la similitud entre dos textos usando diferentes métodos.
    
    Args:
        text1: Primer texto
        text2: Segundo texto
        method: Método de similitud ('jaccard', 'overlap', 'cosine')
        
    Returns:
        Valor de similitud entre 0 y 1
    """
    # Normalizar textos
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)
    
    # Si alguno está vacío, la similitud es 0
    if not text1 or not text2:
        return 0.0
    
    # Crear conjuntos de palabras
    set1 = set(text1.split())
    set2 = set(text2.split())
    
    if method == "jaccard":
        # Índice de Jaccard: tamaño de la intersección / tamaño de la unión
        union = len(set1.union(set2))
        if union == 0:
            return 0.0
        return len(set1.intersection(set2)) / union
    
    elif method == "overlap":
        # Coeficiente de superposición: tamaño de la intersección / tamaño del conjunto más pequeño
        min_size = min(len(set1), len(set2))
        if min_size == 0:
            return 0.0
        return len(set1.intersection(set2)) / min_size
    
    elif method == "cosine":
        # Similitud del coseno básica (sin TF-IDF)
        # Crear un vocabulario conjunto
        vocabulary = sorted(set1.union(set2))
        
        # Crear vectores de frecuencia
        vec1 = np.zeros(len(vocabulary))
        vec2 = np.zeros(len(vocabulary))
        
        for i, word in enumerate(vocabulary):
            if word in set1:
                vec1[i] = 1
            if word in set2:
                vec2[i] = 1
        
        # Calcular similitud del coseno
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    else:
        raise ValueError(f"Método de similitud '{method}' no soportado")
