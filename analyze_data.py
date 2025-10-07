import json
import re
from collections import Counter, defaultdict
import difflib

def normalize_text(text):
    """Normaliza texto para comparación"""
    if not text:
        return ""
    # Convertir a minúsculas y remover caracteres especiales
    text = re.sub(r'[^a-zA-ZáéíóúñÁÉÍÓÚÑ\s]', '', text.lower().strip())
    # Remover números romanos y ordinales
    text = re.sub(r'\b(i{1,3}v?|iv|vi{1,3}x?|ix|x+)\b', '', text)
    # Remover palabras comunes
    words_to_remove = ['de', 'la', 'el', 'en', 'y', 'a', 'para', 'con', 'del', 'las', 'los', 'al', 'por', 'un', 'una']
    words = text.split()
    words = [word for word in words if word not in words_to_remove and len(word) > 2]
    return ' '.join(words)

def extract_career_type(career_name):
    """Extrae el tipo base de carrera"""
    career_lower = normalize_text(career_name)
    
    if any(word in career_lower for word in ['software', 'sistemas', 'informacion', 'computacion', 'informatica']):
        return 'Ingeniería en Software/Sistemas/Computación'
    elif 'civil' in career_lower:
        return 'Ingeniería Civil'
    elif any(word in career_lower for word in ['industrial', 'produccion']):
        return 'Ingeniería Industrial/Producción'
    elif any(word in career_lower for word in ['electronica', 'automatizacion', 'telecomunicaciones']):
        return 'Ingeniería Electrónica/Automatización/Telecomunicaciones'
    elif 'ambiental' in career_lower:
        return 'Ingeniería Ambiental'
    elif 'alimentos' in career_lower:
        return 'Ingeniería de Alimentos'
    elif any(word in career_lower for word in ['mecanica', 'automotriz']):
        return 'Ingeniería Mecánica/Automotriz'
    elif any(word in career_lower for word in ['biotecnologia', 'bioingenieria']):
        return 'Biotecnología/Bioingeniería'
    elif 'quimica' in career_lower:
        return 'Ingeniería Química'
    elif 'minas' in career_lower:
        return 'Ingeniería de Minas'
    elif any(word in career_lower for word in ['energia', 'energias']):
        return 'Ingeniería en Energías'
    elif 'agroempresa' in career_lower or 'agronomia' in career_lower:
        return 'Ingeniería Agrícola/Agronomía'
    else:
        return 'Otras Ingenierías'

