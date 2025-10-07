"""
Utilidades para el análisis de carreras y materias
"""

import re
import unicodedata
from typing import List, Dict, Set, Tuple
import pandas as pd
import numpy as np

def normalize_text(text: str) -> str:
    """
    Normaliza texto removiendo acentos y caracteres especiales
    """
    if not text:
        return ""
    
    # Convertir a minúsculas
    text = text.lower()
    
    # Remover acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Remover caracteres especiales excepto espacios
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text: str) -> List[str]:
    """
    Extrae palabras clave importantes de un texto
    """
    # Palabras comunes a filtrar
    stop_words = {
        'de', 'la', 'el', 'en', 'y', 'a', 'para', 'con', 'del', 'las', 'los',
        'al', 'por', 'un', 'una', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii',
        'laboratorio', 'taller', 'curso', 'nivel', 'basico', 'basica', 'avanzado', 'avanzada'
    }
    
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Filtrar palabras cortas y stop words
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    return keywords

def calculate_jaccard_similarity(set1: Set, set2: Set) -> float:
    """
    Calcula la similitud de Jaccard entre dos conjuntos
    """
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def find_similar_subjects(subject1: str, subject2: str) -> float:
    """
    Encuentra similitud entre dos materias usando múltiples métricas
    """
    # Extraer keywords
    keywords1 = set(extract_keywords(subject1))
    keywords2 = set(extract_keywords(subject2))
    
    # Similitud de Jaccard
    jaccard_sim = calculate_jaccard_similarity(keywords1, keywords2)
    
    # Similitud de texto normalizado
    norm1 = normalize_text(subject1)
    norm2 = normalize_text(subject2)
    
    # Similitud simple por inclusión de texto
    inclusion_sim = 0.0
    if norm1 in norm2 or norm2 in norm1:
        inclusion_sim = 0.8
    
    # Combinar métricas
    combined_sim = max(jaccard_sim, inclusion_sim)
    
    return combined_sim

def group_subjects_by_similarity(subjects: List[str], threshold: float = 0.5) -> List[List[str]]:
    """
    Agrupa materias similares
    """
    groups = []
    used_indices = set()
    
    for i, subject1 in enumerate(subjects):
        if i in used_indices:
            continue
        
        current_group = [subject1]
        used_indices.add(i)
        
        for j, subject2 in enumerate(subjects[i+1:], i+1):
            if j in used_indices:
                continue
            
            similarity = find_similar_subjects(subject1, subject2)
            if similarity >= threshold:
                current_group.append(subject2)
                used_indices.add(j)
        
        if len(current_group) > 1:
            groups.append(current_group)
    
    return groups

def analyze_curriculum_structure(malla_curricular: Dict) -> Dict:
    """
    Analiza la estructura de una malla curricular
    """
    analysis = {
        'total_semestres': len(malla_curricular),
        'total_materias': sum(len(materias) for materias in malla_curricular.values()),
        'materias_por_semestre': {},
        'promedio_materias_semestre': 0,
        'semestre_mas_cargado': '',
        'materias_unicas': set()
    }
    
    # Analizar por semestre
    for semestre, materias in malla_curricular.items():
        num_materias = len(materias)
        analysis['materias_por_semestre'][semestre] = num_materias
        analysis['materias_unicas'].update([normalize_text(m) for m in materias])
    
    # Calcular promedios
    if analysis['materias_por_semestre']:
        analysis['promedio_materias_semestre'] = np.mean(list(analysis['materias_por_semestre'].values()))
        analysis['semestre_mas_cargado'] = max(
            analysis['materias_por_semestre'].items(),
            key=lambda x: x[1]
        )[0]
    
    analysis['materias_unicas'] = list(analysis['materias_unicas'])
    
    return analysis

def identify_career_type(career_name: str) -> str:
    """
    Identifica el tipo de carrera basado en el nombre
    """
    career_lower = normalize_text(career_name)
    
    # Patrones de identificación
    patterns = {
        'Ingeniería de Software': ['software', 'sistemas de informacion', 'sistemas'],
        'Ingeniería Civil': ['civil'],
        'Ingeniería Industrial': ['industrial', 'produccion'],
        'Ingeniería Electrónica': ['electronica', 'automatizacion', 'telecomunicaciones'],
        'Ingeniería Ambiental': ['ambiental'],
        'Ingeniería de Alimentos': ['alimentos'],
        'Ingeniería Mecánica': ['mecanica'],
        'Ingeniería Automotriz': ['automotriz'],
        'Biotecnología': ['biotecnologia', 'bioingenieria'],
        'Ingeniería Química': ['quimica'],
        'Ingeniería de Minas': ['minas'],
        'Computación/Informática': ['computacion', 'informatica', 'tecnologias de la informacion'],
        'Energías': ['energia', 'energias alternativas']
    }
    
    # Buscar coincidencias
    for career_type, keywords in patterns.items():
        for keyword in keywords:
            if keyword in career_lower:
                return career_type
    
    return 'Otras Ingenierías'

