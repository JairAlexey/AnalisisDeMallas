"""
Utilidades para análisis de mallas curriculares y recomendación de materias
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
# Importamos las bibliotecas necesarias para fuzzy matching
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz

try:
    from sklearn.cluster import AgglomerativeClustering
except ImportError:
    print("Error: No se pudo importar AgglomerativeClustering de sklearn.cluster")
    print("Por favor, instale scikit-learn con: pip install scikit-learn>=1.3.0")
    AgglomerativeClustering = None

# Intentar importar las funciones de otros módulos de manera segura
try:
    from .text_processing import normalize_text
except ImportError:
    print("Error: No se pudo importar normalize_text desde text_processing")
    normalize_text = lambda x: x if isinstance(x, str) else ""

try:
    from .embedding_utils import get_embedding, calculate_cosine_similarity, batch_embed_documents
except ImportError:
    print("Error: No se pudieron importar funciones desde embedding_utils")
    # Definir versiones dummy de las funciones
    get_embedding = lambda x, model_name="": np.zeros(384)
    calculate_cosine_similarity = lambda x, y: 0.0
    batch_embed_documents = lambda docs, model_name="", use_cache=False, cache_file=None: np.zeros((len(docs), 384))

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
                materia_con_semestre['universidad'] = curriculum.get('universidad', '')
                materia_con_semestre['carrera'] = curriculum.get('carrera', '')
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

def group_similar_subjects(subjects: List[Dict], 
                          similarity_threshold: float = 0.8,
                          model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> List[Dict]:
    """
    Agrupa materias similares utilizando embeddings y clustering.
    
    Args:
        subjects: Lista de materias
        similarity_threshold: Umbral de similitud para considerar dos materias como equivalentes
        model_name: Modelo de embeddings a utilizar
        
    Returns:
        Lista de grupos de materias similares
    """
    if not subjects:
        return []
    
    # Extraer nombres y descripciones
    names = [s['nombre'] for s in subjects]
    descriptions = [s.get('descripcion', '') for s in subjects]
    
    # Crear texto combinado para cada materia
    combined_texts = []
    for i, name in enumerate(names):
        # Dar más peso al nombre que a la descripción
        if descriptions[i]:
            combined_texts.append(f"{name} {name} {descriptions[i]}")
        else:
            combined_texts.append(name)
    
    # Obtener embeddings
    print(f"Generando embeddings para {len(combined_texts)} materias...")
    embeddings = batch_embed_documents(combined_texts, model_name)
    
    # Aplicar clustering jerárquico
    print("Aplicando clustering para agrupar materias similares...")
    distance_threshold = 1.0 - similarity_threshold
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric='cosine',
        linkage='average'
    )
    
    # Obtener etiquetas de cluster
    labels = clustering.fit_predict(embeddings)
    
    # Agrupar materias por cluster
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        clusters[int(label)].append(subjects[i])
    
    # Convertir a formato de resultado
    result = []
    for label, cluster_subjects in clusters.items():
        # Identificar la materia representativa del cluster (la que tiene más universidades)
        univ_counts = {}
        for s in cluster_subjects:
            univ = s.get('universidad', '')
            if univ:
                univ_counts[univ] = univ_counts.get(univ, 0) + 1
        
        # Determinar área y tipo predominantes
        areas = {}
        tipos = {}
        for s in cluster_subjects:
            area = s.get('area', '')
            tipo = s.get('tipo', '')
            if area:
                areas[area] = areas.get(area, 0) + 1
            if tipo:
                tipos[tipo] = tipos.get(tipo, 0) + 1
        
        area_predominante = max(areas.items(), key=lambda x: x[1])[0] if areas else ''
        tipo_predominante = max(tipos.items(), key=lambda x: x[1])[0] if tipos else ''
        
        # Crear nombre general para el grupo
        # Usar la materia más común como nombre de referencia
        name_counts = {}
        for s in cluster_subjects:
            name = s.get('nombre', '')
            if name:
                name_counts[name] = name_counts.get(name, 0) + 1
        
        nombre_general = max(name_counts.items(), key=lambda x: x[1])[0] if name_counts else "Sin nombre"
        
        # Crear registro de grupo
        group = {
            "nombre_general": nombre_general,
            "materias_equivalentes": [s.get('nombre', '') for s in cluster_subjects],
            "universidades": list(set([s.get('universidad', '') for s in cluster_subjects])),
            "frecuencia": len(set([s.get('universidad', '') for s in cluster_subjects])),
            "area_predominante": area_predominante,
            "tipo_predominante": tipo_predominante,
            "materias": cluster_subjects
        }
        
        result.append(group)
    
    # Ordenar por frecuencia (número de universidades)
    result.sort(key=lambda x: x["frecuencia"], reverse=True)
    
    return result

def identify_core_subjects(subject_groups: List[Dict], 
                          universities: List[str], 
                          threshold_percentage: float = 0.7) -> List[Dict]:
    """
    Identifica las materias troncales (aquellas que aparecen en al menos
    threshold_percentage de las universidades analizadas).
    
    Args:
        subject_groups: Lista de grupos de materias similares
        universities: Lista de universidades analizadas
        threshold_percentage: Porcentaje mínimo de universidades en las que debe aparecer
        
    Returns:
        Lista de materias troncales
    """
    total_universities = len(set(universities))
    threshold_count = total_universities * threshold_percentage
    
    core_subjects = []
    
    for group in subject_groups:
        if len(set(group["universidades"])) >= threshold_count:
            # Calcular la frecuencia relativa
            group["frecuencia_relativa"] = len(set(group["universidades"])) / total_universities
            core_subjects.append(group)
    
    return core_subjects

def compare_curricula(core_subjects: List[Dict], 
                     udla_subjects: List[Dict],
                     similarity_threshold: float = 0.8,
                     model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> Dict:
    """
    Compara materias troncales con las materias de la UDLA para identificar
    cuáles existen y cuáles faltan.
    
    Args:
        core_subjects: Lista de materias troncales
        udla_subjects: Lista de materias de la UDLA
        similarity_threshold: Umbral de similitud para considerar dos materias equivalentes
        model_name: Modelo de embeddings a utilizar
        
    Returns:
        Diccionario con las materias existentes y recomendadas
    """
    # Extraer nombres y descripciones de materias de la UDLA
    udla_names = [s['nombre'] for s in udla_subjects]
    udla_descriptions = [s.get('descripcion', '') for s in udla_subjects]
    
    # Crear texto combinado para materias de la UDLA
    udla_combined_texts = []
    for i, name in enumerate(udla_names):
        if udla_descriptions[i]:
            udla_combined_texts.append(f"{name} {name} {udla_descriptions[i]}")
        else:
            udla_combined_texts.append(name)
    
    # Obtener embeddings de materias de la UDLA
    udla_embeddings = batch_embed_documents(udla_combined_texts, model_name)
    
    # Comparar cada materia troncal con las de la UDLA
    existing_subjects = []
    missing_subjects = []
    
    for core_subject in core_subjects:
        # Crear embedding para el nombre general de la materia troncal
        core_embedding = get_embedding(core_subject["nombre_general"], model_name)
        
        # Verificar similitud con materias de la UDLA
        max_similarity = 0
        most_similar_subject = None
        
        for i, udla_embedding in enumerate(udla_embeddings):
            similarity = calculate_cosine_similarity(core_embedding, udla_embedding)
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_subject = udla_subjects[i]
        
        # Determinar si existe o no
        if max_similarity >= similarity_threshold:
            # La materia existe
            existing_subjects.append({
                "materia_troncal": core_subject["nombre_general"],
                "materia_udla": most_similar_subject["nombre"],
                "similitud": max_similarity,
                "area": core_subject["area_predominante"],
                "tipo": core_subject["tipo_predominante"],
                "semestre": most_similar_subject.get("semestre", "1")
            })
        else:
            # Determinar el semestre recomendado basado en materias similares o tipo de materia
            # Por defecto, asignamos al semestre 1 si no podemos determinar algo mejor
            semestre_sugerido = "1"
            
            # Revisamos si hay materias equivalentes con semestre asignado
            if "materias" in core_subject:
                semestres_equivalentes = [int(m.get("semestre", "1")) for m in core_subject["materias"] if m.get("semestre")]
                if semestres_equivalentes:
                    # Usar el semestre más común para esta materia
                    from collections import Counter
                    semestre_sugerido = str(Counter(semestres_equivalentes).most_common(1)[0][0])
            
            # La materia no existe
            missing_subjects.append({
                "nombre_recomendado": core_subject["nombre_general"],
                "alternativas": core_subject["materias_equivalentes"][:5],  # Top 5 alternativas
                "frecuencia": core_subject["frecuencia_relativa"],
                "area": core_subject["area_predominante"],
                "tipo": core_subject["tipo_predominante"],
                "semestre_sugerido": semestre_sugerido
            })
    
    return {
        "materias_existentes": existing_subjects,
        "materias_a_agregar": missing_subjects
    }


def generate_recommendations(comparison: Dict, 
                            udla_curriculum: Dict, 
                            core_subjects: List[Dict],
                            similarity_threshold: float = 0.85) -> Dict[str, List[str]]:
    """
    Genera recomendaciones para la malla curricular de UDLA.
    
    Args:
        comparison: Resultado de la comparación entre materias troncales y UDLA
        udla_curriculum: Malla curricular de UDLA
        core_subjects: Lista de materias troncales identificadas
        similarity_threshold: Umbral de similitud para considerar materias como duplicadas (0-100)
        
    Returns:
        Malla curricular recomendada
    """
    # Crear copia de la malla original
    recommended_curriculum = {}
    for semestre, materias in udla_curriculum['malla_curricular'].items():
        recommended_curriculum[semestre] = list(materias)
    
    # Crear lista plana de todas las materias existentes para verificación
    all_existing_subjects = []
    for semestre, materias in udla_curriculum['malla_curricular'].items():
        # Manejar tanto strings como diccionarios
        for materia in materias:
            if isinstance(materia, dict) and 'nombre' in materia:
                # Si la materia es un diccionario con campo 'nombre'
                all_existing_subjects.append(materia['nombre'].lower().strip())
            elif isinstance(materia, str):
                # Si la materia es directamente un string
                all_existing_subjects.append(materia.lower().strip())
            else:
                # Para otros formatos imprevistos, añadir un log o manejo específico
                print(f"Formato de materia no reconocido: {type(materia)}")
    
    # Procesar materias a agregar
    subjects_to_add = comparison.get('materias_a_agregar', [])
    
    for subject in subjects_to_add:
        # Extraer detalles relevantes
        nombre_recomendado = subject.get('nombre_recomendado', '')
        semestre_sugerido = subject.get('semestre_sugerido', '1')
        
        # Normalizar el nombre recomendado
        nombre_normalizado = nombre_recomendado.lower().strip()
        
        # Verificar si la materia ya existe (verificación exacta)
        if nombre_normalizado in all_existing_subjects:
            continue
        
        # Verificar si hay alguna materia muy similar (verificación fuzzy)
        is_duplicate = False
        for existing_subject in all_existing_subjects:
            # Comparamos con diferentes algoritmos de similitud para mayor seguridad
            ratio = fuzz.ratio(nombre_normalizado, existing_subject)
            partial_ratio = fuzz.partial_ratio(nombre_normalizado, existing_subject)
            token_sort_ratio = fuzz.token_sort_ratio(nombre_normalizado, existing_subject)
            
            # Si cualquier métrica de similitud supera el umbral, consideramos que es un duplicado
            if ratio > similarity_threshold or partial_ratio > 95 or token_sort_ratio > similarity_threshold:
                print(f"Materia similar encontrada: '{nombre_recomendado}' vs '{existing_subject}' - Similitud: {ratio}%")
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
            
        # Si no es duplicada, la añadimos al semestre sugerido
        if semestre_sugerido in recommended_curriculum:
            recommended_curriculum[semestre_sugerido].append(nombre_recomendado)
            # Añadimos a la lista de materias existentes para siguientes comparaciones
            all_existing_subjects.append(nombre_normalizado)
    
    return recommended_curriculum