def analyze_dataset():
    """Analiza el dataset completo"""
    print("=" * 80)
    print("ANÁLISIS COMPLETO DEL DATASET DE CARRERAS UNIVERSITARIAS")
    print("=" * 80)
    
    # Cargar datos
    with open('data/universidades.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Estadísticas básicas
    total_carreras_registros = len(data)
    universidades = set([item['universidad'] for item in data])
    total_universidades = len(universidades)
    
    # Contar carreras únicas (normalizando nombres)
    carreras_unicas = set()
    carreras_detalle = {}
    
    for item in data:
        carrera_normalizada = normalize_text(item['carrera'])
        carreras_unicas.add(carrera_normalizada)
        
        if carrera_normalizada not in carreras_detalle:
            carreras_detalle[carrera_normalizada] = {
                'nombre_original': item['carrera'],
                'universidades': set(),
                'variaciones': set()
            }
        
        carreras_detalle[carrera_normalizada]['universidades'].add(item['universidad'])
        carreras_detalle[carrera_normalizada]['variaciones'].add(item['carrera'])
    
    # Contar materias totales
    total_materias = 0
    all_subjects = []
    
    for item in data:
        for semestre, materias in item['malla_curricular'].items():
            total_materias += len(materias)
            all_subjects.extend(materias)
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   • Total de registros en el dataset: {total_carreras_registros}")
    print(f"   • Carreras únicas (nombres únicos): {len(carreras_unicas)}")
    print(f"   • Total de universidades: {total_universidades}")
    print(f"   • Total de materias (con repeticiones): {total_materias}")
    print(f"   • Materias únicas: {len(set(all_subjects))}")
    
    print(f"\n� ANÁLISIS DE CARRERAS ÚNICAS:")
    carreras_con_multiples_unis = [
        (carrera, detalles) for carrera, detalles in carreras_detalle.items() 
        if len(detalles['universidades']) > 1
    ]
    
    print(f"   • Carreras ofrecidas por múltiples universidades: {len(carreras_con_multiples_unis)}")
    print(f"   • Carreras exclusivas de una universidad: {len(carreras_unicas) - len(carreras_con_multiples_unis)}")
    
    # Mostrar las carreras más populares (ofrecidas por más universidades)
    carreras_populares = sorted(carreras_con_multiples_unis, 
                               key=lambda x: len(x[1]['universidades']), 
                               reverse=True)[:10]
    
    print(f"\n🏆 TOP 10 CARRERAS MÁS OFRECIDAS:")
    for i, (carrera, detalles) in enumerate(carreras_populares, 1):
        print(f"   {i:2d}. {detalles['nombre_original']}")
        print(f"       → Ofrecida por {len(detalles['universidades'])} universidades")
        if len(detalles['variaciones']) > 1:
            print(f"       → Variaciones: {', '.join(sorted(detalles['variaciones']))}")
        print()
    
    print(f"\n�🏫 UNIVERSIDADES EN EL DATASET:")
    for i, uni in enumerate(sorted(universidades), 1):
        carreras_uni = [item['carrera'] for item in data if item['universidad'] == uni]
        print(f"   {i:2d}. {uni} ({len(carreras_uni)} carreras)")
    
    return data, carreras_detalle

def group_careers_by_type(data):
    """Agrupa carreras por tipo"""
    print("\n" + "=" * 80)
    print("AGRUPACIÓN DE CARRERAS POR TIPO")
    print("=" * 80)
    
    groups = defaultdict(list)
    
    for item in data:
        career_type = extract_career_type(item['carrera'])
        
        # Calcular total de materias
        total_materias = sum(len(materias) for materias in item['malla_curricular'].values())
        
        groups[career_type].append({
            'universidad': item['universidad'],
            'carrera': item['carrera'],
            'total_materias': total_materias,
            'malla_curricular': item['malla_curricular']
        })
    
    # Mostrar grupos
    for group_name, careers in groups.items():
        print(f"\n🎓 GRUPO: {group_name}")
        print(f"   Total de carreras: {len(careers)}")
        
        # Universidades en este grupo
        universidades_grupo = set([career['universidad'] for career in careers])
        print(f"   Universidades ({len(universidades_grupo)}):")
        for uni in sorted(universidades_grupo):
            carreras_uni = [c['carrera'] for c in careers if c['universidad'] == uni]
            print(f"      • {uni}: {len(carreras_uni)} carrera(s)")
            for carrera in carreras_uni:
                print(f"        - {carrera}")
        
        print()
    
    return groups

def find_equivalent_subjects_advanced(groups):
    """Encuentra materias equivalentes usando múltiples técnicas"""
    print("\n" + "=" * 80)
    print("ANÁLISIS DE MATERIAS EQUIVALENTES")
    print("=" * 80)
    
    for group_name, careers in groups.items():
        if len(careers) < 2:  # Solo analizar grupos con múltiples carreras
            continue
            
        print(f"\n📚 GRUPO: {group_name}")
        print("-" * 60)
        
        # Recopilar todas las materias del grupo
        subject_data = []
        for career in careers:
            for semestre, materias in career['malla_curricular'].items():
                for materia in materias:
                    subject_data.append({
                        'materia_original': materia,
                        'materia_normalizada': normalize_text(materia),
                        'universidad': career['universidad'],
                        'carrera': career['carrera'],
                        'semestre': semestre
                    })
        
        # Agrupar materias similares
        equivalent_groups = find_similar_subjects(subject_data)
        
        if equivalent_groups:
            print(f"   Se encontraron {len(equivalent_groups)} grupos de materias equivalentes:")
            
            for i, eq_group in enumerate(equivalent_groups, 1):
                if len(eq_group) >= 2:  # Solo mostrar grupos con al menos 2 materias
                    print(f"\n   {i}. MATERIAS EQUIVALENTES:")
                    
                    # Mostrar todas las materias del grupo
                    for subject in eq_group:
                        print(f"      • \"{subject['materia_original']}\"")
                        print(f"        → {subject['universidad']} - Semestre {subject['semestre']}")
                    
                    # Explicar por qué se consideran equivalentes
                    normalized_subjects = [s['materia_normalizada'] for s in eq_group]
                    common_words = find_common_words(normalized_subjects)
                    if common_words:
                        print(f"      💡 Palabras clave comunes: {', '.join(common_words)}")
                    print()
        else:
            print("   No se encontraron materias equivalentes claras en este grupo.")

def find_similar_subjects(subject_data):
    """Encuentra materias similares usando diferentes técnicas"""
    groups = []
    used_indices = set()
    
    for i, subject1 in enumerate(subject_data):
        if i in used_indices:
            continue
        
        current_group = [subject1]
        used_indices.add(i)
        
        for j, subject2 in enumerate(subject_data[i+1:], i+1):
            if j in used_indices:
                continue
            
            # Verificar similitud
            if are_subjects_similar(subject1, subject2):
                current_group.append(subject2)
                used_indices.add(j)
        
        if len(current_group) > 1:
            groups.append(current_group)
    
    return groups

def are_subjects_similar(subject1, subject2):
    """Determina si dos materias son similares"""
    # No comparar materias de la misma universidad
    if subject1['universidad'] == subject2['universidad']:
        return False
    
    norm1 = subject1['materia_normalizada']
    norm2 = subject2['materia_normalizada']
    
    # Técnica 1: Similitud exacta después de normalización
    if norm1 == norm2:
        return True
    
    # Técnica 2: Una materia contiene a la otra
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Técnica 3: Similitud de palabras clave
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if len(words1) > 0 and len(words2) > 0:
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        jaccard_similarity = intersection / union if union > 0 else 0
        
        if jaccard_similarity >= 0.6:  # 60% de similitud
            return True
    
    # Técnica 4: Similitud de secuencia usando difflib
    similarity_ratio = difflib.SequenceMatcher(None, norm1, norm2).ratio()
    if similarity_ratio >= 0.75:  # 75% de similitud
        return True
    
    return False

def find_common_words(normalized_subjects):
    """Encuentra palabras comunes entre materias"""
    word_counts = Counter()
    
    for subject in normalized_subjects:
        words = subject.split()
        word_counts.update(words)
    
    # Retornar palabras que aparecen en al menos la mitad de las materias
    min_count = len(normalized_subjects) // 2
    common_words = [word for word, count in word_counts.items() if count >= min_count and len(word) > 2]
    
    return common_words

def main():
    try:
        # Análisis completo
        data, carreras_detalle = analyze_dataset()
        groups = group_careers_by_type(data)
        find_equivalent_subjects_advanced(groups)
        
        print("\n" + "=" * 80)
        print("RESUMEN FINAL - CARRERAS ÚNICAS VS REGISTROS")
        print("=" * 80)
        
        # Análisis final de duplicados
        print(f"\n📈 RESUMEN DE DUPLICACIONES:")
        total_registros = len(data)
        carreras_unicas = len(carreras_detalle)
        
        print(f"   • Total de registros en dataset: {total_registros}")
        print(f"   • Carreras realmente únicas: {carreras_unicas}")
        print(f"   • Factor de duplicación: {total_registros/carreras_unicas:.1f}x")
        print(f"   • Registros 'duplicados': {total_registros - carreras_unicas}")
        
        # Mostrar ejemplos de duplicación
        print(f"\n🔍 EJEMPLOS DE CARRERAS 'DUPLICADAS' MÁS COMUNES:")
        duplicadas = [(carrera, detalles) for carrera, detalles in carreras_detalle.items() 
                     if len(detalles['universidades']) > 2]
        duplicadas_ordenadas = sorted(duplicadas, 
                                    key=lambda x: len(x[1]['universidades']), 
                                    reverse=True)[:5]
        
        for carrera, detalles in duplicadas_ordenadas:
            print(f"\n   📚 {detalles['nombre_original']}")
            print(f"      → Aparece en {len(detalles['universidades'])} universidades:")
            for uni in sorted(detalles['universidades']):
                print(f"        • {uni}")
            if len(detalles['variaciones']) > 1:
                print(f"      → Variaciones de nombre: {len(detalles['variaciones'])}")
                for var in sorted(detalles['variaciones']):
                    print(f"        - \"{var}\"")
        
        print("\n" + "=" * 80)
        print("ANÁLISIS COMPLETADO")
        print("=" * 80)
        
    except FileNotFoundError:
        print("❌ Error: No se encuentra el archivo 'data/universidades.json'")
        print("   Asegúrate de que el archivo existe en la carpeta 'data'")
    except Exception as e:
        print(f"❌ Error durante el análisis: {str(e)}")

if __name__ == "__main__":
    main()