def generate_curriculum_summary(data: List[Dict]) -> Dict:
    """
    Genera un resumen completo del dataset de currículums
    """
    summary = {
        'total_carreras': len(data),
        'universidades': set(),
        'tipos_carrera': {},
        'estadisticas_materias': {
            'total': 0,
            'promedio_por_carrera': 0,
            'maximo': 0,
            'minimo': float('inf')
        },
        'materias_mas_comunes': {},
        'analisis_por_universidad': {}
    }
    
    all_subjects = []
    subject_counts = {}
    career_subject_counts = []
    
    for item in data:
        universidad = item['universidad']
        carrera = item['carrera']
        malla = item['malla_curricular']
        
        # Agregar universidad
        summary['universidades'].add(universidad)
        
        # Identificar tipo de carrera
        career_type = identify_career_type(carrera)
        summary['tipos_carrera'][career_type] = summary['tipos_carrera'].get(career_type, 0) + 1
        
        # Analizar materias
        career_subjects = []
        for semestre, materias in malla.items():
            career_subjects.extend(materias)
            all_subjects.extend(materias)
        
        career_subject_count = len(career_subjects)
        career_subject_counts.append(career_subject_count)
        
        # Actualizar estadísticas de materias
        summary['estadisticas_materias']['total'] += career_subject_count
        summary['estadisticas_materias']['maximo'] = max(
            summary['estadisticas_materias']['maximo'], 
            career_subject_count
        )
        summary['estadisticas_materias']['minimo'] = min(
            summary['estadisticas_materias']['minimo'], 
            career_subject_count
        )
        
        # Contar materias
        for subject in career_subjects:
            normalized_subject = normalize_text(subject)
            subject_counts[normalized_subject] = subject_counts.get(normalized_subject, 0) + 1
        
        # Análisis por universidad
        if universidad not in summary['analisis_por_universidad']:
            summary['analisis_por_universidad'][universidad] = {
                'carreras': [],
                'total_carreras': 0,
                'tipos_carrera': {}
            }
        
        summary['analisis_por_universidad'][universidad]['carreras'].append(carrera)
        summary['analisis_por_universidad'][universidad]['total_carreras'] += 1
        summary['analisis_por_universidad'][universidad]['tipos_carrera'][career_type] = \
            summary['analisis_por_universidad'][universidad]['tipos_carrera'].get(career_type, 0) + 1
    
    # Finalizar cálculos
    summary['universidades'] = list(summary['universidades'])
    summary['estadisticas_materias']['promedio_por_carrera'] = np.mean(career_subject_counts)
    summary['materias_mas_comunes'] = dict(
        sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)[:50]
    )
    
    return summary

def export_analysis_to_csv(analysis_data: Dict, filename: str):
    """
    Exporta análisis a archivo CSV
    """
    # Crear DataFrames para diferentes aspectos del análisis
    dfs = {}
    
    if 'career_clusters' in analysis_data:
        # DataFrame de clusters
        cluster_rows = []
        for cluster_name, cluster_data in analysis_data['career_clusters'].items():
            for career in cluster_data['carreras']:
                cluster_rows.append({
                    'cluster': cluster_name,
                    'universidad': career['universidad'],
                    'carrera': career['carrera'],
                    'total_materias': career['total_materias']
                })
        
        dfs['clusters'] = pd.DataFrame(cluster_rows)
    
    # Guardar cada DataFrame en una hoja separada si es Excel
    if filename.endswith('.xlsx'):
        with pd.ExcelWriter(filename) as writer:
            for sheet_name, df in dfs.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        # Guardar como CSV (solo el primer DataFrame)
        if dfs:
            list(dfs.values())[0].to_csv(filename, index=False)

def validate_curriculum_data(data: List[Dict]) -> Dict:
    """
    Valida la integridad de los datos del currículum
    """
    validation_report = {
        'total_records': len(data),
        'valid_records': 0,
        'errors': [],
        'warnings': []
    }
    
    required_fields = ['universidad', 'carrera', 'malla_curricular']
    
    for i, record in enumerate(data):
        record_valid = True
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in record:
                validation_report['errors'].append(
                    f"Registro {i+1}: Falta campo requerido '{field}'"
                )
                record_valid = False
        
        if 'malla_curricular' in record:
            malla = record['malla_curricular']
            
            # Verificar que la malla no esté vacía
            if not malla:
                validation_report['warnings'].append(
                    f"Registro {i+1}: Malla curricular vacía"
                )
            
            # Verificar estructura de la malla
            for semestre, materias in malla.items():
                if not isinstance(materias, list):
                    validation_report['errors'].append(
                        f"Registro {i+1}, Semestre {semestre}: Las materias deben ser una lista"
                    )
                    record_valid = False
                elif len(materias) == 0:
                    validation_report['warnings'].append(
                        f"Registro {i+1}, Semestre {semestre}: No hay materias"
                    )
        
        if record_valid:
            validation_report['valid_records'] += 1
    
    validation_report['validation_success'] = (
        validation_report['valid_records'] == validation_report['total_records'] and
        len(validation_report['errors']) == 0
    )
    
    return validation_report