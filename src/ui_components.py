"""
Componentes de UI para la aplicación Streamlit
"""
import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px

def display_header():
    """Muestra el encabezado de la aplicación"""
    st.title("🎓 Explorador de Carreras Universitarias")
    st.markdown("""
    Esta aplicación te permite explorar datos de universidades, carreras y mallas curriculares.
    """)

def display_university_selector(universities: List[str]) -> str:
    """
    Muestra un selector de universidades
    
    Args:
        universities: Lista de universidades disponibles
        
    Returns:
        La universidad seleccionada
    """
    return st.selectbox("Selecciona una Universidad", options=universities)

def display_career_selector(careers: List[Dict[str, Any]]) -> str:
    """
    Muestra un selector de carreras
    
    Args:
        careers: Lista de carreras disponibles
        
    Returns:
        La carrera seleccionada
    """
    career_names = [career.get('carrera', '') for career in careers]
    return st.selectbox("Selecciona una Carrera", options=career_names)

def display_curriculum(curriculum_data: Dict[str, Any]):
    """
    Muestra la información de una malla curricular
    
    Args:
        curriculum_data: Datos de la malla curricular
    """
    if not curriculum_data:
        st.warning("No se encontró información para esta carrera")
        return
    
    st.subheader(f"Malla Curricular: {curriculum_data.get('carrera', 'N/A')} - {curriculum_data.get('universidad', 'N/A')}")
    
    # Mostrar información adicional si existe
    if 'modalidad' in curriculum_data:
        st.write(f"**Modalidad:** {curriculum_data['modalidad']}")
    
    if 'duracion_ciclos' in curriculum_data:
        st.write(f"**Duración:** {curriculum_data['duracion_ciclos']} ciclos")
    
    if 'titulo' in curriculum_data:
        st.write(f"**Título:** {curriculum_data['titulo']}")
    
    # Mostrar la malla curricular por semestres
    st.write("### Materias por Semestre")
    
    if 'malla_curricular' not in curriculum_data:
        st.warning("No se encontró información de la malla curricular")
        return
    
    tabs = st.tabs([f"Semestre {sem}" for sem in curriculum_data['malla_curricular'].keys()])
    
    for i, (semester, subjects) in enumerate(curriculum_data['malla_curricular'].items()):
        with tabs[i]:
            if not subjects:
                st.write("No hay materias registradas para este semestre")
                continue
                
            # Verificar el formato de las materias
            if isinstance(subjects[0], str):
                # Si son strings simples
                for subject in subjects:
                    st.write(f"- {subject}")
            elif isinstance(subjects[0], dict):
                # Si son objetos con más información
                for subject in subjects:
                    if 'nombre' in subject:
                        subject_name = subject['nombre']
                        
                        # Crear un expander para mostrar detalles adicionales
                        with st.expander(subject_name):
                            for key, value in subject.items():
                                if key != 'nombre':
                                    st.write(f"**{key.capitalize()}:** {value}")
                    else:
                        st.write("- [Materia sin nombre]")

