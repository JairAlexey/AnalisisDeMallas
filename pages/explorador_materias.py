import streamlit as st
import sys
import os
from pathlib import Path

# Añadir el directorio del proyecto al path para importar módulos locales
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar módulos propios
from src.data_service import UniversityDataService
from src.ui_components import display_search_subjects, display_search_results

# Configuración de la página
st.set_page_config(
    page_title="Explorador de Materias - Carreras Universitarias",
    page_icon="🔍",
    layout="wide"
)

# Inicializar servicio de datos
@st.cache_resource
def get_data_service():
    service = UniversityDataService()
    service.connect()
    return service

def main():
    # Encabezado
    st.title("🔍 Explorador de Materias")
    st.markdown("""
    Busca materias específicas en las mallas curriculares de todas las universidades.
    Puedes encontrar dónde se imparten materias similares entre distintas carreras.
    """)
    
    # Inicializar servicio de datos
    data_service = get_data_service()
    
    # Opciones de búsqueda
    search_type = st.radio(
        "Tipo de búsqueda",
        ["Por palabra clave", "Estadísticas de materias"]
    )
    
    if search_type == "Por palabra clave":
        # Búsqueda por palabra clave
        search_term = display_search_subjects()
        
        if search_term:
            with st.spinner(f"Buscando materias con '{search_term}'..."):
                results = data_service.search_subjects(search_term)
                display_search_results(results)
    else:
        # Estadísticas de materias
        with st.spinner("Generando estadísticas de materias..."):
            show_subject_statistics(data_service)

def show_subject_statistics(data_service):
    """Muestra estadísticas detalladas sobre las materias"""
    st.subheader("📊 Estadísticas de Materias")
    
    # Obtener estadísticas
    stats = data_service.get_subject_statistics()
    
    # Mostrar materias más comunes
    st.write("### Materias más comunes entre universidades")
    common_subjects = stats.get('common_subjects', [])
    
    if common_subjects:
        # Crear tabla para mostrar materias comunes
        data = []
        for item in common_subjects[:20]:  # Mostrar solo las 20 más comunes
            data.append({
                "Materia": item['subject'],
                "Apariciones": item['count']
            })
        
        st.dataframe(data, use_container_width=True)
        
        # Opción para descargar la lista completa
        import pandas as pd
        full_df = pd.DataFrame(common_subjects)
        
        st.download_button(
            label="Descargar lista completa",
            data=full_df.to_csv(index=False).encode('utf-8'),
            file_name="materias_comunes.csv",
            mime="text/csv"
        )
    else:
        st.info("No se encontraron materias comunes")

if __name__ == "__main__":
    main()
