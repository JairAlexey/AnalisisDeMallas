"""
Utilidades para la integración y evaluación de criterios ABET en mallas curriculares
"""

import os
import json
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_abet_criteria(file_path: str = None) -> Dict[str, Any]:
    """
    Carga los criterios ABET desde un archivo JSON.
    
    Args:
        file_path: Ruta al archivo JSON con los criterios ABET.
                  Si es None, se utiliza la ruta predeterminada.
    
    Returns:
        Diccionario con los criterios ABET
    """
    if file_path is None:
        # Obtener ruta relativa al directorio del proyecto
        base_dir = Path(__file__).parent.parent
        file_path = os.path.join(base_dir, 'data', 'criterios_abet.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        logger.error(f"Error al cargar criterios ABET desde {file_path}: {e}")
        return {}

def get_general_criteria(abet_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae los criterios generales de ABET.
    
    Args:
        abet_data: Diccionario con los datos ABET
    
    Returns:
        Diccionario con los criterios generales
    """
    try:
        return abet_data.get('criterios_abet', {}).get('criterios_generales', {})
    except Exception as e:
        logger.error(f"Error al extraer criterios generales: {e}")
        return {}

def get_specific_criteria(abet_data: Dict[str, Any], engineering_type: str = None) -> Dict[str, Any]:
    """
    Extrae los criterios específicos para un tipo de ingeniería.
    
    Args:
        abet_data: Diccionario con los datos ABET
        engineering_type: Tipo de ingeniería (ej: 'civil_engineering', 'software_engineering')
    
    Returns:
        Diccionario con los criterios específicos para ese tipo de ingeniería
    """
    try:
        specific_criteria = abet_data.get('criterios_abet', {}).get('criterios_especificos', {})
        
        if engineering_type and engineering_type in specific_criteria:
            return specific_criteria[engineering_type]
        
        return specific_criteria
    except Exception as e:
        logger.error(f"Error al extraer criterios específicos: {e}")
        return {}

def map_career_to_abet_category(career_name: str) -> str:
    """
    Mapea un nombre de carrera a un tipo de ingeniería según ABET.
    
    Args:
        career_name: Nombre de la carrera
    
    Returns:
        Clave del tipo de ingeniería en los criterios ABET
    """
    # Normalizar nombre de carrera (minúsculas, sin acentos)
    import unicodedata
    normalized_name = unicodedata.normalize('NFKD', career_name.lower())\
                               .encode('ASCII', 'ignore')\
                               .decode('ASCII')
    
    # Mapa de palabras clave a categorías ABET
    keyword_to_category = {
        'civil': 'civil_engineering',
        'software': 'software_engineering',
        'industrial': 'industrial_engineering',
        'electrica': 'electrical_engineering',
        'electronica': 'electrical_engineering',
        'mecanica': 'mechanical_engineering',
        'ambiental': 'environmental_engineering',
        'sistemas': 'software_engineering',
        'computacion': 'software_engineering',
        'informatica': 'software_engineering',
        'telecomunicaciones': 'electrical_engineering'
    }
    
    # Buscar palabras clave en el nombre de la carrera
    for keyword, category in keyword_to_category.items():
        if keyword in normalized_name:
            return category
    
    # Si no hay coincidencia específica, devolver None
    return None

def evaluate_curriculum_against_abet(curriculum: Dict[str, Any], abet_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evalúa una malla curricular contra los criterios ABET.
    
    Args:
        curriculum: Malla curricular a evaluar
        abet_data: Datos de criterios ABET
    
    Returns:
        Diccionario con los resultados de la evaluación
    """
    try:
        # Mapear carrera a categoría ABET
        career_name = curriculum.get('carrera', '')
        engineering_type = map_career_to_abet_category(career_name)
        
        # Extraer criterios
        general_criteria = get_general_criteria(abet_data)
        specific_criteria = get_specific_criteria(abet_data, engineering_type)
        
        # Aplanar malla curricular para análisis
        subjects = []
        for semester, semester_subjects in curriculum.get('malla_curricular', {}).items():
            if all(isinstance(s, str) for s in semester_subjects):
                subjects.extend(semester_subjects)
            elif all(isinstance(s, dict) for s in semester_subjects):
                subjects.extend([s.get('nombre', '') for s in semester_subjects if 'nombre' in s])
        
        # Inicializar resultados
        evaluation = {
            'carrera': career_name,
            'tipo_abet': engineering_type,
            'cumplimiento_general': {},
            'cumplimiento_especifico': {},
            'recomendaciones': [],
        }
        
        # Análisis básico de cumplimiento (implementar lógica específica según criterios)
        if engineering_type:
            evaluation['cumplimiento_general'] = {
                'criterio_1': {'cumple': True, 'observaciones': 'Evaluación básica de estudiantes'},
                'criterio_3': {'cumple': True, 'observaciones': 'Competencias identificadas'},
                'criterio_5': {'cumple': False, 'observaciones': 'Revisar balance matemáticas/ciencias'},
                # Agregar más criterios según corresponda
            }
            
            evaluation['cumplimiento_especifico'] = {
                'requisitos': []  # Llenar con análisis específico
            }
            
            evaluation['recomendaciones'] = [
                'Reforzar componente de matemáticas avanzadas',
                'Incluir más laboratorios prácticos',
                # Otras recomendaciones basadas en el análisis
            ]
        else:
            evaluation['recomendaciones'] = [
                'No se pudo mapear la carrera a un tipo específico de ingeniería ABET',
                'Realizar mapeo manual para análisis más detallado'
            ]
        
        return evaluation
        
    except Exception as e:
        logger.error(f"Error al evaluar malla contra criterios ABET: {e}")
        return {'error': str(e)}

def generate_abet_recommendations(curriculum: Dict[str, Any], 
                                abet_data: Dict[str, Any],
                                core_subjects: List[Dict]) -> Dict[str, Any]:
    """
    Genera recomendaciones basadas en criterios ABET y materias troncales identificadas.
    
    Args:
        curriculum: Malla curricular a evaluar
        abet_data: Datos de criterios ABET
        core_subjects: Materias troncales identificadas
    
    Returns:
        Diccionario con recomendaciones ABET
    """
    try:
        # Mapear carrera a categoría ABET
        career_name = curriculum.get('carrera', '')
        engineering_type = map_career_to_abet_category(career_name)
        
        # Extraer criterios específicos para este tipo de ingeniería
        specific_criteria = get_specific_criteria(abet_data, engineering_type)
        
        # Inicializar recomendaciones
        recommendations = {
            'tipo_ingenieria': engineering_type,
            'criterios_aplicables': specific_criteria.get('titulo', 'No especificado'),
            'descripcion': specific_criteria.get('descripcion', ''),
            'recomendaciones_materias': [],
            'areas_refuerzo': [],
            'cumplimiento_estimado': {}
        }
        
        # Analizar requisitos específicos de ABET para este tipo de ingeniería
        if engineering_type and 'requisitos' in specific_criteria:
            for req in specific_criteria['requisitos']:
                # Aquí implementar lógica para verificar si la malla cumple con este requisito
                # Por ahora, simplemente agregamos sugerencias genéricas
                recommendations['areas_refuerzo'].append({
                    'requisito': req,
                    'cumplimiento': 'Parcial',  # o 'Completo', 'No cumple', según análisis
                    'sugerencia': f"Revisar materias relacionadas con: {req}"
                })
        
        # Basándonos en las materias troncales, sugerir ajustes según ABET
        materias_matematicas = 0
        materias_ciencias = 0
        materias_ingenieria = 0
        materias_generales = 0
        
        # Contar materias por área (implementar lógica específica según la estructura de datos)
        for subject in core_subjects:
            area = subject.get('area_predominante', '').lower()
            if 'matemática' in area:
                materias_matematicas += 1
            elif 'ciencia' in area:
                materias_ciencias += 1
            elif 'ingeniería' in area:
                materias_ingenieria += 1
            else:
                materias_generales += 1
        
        # Evaluar cumplimiento de proporciones según ABET
        total_materias = materias_matematicas + materias_ciencias + materias_ingenieria + materias_generales
        if total_materias > 0:
            porcentaje_matematicas_ciencias = (materias_matematicas + materias_ciencias) / total_materias * 100
            porcentaje_ingenieria = materias_ingenieria / total_materias * 100
            
            recommendations['cumplimiento_estimado'] = {
                'matematicas_ciencias': {
                    'porcentaje': porcentaje_matematicas_ciencias,
                    'evaluacion': 'Suficiente' if porcentaje_matematicas_ciencias >= 20 else 'Insuficiente',
                    'recomendacion': 'Mantener proporción' if porcentaje_matematicas_ciencias >= 20 else 'Aumentar materias de matemáticas y ciencias'
                },
                'ingenieria_diseno': {
                    'porcentaje': porcentaje_ingenieria,
                    'evaluacion': 'Suficiente' if porcentaje_ingenieria >= 30 else 'Insuficiente',
                    'recomendacion': 'Mantener proporción' if porcentaje_ingenieria >= 30 else 'Aumentar materias de ingeniería y diseño'
                }
            }
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error al generar recomendaciones ABET: {e}")
        return {'error': str(e)}