def display_recommended_curriculum(curriculum: Dict, nuevas_materias: Optional[List[str]] = None):
    """
    Muestra la malla curricular recomendada de manera estructurada
    
    Args:
        curriculum: Diccionario con la estructura de la malla recomendada
        nuevas_materias: Lista de nombres de materias nuevas agregadas (opcional)
    """
    if not curriculum:
        st.warning("No hay información de malla curricular recomendada disponible")
        return
        
    st.subheader("Malla Curricular Recomendada")
    
    # Obtener semestres y ordenarlos numéricamente
    semesters = list(curriculum.keys())
    semesters.sort(key=lambda x: int(x) if x.isdigit() else float('inf'))
    
    # Crear columnas para mostrar los semestres
    cols_per_row = 3
    
    for i in range(0, len(semesters), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j in range(cols_per_row):
            if i + j < len(semesters):
                semester = semesters[i + j]
                subjects = curriculum[semester]
                
                with cols[j]:
                    st.markdown(f"**Semestre {semester}**")
                    
                    if not subjects:
                        st.info("No hay materias para este semestre")
                        continue
                    
                    # Verificar si las materias son objetos o strings
                    if isinstance(subjects[0], dict):
                        for subject in subjects:
                            nombre_materia = subject.get('nombre', 'Sin nombre')
                            es_nueva = nuevas_materias and nombre_materia in nuevas_materias
                            color_style = "background-color: #d4f8e8; border-left: 4px solid #34c759;" if es_nueva else "background-color: #f8f9fa;"
                            with st.expander(nombre_materia):
                                st.markdown(f'<div style="{color_style} padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;">', unsafe_allow_html=True)
                                st.write(f"**Descripción:** {subject.get('descripcion', 'No disponible')}")
                                st.write(f"**Área:** {subject.get('area', 'No especificada')}")
                                st.write(f"**Tipo:** {subject.get('tipo', 'No especificado')}")
                                if 'creditos' in subject:
                                    st.write(f"**Créditos:** {subject.get('creditos', 0)}")
                                elif 'creditos_estimados' in subject:
                                    st.write(f"**Créditos estimados:** {subject.get('creditos_estimados', 0)}")
                                st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        # Si son strings, mostrarlos en una lista simple
                        for subject in subjects:
                            es_nueva = nuevas_materias and subject in nuevas_materias
                            if es_nueva:
                                st.markdown(f'<div style="background-color: #d4f8e8; border-left: 4px solid #34c759; padding: 0.2rem; border-radius: 3px; margin-bottom: 0.2rem;">- {subject}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f"- {subject}")

def display_university_stats(university_stats: Dict[str, Any]):
    """
    Muestra estadísticas generales sobre universidades
    
    Args:
        university_stats: Estadísticas a mostrar
    """
    st.subheader("📊 Estadísticas de Universidades y Carreras")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Universidades", university_stats.get('total_universities', 0))
    with col2:
        st.metric("Carreras", university_stats.get('total_careers', 0))
    with col3:
        st.metric("Materias Totales", university_stats.get('total_subjects', 0))
    
    # Gráfico de carreras por universidad
    st.subheader("Carreras por Universidad")
    careers_per_uni = university_stats.get('careers_per_university', {})
    if careers_per_uni:
        df_uni = pd.DataFrame({
            'Universidad': list(careers_per_uni.keys()),
            'Cantidad de Carreras': list(careers_per_uni.values())
        })
        fig = px.bar(df_uni, x='Universidad', y='Cantidad de Carreras',
                    title='Cantidad de Carreras por Universidad',
                    color='Cantidad de Carreras')
        st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar materias más comunes
    st.subheader("Materias más Comunes")
    common_subjects = university_stats.get('common_subjects', [])
    if common_subjects:
        top_n = min(10, len(common_subjects))
        df_common = pd.DataFrame(common_subjects[:top_n])
        fig = px.bar(df_common, x='subject', y='count',
                    title=f'Top {top_n} Materias más Comunes',
                    labels={'subject': 'Materia', 'count': 'Cantidad de Apariciones'})
        st.plotly_chart(fig, use_container_width=True)

def display_search_subjects():
    """
    Muestra un cuadro de búsqueda para materias
    
    Returns:
        El texto de búsqueda ingresado
    """
    st.subheader("🔍 Buscar Materias")
    return st.text_input("Ingresa palabras clave para buscar materias:")

def display_search_results(results: List[Dict[str, Any]]):
    """
    Muestra los resultados de búsqueda de materias
    
    Args:
        results: Resultados de la búsqueda
    """
    if not results:
        st.info("No se encontraron materias que coincidan con la búsqueda")
        return
    
    st.write(f"Se encontraron coincidencias en {len(results)} carreras:")
    
    for result in results:
        university = result.get('universidad', 'Universidad desconocida')
        career = result.get('carrera', 'Carrera desconocida')
        matches = result.get('materias_coincidentes', {})
        
        with st.expander(f"{university} - {career}"):
            for semester, subjects in matches.items():
                st.write(f"**Semestre {semester}:**")
                
                if isinstance(subjects[0], str):
                    for subject in subjects:
                        st.markdown(f"- *{subject}*")
                elif isinstance(subjects[0], dict):
                    for subject in subjects:
                        if 'nombre' in subject:
                            st.markdown(f"- *{subject['nombre']}*")
