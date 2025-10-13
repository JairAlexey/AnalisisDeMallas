import streamlit as st
import sys
import os
from pathlib import Path

# Añadir el directorio del proyecto al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos propios
from src.data_service import UniversityDataService
from src.ui_components import (
    display_header, display_university_selector, display_career_selector,
    display_curriculum, display_university_stats
)

# Configuración de la página
st.set_page_config(
    page_title="Reformulador de Carreras Universitarias",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4a4a4a;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        color: #667eea;
        margin-bottom: 1rem;
    }
    .card {
        border-radius: 5px;
        padding: 1.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .nav-item {
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin-bottom: 0.5rem;
        background-color: #f8f9fa;
        cursor: pointer;
    }
    .nav-item:hover {
        background-color: #e9ecef;
    }
    .nav-item-active {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar servicio de datos
@st.cache_resource
def get_data_service():
    service = UniversityDataService()
    service.connect()
    return service

def main():
    # Mostrar encabezado
    display_header()
    
    # Inicializar servicio de datos
    data_service = get_data_service()
    
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    page = st.sidebar.radio(
        "Selecciona una página", 
        ["Resumen General", "Explorar Universidad y Carrera", "Analizador de Carreras"]
    )
    
    # Mostrar la página seleccionada
    if page == "Resumen General":
        show_general_summary(data_service)
    elif page == "Explorar Universidad y Carrera":
        show_university_explorer(data_service)
    elif page == "Analizador de Carreras":
        show_analyzer_redirect()
    
    # Footer
    st.markdown("---")
    st.caption("Desarrollado para UDLA - Universidad de Las Américas | 2023")

def show_general_summary(data_service):
    with st.spinner("Cargando estadísticas..."):
        stats = data_service.get_subject_statistics()
        display_university_stats(stats)

def show_university_explorer(data_service):
    """Muestra el explorador de universidades y carreras"""
    st.subheader("🔍 Explorador de Universidades y Carreras")
    
    # Obtener lista de universidades
    with st.spinner("Cargando universidades..."):
        universities = data_service.get_universities()
    
    if not universities:
        st.error("No se encontraron universidades en la base de datos")
        return
    
    # Selector de universidad
    university = display_university_selector(universities)
    
    # Obtener carreras de la universidad seleccionada
    with st.spinner(f"Cargando carreras de {university}..."):
        careers = data_service.get_careers_by_university(university)
    
    if not careers:
        st.warning(f"No se encontraron carreras para {university}")
        return
    
    # Selector de carrera
    career = display_career_selector(careers)
    
    # Mostrar malla curricular
    with st.spinner(f"Cargando malla curricular de {career}..."):
        curriculum = data_service.get_curriculum(university, career)
        display_curriculum(curriculum)

def show_analyzer_redirect():
    """Muestra un enlace para redirigir al analizador de carreras"""
    st.subheader("🔍 Analizador de Carreras")
    
    st.markdown("""
    <div class="card">
        <h3>Reformulación Curricular Inteligente</h3>
        <p>El Analizador de Carreras te permite:</p>
        <ul>
            <li>Comparar mallas curriculares de diferentes universidades</li>
            <li>Identificar materias troncales o fundamentales en cada carrera</li>
            <li>Recibir recomendaciones para mejorar las mallas curriculares de la UDLA</li>
            <li>Generar propuestas automáticas de mallas optimizadas</li>
        </ul>
        <p>Accede a la herramienta completa usando el siguiente enlace:</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Ir al Analizador de Carreras", type="primary"):
        st.switch_page("pages/analizador_carreras.py")

if __name__ == "__main__":
    main()
