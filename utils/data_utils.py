"""
Utilidades para operaciones con datos de mallas curriculares
"""

import json
import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import pymongo
from pymongo import MongoClient

def connect_to_mongodb(connection_string: Optional[str] = None, 
                      db_name: str = "carreras_universitarias") -> pymongo.database.Database:
    """
    Conecta a la base de datos MongoDB.
    
    Args:
        connection_string: String de conexión a MongoDB. Si es None, se usa localhost:27017
        db_name: Nombre de la base de datos
        
    Returns:
        Objeto de base de datos MongoDB
    """
    if connection_string is None:
        connection_string = "mongodb://localhost:27017/"
    
    try:
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        # Verificar conexión
        client.admin.command('ping')
        return client[db_name]
    except Exception as e:
        import logging
        logging.error(f"Error al conectar a MongoDB: {e}")
        # Devolver None en lugar de levantar una excepción
        return None

def get_career_documents(db: pymongo.database.Database, 
                        career_name: str, 
                        collection_name: str = "mallas_curriculares") -> List[Dict]:
    """
    Obtiene documentos de carreras desde MongoDB.
    
    Args:
        db: Objeto de base de datos MongoDB
        career_name: Nombre de la carrera a buscar
        collection_name: Nombre de la colección
        
    Returns:
        Lista de documentos encontrados
    """
    # Verificar si la conexión a la base de datos es válida
    if db is None:
        import logging
        logging.error("No hay conexión a la base de datos MongoDB")
        return []
        
    try:
        # Crear expresión regular para búsqueda insensible a mayúsculas/minúsculas
        import re
        regex = re.compile(f".*{re.escape(career_name)}.*", re.IGNORECASE)
        
        # Realizar consulta
        cursor = db[collection_name].find({"carrera": {"$regex": regex}})
        
        # Convertir cursor a lista
        return list(cursor)
    except Exception as e:
        import logging
        logging.error(f"Error al obtener documentos de carreras: {e}")
        return []

def get_udla_curriculum(db: pymongo.database.Database, 
                       career_name: str,
                       collection_name: str = "mallas_curriculares") -> Dict:
    """
    Obtiene el documento de malla curricular de la UDLA para una carrera específica.
    
    Args:
        db: Objeto de base de datos MongoDB
        career_name: Nombre de la carrera
        collection_name: Nombre de la colección
        
    Returns:
        Documento de la malla curricular o None si no se encuentra
    """
    # Verificar si la conexión a la base de datos es válida
    if db is None:
        import logging
        logging.error("No hay conexión a la base de datos MongoDB")
        return None
        
    try:
        # Crear expresión regular para búsqueda insensible a mayúsculas/minúsculas
        import re
        regex = re.compile(f".*{re.escape(career_name)}.*", re.IGNORECASE)
        
        # Realizar consulta
        return db[collection_name].find_one({
            "universidad": "UDLA",
            "carrera": {"$regex": regex}
        })
    except Exception as e:
        import logging
        logging.error(f"Error al obtener malla curricular de UDLA: {e}")
        return None

def load_json_data(file_path: Union[str, Path]) -> Dict:
    """
    Carga datos desde un archivo JSON.
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        Datos cargados desde el archivo
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_data(data: Dict, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Guarda datos en un archivo JSON.
    
    Args:
        data: Datos a guardar
        file_path: Ruta donde guardar el archivo
        indent: Nivel de indentación
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def flatten_curriculum(curriculum: Dict) -> List[Dict]:
    """
    Aplana una malla curricular para obtener una lista de todas las materias.
    
    Args:
        curriculum: Diccionario con la malla curricular
        
    Returns:
        Lista de materias
    """
    subjects = []
    
    # Verificar si la malla tiene el formato enriquecido
    is_enriched = False
    
    # Explorar el primer semestre para detectar el formato
    first_semester_key = next(iter(curriculum['malla_curricular']), None)
    if first_semester_key and curriculum['malla_curricular'][first_semester_key]:
        first_subject = curriculum['malla_curricular'][first_semester_key][0]
        is_enriched = isinstance(first_subject, dict) and 'nombre' in first_subject
    
    # Recorrer cada semestre
    for semestre, materias in curriculum['malla_curricular'].items():
        if is_enriched:
            # Formato enriquecido
            for materia in materias:
                # Añadir semestre a la materia
                materia_con_semestre = materia.copy()
                materia_con_semestre['semestre'] = semestre
                subjects.append(materia_con_semestre)
        else:
            # Formato simple (lista de strings)
            for materia in materias:
                subjects.append({
                    'nombre': materia,
                    'semestre': semestre,
                    'universidad': curriculum.get('universidad', ''),
                    'carrera': curriculum.get('carrera', '')
                })
    
    return subjects

def get_all_subjects(curricula: List[Dict]) -> List[Dict]:
    """
    Obtiene todas las materias de varias mallas curriculares.
    
    Args:
        curricula: Lista de mallas curriculares
        
    Returns:
        Lista de todas las materias
    """
    all_subjects = []
    
    for curriculum in curricula:
        subjects = flatten_curriculum(curriculum)
        all_subjects.extend(subjects)
    
    return all_subjects

def normalize_subject_format(subject: Dict) -> Dict:
    """
    Normaliza el formato de una materia para asegurar que tenga todos los campos necesarios.
    
    Args:
        subject: Diccionario con los datos de la materia
        
    Returns:
        Diccionario normalizado
    """
    # Copiar para no modificar el original
    normalized = subject.copy()
    
    # Asegurar que existen los campos básicos
    if 'nombre' not in normalized:
        normalized['nombre'] = ''
    
    if 'descripcion' not in normalized:
        normalized['descripcion'] = ''
    
    if 'area' not in normalized:
        normalized['area'] = ''
    
    if 'tipo' not in normalized:
        normalized['tipo'] = ''
    
    if 'creditos_estimados' not in normalized:
        normalized['creditos_estimados'] = 0
    
    if 'semestre' not in normalized:
        normalized['semestre'] = '0'
    
    if 'universidad' not in normalized:
        normalized['universidad'] = ''
    
    if 'carrera' not in normalized:
        normalized['carrera'] = ''
    
    return normalized
