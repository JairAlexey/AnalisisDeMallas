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
    page = st.sidebar.radio("Selecciona una página", 
                           ["Resumen General", "Explorar Universidad y Carrera"])
    
    # Mostrar la página seleccionada
    if page == "Resumen General":
        show_general_summary(data_service)
    else:
        show_university_explorer(data_service)
    
    # Footer
    st.markdown("---")
    st.caption("Desarrollado para UDLA - Universidad de Las Américas | 2023")

def show_general_summary(data_service):
    """Muestra el resumen general de universidades y carreras"""
    st.subheader("📊 Resumen General")
    
    with st.spinner("Cargando estadísticas..."):
        stats = data_service.get_subject_statistics()
        display_university_stats(stats)
    
    # Explicación del explorador
    st.subheader("📋 Cómo usar el explorador")
    st.markdown("""
    Para explorar en detalle las carreras y sus mallas curriculares:
    1. Navega a la sección "Explorar Universidad y Carrera" desde el menú lateral
    2. Selecciona una universidad de la lista
    3. Elige una carrera de esa universidad
    4. Explora la malla curricular por semestres
    
    Para buscar materias específicas:
    - Usa la página "Explorador de Materias" desde el menú lateral
    """)

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

if __name__ == "__main__":
    main()
