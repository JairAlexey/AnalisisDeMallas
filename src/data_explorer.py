import streamlit as st
import pandas as pd
import numpy as np
from src.career_reformulator import CareerReformulator
import json
import os

def create_sample_analysis():
    """
    Crea un análisis de muestra para demostración
    """
    # Cargar datos
    reformulator = CareerReformulator()
    
    if not os.path.exists('data/universidades.json'):
        st.error("No se encuentra el archivo de datos 'data/universidades.json'")
        return None
    
    data = reformulator.load_data('data/universidades.json')
    
    # Ejecutar clustering
    clusters = reformulator.cluster_careers(n_clusters=8)
    
    return reformulator, clusters

def display_basic_stats(data):
    """
    Muestra estadísticas básicas del dataset
    """
    if not data:
        return
    
    # Calcular estadísticas
    universities = set([item['universidad'] for item in data])
    careers = [item['carrera'] for item in data]
    total_subjects = []
    
    for item in data:
        subjects_count = sum(len(subjects) for subjects in item['malla_curricular'].values())
        total_subjects.append(subjects_count)
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏫 Universidades", len(universities))
    
    with col2:
        st.metric("🎓 Carreras Totales", len(careers))
    
    with col3:
        st.metric("📚 Promedio Materias", f"{np.mean(total_subjects):.1f}")
    
    with col4:
        st.metric("📊 Rango Materias", f"{min(total_subjects)}-{max(total_subjects)}")
    
    # Lista de universidades
    st.subheader("🏫 Universidades en el Dataset")
    universities_df = pd.DataFrame({
        'Universidad': sorted(list(universities))
    })
    st.dataframe(universities_df, use_container_width=True)
    
    return universities, careers, total_subjects

def show_career_distribution(data):
    """
    Muestra la distribución de carreras por universidad
    """
    if not data:
        return
    
    # Contar carreras por universidad
    career_counts = {}
    for item in data:
        uni = item['universidad']
        career_counts[uni] = career_counts.get(uni, 0) + 1
    
    # Crear DataFrame para visualización
    dist_df = pd.DataFrame(
        list(career_counts.items()),
        columns=['Universidad', 'Número de Carreras']
    ).sort_values('Número de Carreras', ascending=False)
    
    st.subheader("📊 Distribución de Carreras por Universidad")
    st.bar_chart(dist_df.set_index('Universidad')['Número de Carreras'])
    st.dataframe(dist_df, use_container_width=True)

def explore_subjects(data):
    """
    Explora las materias más comunes en el dataset
    """
    if not data:
        return
    
    # Recopilar todas las materias
    all_subjects = []
    for item in data:
        for semester, subjects in item['malla_curricular'].items():
            all_subjects.extend(subjects)
    
    # Contar frecuencias
    from collections import Counter
    subject_counts = Counter(all_subjects)
    
    # Mostrar las más comunes
    st.subheader("📚 Materias Más Comunes (Top 20)")
    common_subjects = subject_counts.most_common(20)
    
    subjects_df = pd.DataFrame(common_subjects, columns=['Materia', 'Frecuencia'])
    st.bar_chart(subjects_df.set_index('Materia')['Frecuencia'])
    st.dataframe(subjects_df, use_container_width=True)

def simple_career_grouping(data):
    """
    Agrupación simple de carreras por palabras clave
    """
    if not data:
        return {}
    
    # Definir grupos basados en palabras clave
    groups = {
        'Ingeniería de Software/Sistemas': ['software', 'sistemas', 'informática', 'computación'],
        'Ingeniería Civil': ['civil'],
        'Ingeniería Industrial': ['industrial', 'producción'],
        'Ingeniería Electrónica': ['electrónica', 'automatización', 'telecomunicaciones'],
        'Ingeniería Ambiental': ['ambiental'],
        'Ingeniería de Alimentos': ['alimentos'],
        'Ingeniería Mecánica/Automotriz': ['mecánica', 'automotriz'],
        'Biotecnología/Bioingeniería': ['biotecnología', 'bioingeniería', 'biotecnología'],
        'Ingeniería Química': ['química'],
        'Otras Ingenierías': []
    }
    
    # Clasificar carreras
    classified_careers = {group: [] for group in groups.keys()}
    
    for item in data:
        career_name = item['carrera'].lower()
        classified = False
        
        for group, keywords in groups.items():
            if group == 'Otras Ingenierías':
                continue
            
            for keyword in keywords:
                if keyword in career_name:
                    classified_careers[group].append({
                        'universidad': item['universidad'],
                        'carrera': item['carrera'],
                        'total_materias': sum(len(subjects) for subjects in item['malla_curricular'].values())
                    })
                    classified = True
                    break
            
            if classified:
                break
        
        if not classified:
            classified_careers['Otras Ingenierías'].append({
                'universidad': item['universidad'],
                'carrera': item['carrera'],
                'total_materias': sum(len(subjects) for subjects in item['malla_curricular'].values())
            })
    
    return classified_careers

def main():
    st.set_page_config(
        page_title="Análisis Exploratorio - Carreras Universitarias",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Análisis Exploratorio de Carreras Universitarias")
    st.markdown("---")
    
    # Cargar datos
    try:
        with open('data/universidades.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        st.success(f"✅ Datos cargados exitosamente: {len(data)} carreras encontradas")
        
        # Tabs para diferentes análisis
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Estadísticas Generales",
            "🎓 Distribución de Carreras", 
            "📚 Análisis de Materias",
            "🔗 Agrupación Simple"
        ])
        
        with tab1:
            st.header("📊 Estadísticas Generales del Dataset")
            display_basic_stats(data)
        
        with tab2:
            st.header("🎓 Distribución de Carreras")
            show_career_distribution(data)
        
        with tab3:
            st.header("📚 Análisis de Materias")
            explore_subjects(data)
        
        with tab4:
            st.header("🔗 Agrupación Simple de Carreras")
            st.info("Esta es una agrupación básica por palabras clave. Para análisis más avanzado, usa la aplicación principal.")
            
            grouped_careers = simple_career_grouping(data)
            
            for group_name, careers in grouped_careers.items():
                if careers:  # Solo mostrar grupos con carreras
                    with st.expander(f"{group_name} ({len(careers)} carreras)", expanded=False):
                        careers_df = pd.DataFrame(careers)
                        st.dataframe(careers_df, use_container_width=True)
                        
                        # Mostrar universidades únicas en este grupo
                        unique_unis = careers_df['universidad'].unique()
                        st.write(f"**Universidades:** {', '.join(unique_unis)}")
    
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo 'data/universidades.json'")
        st.info("Asegúrate de que el archivo existe en la carpeta 'data'")
    
    except Exception as e:
        st.error(f"❌ Error al procesar los datos: {str(e)}")

if __name__ == "__main__":
    main()