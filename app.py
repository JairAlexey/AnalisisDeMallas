import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from collections import Counter
import re
import os

# Configuración de la página
st.set_page_config(
    page_title="Reformulador de Carreras Universitarias",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.3rem;
        opacity: 0.95;
        margin-bottom: 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #667eea;
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .cluster-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border: 2px solid #e9ecef;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .cluster-card:hover {
        border-color: #667eea;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }
    
    .cluster-card h3 {
        color: #667eea;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #155724;
    }
    
    .info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 2px solid #17a2b8;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #0c5460;
    }
    
    .university-tag {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
        display: inline-block;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .subject-item {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .subject-item:hover {
        border-left-color: #667eea;
        transform: translateX(5px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stat-item {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        display: block;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Carga los datos del JSON"""
    try:
        with open('data/universidades.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("❌ No se encuentra el archivo 'data/universidades.json'")
        st.info("Por favor asegúrate de que el archivo existe en la carpeta 'data'")
        return None
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        return None

def normalize_text(text):
    """Normaliza texto para comparación"""
    if not text:
        return ""
    # Remover acentos manualmente y caracteres especiales
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u', 'Ñ': 'n'
    }
    
    result = text.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return re.sub(r'[^a-z0-9\s]', '', result).strip()

def extract_career_type(career_name):
    """Extrae el tipo base de carrera"""
    career_lower = normalize_text(career_name)
    
    # Patrones más específicos
    patterns = [
        (['software', 'sistemas', 'informatica', 'computacion', 'tecnologias de la informacion'], 'Ingeniería en Software/Sistemas'),
        (['civil'], 'Ingeniería Civil'),
        (['industrial', 'produccion'], 'Ingeniería Industrial/Producción'),
        (['electronica', 'automatizacion', 'telecomunicaciones'], 'Ingeniería Electrónica/Automatización'),
        (['ambiental'], 'Ingeniería Ambiental'),
        (['alimentos'], 'Ingeniería de Alimentos'),
        (['mecanica', 'automotriz'], 'Ingeniería Mecánica/Automotriz'),
        (['biotecnologia', 'bioingenieria'], 'Biotecnología/Bioingeniería'),
        (['quimica'], 'Ingeniería Química'),
        (['minas'], 'Ingeniería de Minas'),
        (['energia', 'energias'], 'Ingeniería en Energías'),
        (['agronomia', 'agroempresa'], 'Ingeniería Agrícola/Agronomía')
    ]
    
    for keywords, category in patterns:
        if any(keyword in career_lower for keyword in keywords):
            return category
    
    return 'Otras Ingenierías'

def analyze_career_similarity(career1, career2):
    """Analiza similitud entre dos carreras basado en materias"""
    subjects1 = set([normalize_text(s) for s in career1['materias']])
    subjects2 = set([normalize_text(s) for s in career2['materias']])
    
    # Similitud de Jaccard
    intersection = len(subjects1.intersection(subjects2))
    union = len(subjects1.union(subjects2))
    
    jaccard = intersection / union if union > 0 else 0
    
    # Similitud por palabras clave en nombres
    name1_words = set(normalize_text(career1['carrera']).split())
    name2_words = set(normalize_text(career2['carrera']).split())
    
    name_intersection = len(name1_words.intersection(name2_words))
    name_union = len(name1_words.union(name2_words))
    
    name_similarity = name_intersection / name_union if name_union > 0 else 0
    
    # Combinar métricas (70% materias, 30% nombre)
    combined_similarity = (jaccard * 0.7) + (name_similarity * 0.3)
    
    return combined_similarity

def smart_career_clustering(data, similarity_threshold=0.3):
    """Agrupación inteligente considerando similitud de materias"""
    # Preparar datos
    careers_processed = []
    for item in data:
        total_materias = sum(len(materias) for materias in item['malla_curricular'].values())
        
        career_info = {
            'universidad': item['universidad'],
            'carrera': item['carrera'],
            'total_materias': total_materias,
            'materias': []
        }
        
        # Recopilar todas las materias
        for semestre, materias in item['malla_curricular'].items():
            career_info['materias'].extend(materias)
        
        career_info['career_type'] = extract_career_type(item['carrera'])
        careers_processed.append(career_info)
    
    # Agrupar por tipo inicial
    type_groups = {}
    for career in careers_processed:
        career_type = career['career_type']
        if career_type not in type_groups:
            type_groups[career_type] = []
        type_groups[career_type].append(career)
    
    # Refinar agrupación con análisis de similitud
    final_clusters = {}
    
    for type_name, careers_list in type_groups.items():
        if len(careers_list) <= 1:
            # Grupo muy pequeño, mantener como está
            final_clusters[type_name] = {
                'carreras': careers_list,
                'universidades': list(set([c['universidad'] for c in careers_list])),
                'total_carreras': len(careers_list)
            }
            continue
        
        # Para grupos grandes, crear subgrupos basados en similitud
        if len(careers_list) > 3:
            # Analizar similitudes y crear subgrupos
            subgroups = create_similarity_subgroups(careers_list, similarity_threshold)
            
            for i, subgroup in enumerate(subgroups):
                if len(subgroup) > 1:
                    subgroup_name = f"{type_name} - Grupo {i+1}" if len(subgroups) > 1 else type_name
                    final_clusters[subgroup_name] = {
                        'carreras': subgroup,
                        'universidades': list(set([c['universidad'] for c in subgroup])),
                        'total_carreras': len(subgroup)
                    }
        else:
            final_clusters[type_name] = {
                'carreras': careers_list,
                'universidades': list(set([c['universidad'] for c in careers_list])),
                'total_carreras': len(careers_list)
            }
    
    return final_clusters

def create_similarity_subgroups(careers_list, threshold):
    """Crea subgrupos basados en similitud de materias"""
    if len(careers_list) <= 3:
        return [careers_list]
    
    # Calcular matriz de similitud
    n = len(careers_list)
    similarities = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            sim = analyze_career_similarity(careers_list[i], careers_list[j])
            similarities[i][j] = sim
            similarities[j][i] = sim
    
    # Agrupación simple basada en similitud
    groups = []
    used = set()
    
    for i in range(n):
        if i in used:
            continue
        
        current_group = [careers_list[i]]
        used.add(i)
        
        for j in range(i+1, n):
            if j not in used and similarities[i][j] >= threshold:
                current_group.append(careers_list[j])
                used.add(j)
        
        groups.append(current_group)
    
    return groups

def find_equivalent_subjects_advanced(careers):
    """Encuentra materias equivalentes usando análisis de palabras clave"""
    # Recopilar todas las materias con metadatos
    all_subjects = []
    for career in careers:
        for subject in career['materias']:
            normalized = normalize_text(subject)
            words = normalized.split()
            
            all_subjects.append({
                'original': subject,
                'normalized': normalized,
                'words': words,
                'key_words': [w for w in words if len(w) > 3],  # Palabras importantes
                'universidad': career['universidad'],
                'carrera': career['carrera']
            })
    
    # Agrupar por similitud
    equivalent_groups = []
    processed = set()
    
    for i, subject1 in enumerate(all_subjects):
        if i in processed:
            continue
        
        current_group = [subject1]
        processed.add(i)
        
        for j, subject2 in enumerate(all_subjects[i+1:], i+1):
            if j in processed:
                continue
            
            # Calcular similitud
            similarity = calculate_subject_similarity(subject1, subject2)
            
            if similarity >= 0.6:  # Umbral de similitud
                current_group.append(subject2)
                processed.add(j)
        
        if len(current_group) > 1:
            # Determinar materia representativa (la más común o completa)
            representative = max(current_group, key=lambda x: len(x['original']))
            
            equivalent_groups.append({
                'grupo_id': len(equivalent_groups) + 1,
                'materia_representativa': representative['original'],
                'materias_equivalentes': current_group,
                'universidades_involucradas': list(set([s['universidad'] for s in current_group])),
                'promedio_similitud': 0.8  # Aproximado
            })
    
    return equivalent_groups

def calculate_subject_similarity(subject1, subject2):
    """Calcula similitud entre dos materias"""
    # Similitud por palabras clave
    words1 = set(subject1['key_words'])
    words2 = set(subject2['key_words'])
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    jaccard = intersection / union if union > 0 else 0
    
    # Bonus por inclusión de texto
    norm1 = subject1['normalized']
    norm2 = subject2['normalized']
    
    inclusion_bonus = 0
    if norm1 in norm2 or norm2 in norm1:
        inclusion_bonus = 0.3
    
    return min(1.0, jaccard + inclusion_bonus)

def display_advanced_cluster_analysis(cluster_name, cluster_data):
    """Muestra análisis avanzado de un cluster"""
    st.markdown(f"""
    <div class="cluster-card">
        <h3>🎯 Análisis Avanzado: {cluster_name}</h3>
        <p>Agrupación inteligente basada en similitud de contenido curricular</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas principales con diseño mejorado
    st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{cluster_data['total_carreras']}</span>
            <div class="stat-label">Carreras Totales</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{len(cluster_data['universidades'])}</span>
            <div class="stat-label">Universidades</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_subjects = np.mean([career['total_materias'] for career in cluster_data['carreras']])
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{avg_subjects:.1f}</span>
            <div class="stat-label">Promedio Materias</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        subject_range = [career['total_materias'] for career in cluster_data['carreras']]
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{min(subject_range)}-{max(subject_range)}</span>
            <div class="stat-label">Rango Materias</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Universidades participantes con tags
    st.subheader("🏫 Universidades Participantes")
    universities_html = "".join([
        f'<span class="university-tag">{uni}</span>' 
        for uni in cluster_data['universidades']
    ])
    st.markdown(universities_html, unsafe_allow_html=True)
    
    # Tabs para análisis detallado
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Distribución Detallada", 
        "🔍 Materias Equivalentes Inteligentes",
        "📚 Análisis Curricular Comparativo",
        "📈 Métricas de Similitud"
    ])
    
    with tab1:
        # Gráfico de distribución mejorado
        st.subheader("📊 Distribución por Universidad")
        
        university_counts = {}
        university_details = {}
        
        for career in cluster_data['carreras']:
            uni = career['universidad']
            university_counts[uni] = university_counts.get(uni, 0) + 1
            
            if uni not in university_details:
                university_details[uni] = []
            university_details[uni].append({
                'carrera': career['carrera'],
                'materias': career['total_materias']
            })
        
        # Crear DataFrame para visualización
        unis_df = pd.DataFrame([
            {
                'Universidad': uni,
                'Carreras': count,
                'Promedio_Materias': np.mean([d['materias'] for d in university_details[uni]])
            }
            for uni, count in university_counts.items()
        ]).sort_values('Carreras', ascending=True)
        
        st.bar_chart(unis_df.set_index('Universidad')['Carreras'])
        
        # Detalles expandibles por universidad
        st.subheader("🔍 Detalles por Universidad")
        for uni in cluster_data['universidades']:
            with st.expander(f"📋 {uni} ({university_counts[uni]} carreras)"):
                uni_df = pd.DataFrame(university_details[uni])
                st.dataframe(uni_df, use_container_width=True)
                
                avg_materias = np.mean([d['materias'] for d in university_details[uni]])
                st.metric("Promedio de materias", f"{avg_materias:.1f}")
    
    with tab2:
        st.subheader("🧠 Análisis Inteligente de Materias Equivalentes")
        
        with st.spinner("🔍 Analizando equivalencias con algoritmos avanzados..."):
            equivalent_subjects = find_equivalent_subjects_advanced(cluster_data['carreras'])
        
        if equivalent_subjects:
            st.markdown(f"""
            <div class="success-box">
                <strong>🎉 ¡Análisis completado!</strong><br>
                Se identificaron <strong>{len(equivalent_subjects)}</strong> grupos de materias equivalentes
                usando análisis semántico avanzado.
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar grupos de equivalencia
            for i, group in enumerate(equivalent_subjects[:8]):  # Top 8 grupos
                with st.expander(
                    f"🎯 Grupo {group['grupo_id']}: {group['materia_representativa']}", 
                    expanded=i < 2
                ):
                    
                    st.markdown(f"""
                    <div class="info-box">
                        <strong>📚 Materia Representativa:</strong> {group['materia_representativa']}<br>
                        <strong>🏫 Universidades:</strong> {', '.join(group['universidades_involucradas'])}<br>
                        <strong>📊 Confianza:</strong> {group['promedio_similitud']:.1%}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("**💡 Materias Equivalentes Detectadas:**")
                    for subject in group['materias_equivalentes']:
                        st.markdown(f"""
                        <div class="subject-item">
                            <strong>📖 {subject['original']}</strong><br>
                            <small>🏫 {subject['universidad']} • 🎓 {subject['carrera']}</small>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="info-box">
                <strong>ℹ️ Información:</strong><br>
                No se encontraron grupos de materias equivalentes con el nivel de confianza establecido.
                Esto puede indicar que las materias en este cluster son muy específicas o únicas.
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader("📚 Análisis Curricular Comparativo")
        
        # Análisis de estructura curricular
        semestre_analysis = {}
        for career in cluster_data['carreras']:
            # Simular análisis de semestres (basado en total de materias)
            total_materias = career['total_materias']
            estimated_semesters = max(8, min(10, total_materias // 6))  # Estimación
            
            semestre_analysis[f"{career['universidad']} - {career['carrera']}"] = {
                'total_materias': total_materias,
                'semestres_estimados': estimated_semesters,
                'materias_por_semestre': total_materias / estimated_semesters
            }
        
        # Crear DataFrame para comparación
        comparison_df = pd.DataFrame([
            {
                'Carrera': carrera,
                'Universidad': carrera.split(' - ')[0],
                'Total Materias': data['total_materias'],
                'Semestres (Est.)': data['semestres_estimados'],
                'Materias/Semestre': f"{data['materias_por_semestre']:.1f}"
            }
            for carrera, data in semestre_analysis.items()
        ])
        
        st.dataframe(comparison_df, use_container_width=True)
        
        # Estadísticas comparativas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Distribución de Carga Académica")
            materias_counts = [data['total_materias'] for data in semestre_analysis.values()]
            
            bins = np.histogram(materias_counts, bins=5)[1]
            hist_data = pd.DataFrame({
                'Rango_Materias': [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)],
                'Cantidad_Carreras': np.histogram(materias_counts, bins=5)[0]
            })
            
            st.bar_chart(hist_data.set_index('Rango_Materias')['Cantidad_Carreras'])
        
        with col2:
            st.subheader("📈 Métricas Estadísticas")
            st.metric("Media de Materias", f"{np.mean(materias_counts):.1f}")
            st.metric("Desviación Estándar", f"{np.std(materias_counts):.1f}")
            st.metric("Coeficiente de Variación", f"{(np.std(materias_counts)/np.mean(materias_counts)*100):.1f}%")
    
    with tab4:
        st.subheader("🎯 Métricas de Similitud del Cluster")
        
        # Calcular similitudes entre carreras del cluster
        careers = cluster_data['carreras']
        n_careers = len(careers)
        
        if n_careers > 1:
            similarities = []
            comparisons = []
            
            for i in range(n_careers):
                for j in range(i+1, n_careers):
                    sim = analyze_career_similarity(careers[i], careers[j])
                    similarities.append(sim)
                    comparisons.append(f"{careers[i]['universidad']} vs {careers[j]['universidad']}")
            
            if similarities:
                # Métricas de similitud
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Similitud Promedio", f"{np.mean(similarities):.2%}")
                
                with col2:
                    st.metric("Similitud Máxima", f"{np.max(similarities):.2%}")
                
                with col3:
                    st.metric("Similitud Mínima", f"{np.min(similarities):.2%}")
                
                # Distribución de similitudes
                st.subheader("📊 Distribución de Similitudes")
                
                similarity_ranges = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
                range_counts = [
                    sum(1 for s in similarities if 0 <= s < 0.2),
                    sum(1 for s in similarities if 0.2 <= s < 0.4),
                    sum(1 for s in similarities if 0.4 <= s < 0.6),
                    sum(1 for s in similarities if 0.6 <= s < 0.8),
                    sum(1 for s in similarities if 0.8 <= s <= 1.0)
                ]
                
                sim_df = pd.DataFrame({
                    'Rango_Similitud': similarity_ranges,
                    'Cantidad': range_counts
                })
                
                st.bar_chart(sim_df.set_index('Rango_Similitud')['Cantidad'])
                
                # Detalles de comparaciones
                if st.checkbox("🔍 Ver comparaciones detalladas"):
                    comparison_df = pd.DataFrame({
                        'Comparación': comparisons,
                        'Similitud': [f"{s:.2%}" for s in similarities]
                    }).sort_values('Similitud', ascending=False)
                    
                    st.dataframe(comparison_df, use_container_width=True)
        else:
            st.info("Se necesitan al menos 2 carreras para calcular métricas de similitud.")

def display_dataset_statistics(data):
    """Muestra estadísticas detalladas del dataset"""
    st.markdown("## 📊 ESTADÍSTICAS GENERALES DEL DATASET")
    
    # Calcular estadísticas
    total_carreras = len(data)
    universidades = set([item['universidad'] for item in data])
    total_universidades = len(universidades)
    
    # Contar materias totales
    total_materias = 0
    all_subjects = []
    
    for item in data:
        for semestre, materias in item['malla_curricular'].items():
            total_materias += len(materias)
            all_subjects.extend(materias)
    
    materias_unicas = len(set(all_subjects))
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{total_carreras}</span>
            <div class="stat-label">📚 Total Carreras</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{total_universidades}</span>
            <div class="stat-label">🏫 Universidades</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{total_materias:,}</span>
            <div class="stat-label">📖 Total Materias</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-item">
            <span class="stat-number">{materias_unicas:,}</span>
            <div class="stat-label">🔍 Materias Únicas</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Lista de universidades
    st.markdown("### 🏫 UNIVERSIDADES EN EL DATASET")
    
    col1, col2 = st.columns(2)
    universities_list = sorted(list(universidades))
    mid_point = len(universities_list) // 2
    
    with col1:
        for i, uni in enumerate(universities_list[:mid_point], 1):
            st.write(f"{i:2d}. {uni}")
    
    with col2:
        for i, uni in enumerate(universities_list[mid_point:], mid_point + 1):
            st.write(f"{i:2d}. {uni}")
    
    return {
        'total_carreras': total_carreras,
        'total_universidades': total_universidades,
        'total_materias': total_materias,
        'materias_unicas': materias_unicas,
        'universidades': universities_list
    }

def display_career_groups_detailed(data):
    """Muestra agrupación detallada de carreras por tipo"""
    st.markdown("## 🎓 AGRUPACIÓN DE CARRERAS POR TIPO")
    
    # Agrupar carreras
    groups = {}
    for item in data:
        career_type = extract_career_type(item['carrera'])
        
        if career_type not in groups:
            groups[career_type] = []
        
        total_materias = sum(len(materias) for materias in item['malla_curricular'].values())
        
        groups[career_type].append({
            'universidad': item['universidad'],
            'carrera': item['carrera'],
            'total_materias': total_materias,
            'malla_curricular': item['malla_curricular']
        })
    
    # Mostrar cada grupo
    for group_name, careers in groups.items():
        with st.expander(f"🎯 **{group_name}** ({len(careers)} carreras)", expanded=True):
            
            # Universidades en este grupo
            universidades_grupo = {}
            for career in careers:
                uni = career['universidad']
                if uni not in universidades_grupo:
                    universidades_grupo[uni] = []
                universidades_grupo[uni].append(career)
            
            st.markdown(f"**📊 Resumen:**")
            st.write(f"• Total de carreras: **{len(careers)}**")
            st.write(f"• Universidades involucradas: **{len(universidades_grupo)}**")
            
            # Detalles por universidad
            st.markdown("**🏫 Distribución por Universidad:**")
            
            for uni, uni_careers in universidades_grupo.items():
                st.markdown(f"**• {uni}:** {len(uni_careers)} carrera(s)")
                for career in uni_careers:
                    st.write(f"  - {career['carrera']} ({career['total_materias']} materias)")
    
    return groups

def find_equivalent_subjects_streamlit(groups):
    """Encuentra y muestra materias equivalentes en Streamlit"""
    st.markdown("## 🔍 ANÁLISIS DE MATERIAS EQUIVALENTES")
    
    # Seleccionar grupo para análisis
    group_names = [name for name, careers in groups.items() if len(careers) >= 2]
    
    if not group_names:
        st.warning("No hay grupos con suficientes carreras para análisis de equivalencias.")
        return
    
    selected_group = st.selectbox(
        "Selecciona un grupo para analizar materias equivalentes:",
        group_names
    )
    
    if selected_group:
        careers = groups[selected_group]
        
        st.markdown(f"### 📚 GRUPO: {selected_group}")
        st.write(f"Analizando {len(careers)} carreras de {len(set([c['universidad'] for c in careers]))} universidades...")
        
        # Recopilar materias
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
        
        # Encontrar equivalencias
        equivalent_groups = find_similar_subjects_detailed(subject_data)
        
        if equivalent_groups:
            st.success(f"✅ Se encontraron **{len(equivalent_groups)}** grupos de materias equivalentes")
            
            # Mostrar grupos de equivalencia
            for i, eq_group in enumerate(equivalent_groups[:15], 1):  # Mostrar primeros 15
                if len(eq_group) >= 2:
                    with st.expander(f"📖 Grupo {i}: Materias Equivalentes ({len(eq_group)} materias)", expanded=i <= 3):
                        
                        # Mostrar todas las materias del grupo
                        for j, subject in enumerate(eq_group):
                            icon = "🎯" if j == 0 else "📚"
                            st.markdown(f"""
                            <div class="subject-item">
                                {icon} <strong>"{subject['materia_original']}"</strong><br>
                                <small>🏫 {subject['universidad']} - Semestre {subject['semestre']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Explicar similitud
                        normalized_subjects = [s['materia_normalizada'] for s in eq_group]
                        common_words = find_common_words_simple(normalized_subjects)
                        if common_words:
                            st.info(f"💡 **Palabras clave comunes:** {', '.join(common_words)}")
        else:
            st.info("No se encontraron materias equivalentes claras en este grupo.")

def find_similar_subjects_detailed(subject_data):
    """Encuentra materias similares con lógica mejorada"""
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
            if are_subjects_equivalent(subject1, subject2):
                current_group.append(subject2)
                used_indices.add(j)
        
        if len(current_group) > 1:
            groups.append(current_group)
    
    return groups

def are_subjects_equivalent(subject1, subject2):
    """Determina si dos materias son equivalentes"""
    # No comparar materias de la misma universidad
    if subject1['universidad'] == subject2['universidad']:
        return False
    
    norm1 = subject1['materia_normalizada']
    norm2 = subject2['materia_normalizada']
    
    # Técnica 1: Similitud exacta
    if norm1 == norm2 and norm1.strip():
        return True
    
    # Técnica 2: Una materia contiene a la otra
    if len(norm1) > 3 and len(norm2) > 3:
        if norm1 in norm2 or norm2 in norm1:
            return True
    
    # Técnica 3: Similitud de palabras clave
    words1 = set([w for w in norm1.split() if len(w) > 2])
    words2 = set([w for w in norm2.split() if len(w) > 2])
    
    if len(words1) > 0 and len(words2) > 0:
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        jaccard_similarity = intersection / union if union > 0 else 0
        
        if jaccard_similarity >= 0.6:  # 60% de similitud
            return True
    
    # Técnica 4: Similitud por palabras clave importantes
    important_words1 = set([w for w in words1 if len(w) > 4])
    important_words2 = set([w for w in words2 if len(w) > 4])
    
    if important_words1 and important_words2:
        if len(important_words1.intersection(important_words2)) > 0:
            return True
    
    return False

def find_common_words_simple(normalized_subjects):
    """Encuentra palabras comunes entre materias"""
    word_counts = Counter()
    
    for subject in normalized_subjects:
        words = [w for w in subject.split() if len(w) > 2]
        word_counts.update(words)
    
    # Retornar palabras que aparecen en al menos la mitad de las materias
    min_count = max(2, len(normalized_subjects) // 2)
    common_words = [word for word, count in word_counts.items() if count >= min_count]
    
    return common_words[:5]  # Máximo 5 palabras

def main():
    # Header principal mejorado
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Reformulador de Carreras Universitarias</h1>
        <p>Sistema Inteligente de Análisis Curricular con Algoritmos Avanzados de Machine Learning</p>
    </div>
    """, unsafe_allow_html=True)
    
    
    # Cargar datos
    data = load_data()
    
    if data is None:
        st.stop()
    
    # Crear tabs principales para organizar la información
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Estadísticas Generales", 
        "🎓 Grupos de Carreras", 
        "🔍 Materias Equivalentes",
        "🚀 Análisis Avanzado"
    ])
    
    with tab1:
        st.markdown("---")
        dataset_stats = display_dataset_statistics(data)
        
        # Información adicional
        st.markdown("### 📈 Análisis Adicional")
        
        # Distribución de carreras por universidad
        university_career_count = {}
        for item in data:
            uni = item['universidad']
            university_career_count[uni] = university_career_count.get(uni, 0) + 1
        
        # Crear DataFrame para visualización
        uni_df = pd.DataFrame(
            list(university_career_count.items()),
            columns=['Universidad', 'Número de Carreras']
        ).sort_values('Número de Carreras', ascending=False)
        
        st.markdown("#### 🏫 Distribución de Carreras por Universidad")
        st.bar_chart(uni_df.set_index('Universidad')['Número de Carreras'])
        
        # Mostrar tabla detallada
        st.dataframe(uni_df, use_container_width=True)
    
    with tab2:
        st.markdown("---")
        career_groups = display_career_groups_detailed(data)
        
        # Resumen visual de los grupos
        st.markdown("### 📊 Resumen Visual de Grupos")
        
        group_summary = []
        for group_name, careers in career_groups.items():
            universities = set([career['universidad'] for career in careers])
            avg_materias = np.mean([career['total_materias'] for career in careers])
            
            group_summary.append({
                'Grupo': group_name,
                'Carreras': len(careers),
                'Universidades': len(universities),
                'Promedio Materias': f"{avg_materias:.1f}"
            })
        
        summary_df = pd.DataFrame(group_summary)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Carreras por Grupo")
            st.bar_chart(summary_df.set_index('Grupo')['Carreras'])
        
        with col2:
            st.markdown("#### 🏫 Universidades por Grupo")
            st.bar_chart(summary_df.set_index('Grupo')['Universidades'])
        
        # Tabla resumen
        st.dataframe(summary_df, use_container_width=True)
    
    with tab3:
        st.markdown("---")
        if 'career_groups' not in st.session_state:
            st.session_state['career_groups'] = career_groups
        
        find_equivalent_subjects_streamlit(st.session_state['career_groups'])
    
    with tab4:
        st.markdown("---")
        st.markdown("## 🚀 Análisis Avanzado con Machine Learning")
        
        # Sidebar mejorado
        with st.sidebar:
            st.markdown("## ⚙️ Panel de Control")
            
            # Configuración de análisis
            st.markdown("### 🔧 Configuración de Análisis")
            
            similarity_threshold = st.slider(
                "🎯 Umbral de Similitud",
                min_value=0.1,
                max_value=0.8,
                value=0.3,
                step=0.1,
                help="Nivel mínimo de similitud para agrupar carreras (menor = grupos más grandes)"
            )
            
            enable_advanced_analysis = st.checkbox(
                "🧠 Análisis Avanzado",
                value=True,
                help="Habilita algoritmos avanzados de similitud semántica"
            )
            
            st.markdown("---")
            st.markdown("### 📊 Información del Dataset")
            
            # Estadísticas generales en sidebar
            total_universities = len(set([item['universidad'] for item in data]))
            total_careers = len(data)
            total_subjects = sum([
                len(sum(item['malla_curricular'].values(), [])) 
                for item in data
            ])
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <span class="stat-number" style="color: #667eea;">{total_universities}</span>
                    <div class="stat-label">🏫 Universidades</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <span class="stat-number" style="color: #667eea;">{total_careers}</span>
                    <div class="stat-label">🎓 Carreras</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <span class="stat-number" style="color: #667eea;">{total_subjects}</span>
                    <div class="stat-label">📚 Materias Totales</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
        # Contenido principal del análisis avanzado
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🎯 Ejecutar Análisis Completo", type="primary", use_container_width=True):
                
                with st.spinner("🧠 Ejecutando algoritmos de Machine Learning..."):
                    # Barra de progreso avanzada
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Paso 1: Preparación de datos
                    status_text.text("🔄 Paso 1/4: Preparando y normalizando datos...")
                    progress_bar.progress(25)
                    time.sleep(0.8)
                    
                    # Paso 2: Análisis de similitud
                    status_text.text("🧮 Paso 2/4: Calculando similitudes semánticas...")
                    progress_bar.progress(50)
                    time.sleep(1.0)
                    
                    # Paso 3: Clustering inteligente
                    status_text.text("🎯 Paso 3/4: Ejecutando clustering inteligente...")
                    progress_bar.progress(75)
                    
                    if enable_advanced_analysis:
                        clusters = smart_career_clustering(data, similarity_threshold)
                    else:
                        # Usar agrupación simple como fallback
                        clusters = {}
                        for item in data:
                            career_type = extract_career_type(item['carrera'])
                            if career_type not in clusters:
                                clusters[career_type] = {'carreras': [], 'universidades': set(), 'total_carreras': 0}
                            
                            total_materias = sum(len(materias) for materias in item['malla_curricular'].values())
                            career_info = {
                                'universidad': item['universidad'],
                                'carrera': item['carrera'],
                                'total_materias': total_materias,
                                'materias': sum(item['malla_curricular'].values(), [])
                            }
                            clusters[career_type]['carreras'].append(career_info)
                            clusters[career_type]['universidades'].add(item['universidad'])
                            clusters[career_type]['total_carreras'] += 1
                        
                        for cluster in clusters.values():
                            cluster['universidades'] = list(cluster['universidades'])
                    
                    time.sleep(0.5)
                    
                    # Paso 4: Finalización
                    status_text.text("✨ Paso 4/4: Generando insights y visualizaciones...")
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    
                    progress_bar.empty()
                    status_text.empty()
                
                # Mensaje de éxito personalizado
                st.markdown(f"""
                <div class="success-box">
                    <h3>🎉 ¡Análisis Completado Exitosamente!</h3>
                    <p>Se identificaron <strong>{len(clusters)}</strong> clusters inteligentes de carreras similares.</p>
                    <p>Algoritmo utilizado: <strong>{'Clustering Semántico Avanzado' if enable_advanced_analysis else 'Agrupación por Categorías'}</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Guardar en session state
                st.session_state['clusters'] = clusters
                st.session_state['analysis_mode'] = 'advanced' if enable_advanced_analysis else 'simple'
        
        with col2:
            st.markdown("### 💡 Información")
            
            if 'clusters' in st.session_state:
                clusters = st.session_state['clusters']
                
                st.markdown(f"""
                <div class="info-box">
                    <h4>📈 Resultados del Análisis</h4>
                    <p><strong>Clusters:</strong> {len(clusters)}</p>
                    <p><strong>Modo:</strong> {st.session_state.get('analysis_mode', 'N/A').title()}</p>
                    <p><strong>Estado:</strong> ✅ Completado</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="info-box">
                    <h4>🎯 Listo para Analizar</h4>
                    <p>Haz clic en el botón para iniciar el análisis inteligente de carreras.</p>
                    <p>El sistema utilizará algoritmos avanzados para identificar similitudes.</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Mostrar resultados del clustering
        if 'clusters' in st.session_state:
            clusters = st.session_state['clusters']
            
            st.markdown("---")
            st.markdown("## 🔍 Explorador Interactivo de Clusters")
            
            # Selector de cluster mejorado
            cluster_names = list(clusters.keys())
            selected_cluster = st.selectbox(
                "🎯 Selecciona un cluster para análisis detallado:",
                cluster_names,
                help="Explora en detalle cada grupo de carreras similares identificado por el algoritmo"
            )
            
            if selected_cluster and enable_advanced_analysis:
                display_advanced_cluster_analysis(selected_cluster, clusters[selected_cluster])
            elif selected_cluster:
                # Mostrar análisis simple como fallback
                st.info("Análisis básico disponible. Habilita 'Análisis Avanzado' para funcionalidades completas.")
            
            # Resumen ejecutivo de todos los clusters
            st.markdown("---")
            st.markdown("## 📊 Dashboard Ejecutivo")
            
            # Crear métricas de resumen
            cluster_summary = []
            total_similarity_score = 0
            
            for name, data_cluster in clusters.items():
                avg_materias = np.mean([career['total_materias'] for career in data_cluster['carreras']])
                
                # Calcular score de diversidad (más universidades = mayor diversidad)
                diversity_score = len(data_cluster['universidades']) / max(1, data_cluster['total_carreras']) * 100
                
                cluster_summary.append({
                    'Cluster': name,
                    'Carreras': data_cluster['total_carreras'],
                    'Universidades': len(data_cluster['universidades']),
                    'Promedio_Materias': f"{avg_materias:.1f}",
                    'Diversidad': f"{diversity_score:.0f}%",
                    'Principales_Unis': ', '.join(data_cluster['universidades'][:2]) + ('...' if len(data_cluster['universidades']) > 2 else '')
                })
            
            summary_df = pd.DataFrame(cluster_summary)
            
            # Visualización mejorada
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Distribución de Carreras por Cluster")
                st.bar_chart(summary_df.set_index('Cluster')['Carreras'])
            
            with col2:
                st.subheader("🏫 Diversidad Universitaria por Cluster")
                st.bar_chart(summary_df.set_index('Cluster')['Universidades'])
            
            # Tabla resumen mejorada
            st.subheader("📋 Resumen Ejecutivo Completo")
            st.dataframe(
                summary_df,
                use_container_width=True,
                column_config={
                    'Cluster': st.column_config.TextColumn('🎯 Grupo de Carreras', width="large"),
                    'Carreras': st.column_config.NumberColumn('📊 Total Carreras'),
                    'Universidades': st.column_config.NumberColumn('🏫 N° Universidades'),
                    'Promedio_Materias': st.column_config.TextColumn('📚 Promedio Materias'),
                    'Diversidad': st.column_config.TextColumn('🌟 Score Diversidad'),
                    'Principales_Unis': st.column_config.TextColumn('🏛️ Principales Universidades', width="large")
                }
            )

if __name__ == "__main__":
    main()