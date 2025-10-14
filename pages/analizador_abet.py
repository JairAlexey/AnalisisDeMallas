import streamlit as st
import sys
import os
import json
import time
from pathlib import Path

# Añadir el directorio del proyecto al path para importar módulos locales
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar módulos propios
from src.curriculum_analyzer import CurriculumAnalyzer
from mongodb_connector import MongoDBConnector
from utils.abet_utils import load_abet_criteria, map_career_to_abet_category

# Configuración de la página
st.set_page_config(
    page_title="Análisis ABET - Reformulador de Carreras Universitarias",
    page_icon="🎯",
    layout="wide"
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
    .highlight {
        background-color: #eef2ff;
        padding: 0.5rem;
        border-radius: 3px;
        border-left: 3px solid #667eea;
    }
    .error-box {
        background-color: #ffe5e5;
        padding: 1rem;
        border-radius: 5px;
        border-left: 3px solid #ff4d4d;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e5f3ff;
        padding: 1rem;
        border-radius: 5px;
        border-left: 3px solid #4da6ff;
        margin-bottom: 1rem;
    }
    .abet-criteria-box {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 5px;
        border-left: 3px solid #0066cc;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar analizador
@st.cache_resource
def get_analyzer():
    # Usamos MongoDBConnector con la configuración correcta de base de datos
    connector = MongoDBConnector()
    # Asegurar que usamos los mismos nombres de BD y colección que en app.py
    connector.db_name = "carreras_universitarias"
    connector.collection_name = "mallas_curriculares"
    
    # Obtener ruta al archivo de criterios ABET
    abet_criteria_path = os.path.join(project_root, 'data', 'criterios_abet.json')
    
    if connector.connect():
        # Pasamos la configuración correcta al analizador
        analyzer = CurriculumAnalyzer(
            db_name=connector.db_name,
            collection_name=connector.collection_name,
            abet_criteria_path=abet_criteria_path
        )
        
        # Forzar la verificación del estado de conexión real
        if analyzer.check_status()["database_connected"]:
            return analyzer
        else:
            print("Conexión a MongoDB no disponible en el analizador")
    else:
        print("Error al conectar a MongoDB en analizador_abet.py")
    
    # En caso de error, crear analizador con modo offline
    return CurriculumAnalyzer(abet_criteria_path=abet_criteria_path)

def load_abet_criteria_file():
    """Carga los criterios ABET desde el archivo"""
    try:
        abet_path = os.path.join(project_root, 'data', 'criterios_abet.json')
        return load_abet_criteria(abet_path)
    except Exception as e:
        st.error(f"Error al cargar criterios ABET: {e}")
        return None

def main():
    # Encabezado
    st.title("🎯 Análisis de Criterios ABET")
    st.markdown("""
    Esta herramienta permite evaluar las mallas curriculares de las carreras de ingeniería
    según los criterios establecidos por ABET (Accreditation Board for Engineering and Technology).
    """)
    
    # Inicializar analizador
    analyzer = get_analyzer()
    
    # Verificar estado del analizador
    status = analyzer.check_status()
    if not status["database_connected"]:
        st.error("⚠️ No se pudo conectar a la base de datos MongoDB.")
        st.warning("El análisis ABET requiere acceso a la base de datos. Por favor, verifica la conexión.")
        return
    
    if not status.get("abet_criteria_loaded", False):
        st.error("⚠️ No se pudieron cargar los criterios ABET.")
        st.warning("El archivo de criterios ABET no se pudo cargar correctamente.")
        return
    
    # Cargar criterios ABET para visualización
    abet_criteria = load_abet_criteria_file()
    if not abet_criteria:
        st.error("⚠️ No se pudieron cargar los criterios ABET para visualización.")
        return
    
    # Crear pestañas para diferentes funciones
    tab1, tab2, tab3 = st.tabs([
        "Análisis ABET de Carrera", 
        "Explorar Criterios ABET",
        "Resultados Anteriores"
    ])
    
    with tab1:
        show_abet_analysis_form(analyzer)
        
    with tab2:
        show_abet_criteria(abet_criteria)
        
    with tab3:
        show_previous_abet_evaluations(analyzer)

def show_abet_analysis_form(analyzer):
    """Muestra el formulario para realizar un análisis ABET de una carrera"""
    st.header("Análisis ABET de Carrera")
    
    # Obtener universidades disponibles
    with st.spinner("Cargando universidades..."):
        if analyzer.connector and analyzer.db is not None:
            universities = analyzer.connector.get_universities()
        else:
            universities = []
    
    if not universities:
        st.warning("No se pudieron obtener las universidades desde la base de datos")
        return
    
    # Selector de universidad
    university = st.selectbox("Selecciona una universidad:", universities)
    
    # Obtener carreras de la universidad seleccionada
    with st.spinner(f"Cargando carreras de {university}..."):
        if analyzer.connector and analyzer.db is not None:
            careers_data = analyzer.connector.get_careers_by_university(university)
            careers = [career.get('carrera', '') for career in careers_data if career.get('carrera', '')]
        else:
            careers = []
    
    if not careers:
        st.warning(f"No se encontraron carreras para {university}")
        return
    
    # Selector de carrera
    career = st.selectbox("Selecciona una carrera para analizar:", careers)
    
    # Botón para iniciar análisis ABET
    if st.button("Iniciar Análisis ABET", type="primary"):
        with st.spinner(f"Analizando criterios ABET para {career} de {university}..."):
            try:
                # Realizar análisis ABET
                result = analyzer.analyze_abet_compliance(university, career)
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    # Mostrar resultados
                    show_abet_analysis_result(result)
                    
                    # Opción para descargar resultados
                    st.download_button(
                        label="Descargar resultados ABET (JSON)",
                        data=json.dumps(result, indent=2, ensure_ascii=False),
                        file_name=f"abet_{university.replace(' ', '_')}_{career.replace(' ', '_')}.json",
                        mime="application/json"
                    )
            
            except Exception as e:
                st.error(f"Error durante el análisis ABET: {e}")

def show_abet_criteria(abet_criteria):
    """Muestra los criterios ABET disponibles"""
    st.header("Explorar Criterios ABET")
    
    if not abet_criteria or 'criterios_abet' not in abet_criteria:
        st.error("No se pudieron cargar los criterios ABET")
        return
    
    # Información general sobre ABET
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown(f"### ABET - {abet_criteria['criterios_abet'].get('version', '')}")
    st.markdown(abet_criteria['criterios_abet'].get('descripcion_general', ''))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar criterios generales
    st.subheader("Criterios Generales")
    criterios_generales = abet_criteria['criterios_abet'].get('criterios_generales', {})
    
    if not criterios_generales:
        st.warning("No hay información sobre criterios generales")
    else:
        for criterio_id, criterio_data in criterios_generales.items():
            with st.expander(criterio_data.get('titulo', criterio_id)):
                st.markdown(f"**{criterio_data.get('titulo', '')}**")
                st.markdown(criterio_data.get('descripcion', ''))
                
                # Mostrar subcriterios si existen
                if 'subcriterios' in criterio_data:
                    st.markdown("##### Subcriterios:")
                    for subcrit_id, subcrit_desc in criterio_data['subcriterios'].items():
                        st.markdown(f"- **{subcrit_id}:** {subcrit_desc}")
                
                # Mostrar componentes requeridos si existen
                if 'componentes_requeridos' in criterio_data:
                    st.markdown("##### Componentes Requeridos:")
                    for comp_name, comp_desc in criterio_data['componentes_requeridos'].items():
                        st.markdown(f"- **{comp_name}:** {comp_desc}")
    
    # Mostrar criterios específicos
    st.subheader("Criterios Específicos por Tipo de Ingeniería")
    criterios_especificos = abet_criteria['criterios_abet'].get('criterios_especificos', {})
    
    if not criterios_especificos:
        st.warning("No hay información sobre criterios específicos")
    else:
        for tipo_id, tipo_data in criterios_especificos.items():
            with st.expander(tipo_data.get('titulo', tipo_id)):
                st.markdown(f"**{tipo_data.get('titulo', '')}**")
                st.markdown(tipo_data.get('descripcion', ''))
                
                # Mostrar requisitos
                if 'requisitos' in tipo_data:
                    st.markdown("##### Requisitos:")
                    for req in tipo_data['requisitos']:
                        st.markdown(f"- {req}")

def show_previous_abet_evaluations(analyzer):
    """Muestra evaluaciones ABET previas guardadas en la base de datos"""
    st.header("Evaluaciones ABET Anteriores")
    
    if not analyzer.connector or analyzer.db is None:
        st.warning("No hay conexión a la base de datos para obtener evaluaciones anteriores")
        return
    
    # Obtener universidades disponibles
    with st.spinner("Cargando universidades..."):
        universities = analyzer.connector.get_universities()
    
    if not universities:
        st.warning("No se pudieron obtener las universidades desde la base de datos")
        return
    
    # Selector de universidad
    university = st.selectbox(
        "Selecciona una universidad:", 
        universities,
        key="university_selector_previous"
    )
    
    # Obtener carreras de la universidad seleccionada
    with st.spinner(f"Buscando carreras evaluadas de {university}..."):
        try:
            # Buscar documentos que tengan evaluación ABET
            collection = analyzer.db[analyzer.collection_name]
            pipeline = [
                {"$match": {
                    "universidad": university,
                    "evaluacion_abet": {"$exists": True}
                }},
                {"$project": {"carrera": 1}}
            ]
            
            careers_with_abet = list(collection.aggregate(pipeline))
            careers = [doc.get('carrera', '') for doc in careers_with_abet if doc.get('carrera', '')]
            
        except Exception as e:
            st.error(f"Error al buscar evaluaciones ABET: {e}")
            careers = []
    
    if not careers:
        st.info(f"No se encontraron evaluaciones ABET para carreras de {university}")
        return
    
    # Selector de carrera
    career = st.selectbox(
        "Selecciona una carrera:", 
        careers,
        key="career_selector_previous"
    )
    
    # Botón para cargar evaluación
    if st.button("Cargar Evaluación ABET"):
        with st.spinner(f"Cargando evaluación ABET para {career}..."):
            try:
                # Obtener evaluación ABET
                abet_evaluation = analyzer.connector.get_abet_evaluation(university, career)
                
                if abet_evaluation:
                    # Mostrar resultados
                    show_abet_analysis_result(abet_evaluation)
                    
                    # Opción para descargar resultados
                    st.download_button(
                        label="Descargar evaluación ABET (JSON)",
                        data=json.dumps(abet_evaluation, indent=2, ensure_ascii=False),
                        file_name=f"abet_{university.replace(' ', '_')}_{career.replace(' ', '_')}.json",
                        mime="application/json"
                    )
                else:
                    st.warning(f"No se encontró evaluación ABET para {career} de {university}")
            
            except Exception as e:
                st.error(f"Error al cargar evaluación ABET: {e}")

def show_abet_analysis_result(result):
    """Muestra el resultado del análisis ABET"""
    st.subheader(f"Análisis ABET para: {result.get('carrera', 'Carrera')}")
    
    # Información general
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Información General")
    st.write(f"**Universidad:** {result.get('universidad', 'No especificada')}")
    st.write(f"**Carrera:** {result.get('carrera', 'No especificada')}")
    
    # Tipo de ingeniería ABET
    if 'evaluacion_abet' in result and 'tipo_abet' in result['evaluacion_abet']:
        tipo_abet = result['evaluacion_abet']['tipo_abet']
        st.write(f"**Tipo de ingeniería ABET:** {tipo_abet}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar evaluación ABET general
    if 'evaluacion_abet' in result:
        evaluacion = result['evaluacion_abet']
        
        st.markdown('<div class="abet-criteria-box">', unsafe_allow_html=True)
        st.markdown("### Evaluación de Criterios ABET")
        
        # Mostrar cumplimiento de criterios generales
        if 'cumplimiento_general' in evaluacion:
            st.markdown("#### Cumplimiento de Criterios Generales")
            
            cumplimiento = evaluacion['cumplimiento_general']
            for criterio, datos in cumplimiento.items():
                status_icon = "✅" if datos.get('cumple', False) else "⚠️"
                st.markdown(f"**{status_icon} {criterio}:** {datos.get('observaciones', '')}")
        
        # Mostrar cumplimiento de criterios específicos
        if 'cumplimiento_especifico' in evaluacion:
            st.markdown("#### Cumplimiento de Criterios Específicos")
            
            if 'requisitos' in evaluacion['cumplimiento_especifico']:
                for req in evaluacion['cumplimiento_especifico']['requisitos']:
                    st.markdown(f"- {req}")
            else:
                st.info("No hay información detallada sobre criterios específicos")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar recomendaciones ABET
    if 'recomendaciones_abet' in result:
        recomendaciones = result['recomendaciones_abet']
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Recomendaciones ABET")
        
        # Información general
        st.markdown(f"**Tipo de ingeniería:** {recomendaciones.get('criterios_aplicables', 'No especificado')}")
        st.markdown(recomendaciones.get('descripcion', ''))
        
        # Mostrar cumplimiento estimado
        if 'cumplimiento_estimado' in recomendaciones:
            st.markdown("#### Cumplimiento Estimado")
            
            cumplimiento = recomendaciones['cumplimiento_estimado']
            
            # Crear dos columnas para visualización
            col1, col2 = st.columns(2)
            
            # Mostrar matemáticas y ciencias
            if 'matematicas_ciencias' in cumplimiento:
                mat_ciencias = cumplimiento['matematicas_ciencias']
                with col1:
                    st.metric(
                        "Matemáticas y Ciencias", 
                        f"{mat_ciencias.get('porcentaje', 0):.1f}%", 
                        delta="Suficiente" if mat_ciencias.get('evaluacion') == 'Suficiente' else "Insuficiente",
                        delta_color="normal" if mat_ciencias.get('evaluacion') == 'Suficiente' else "inverse"
                    )
                    st.caption(mat_ciencias.get('recomendacion', ''))
            
            # Mostrar ingeniería y diseño
            if 'ingenieria_diseno' in cumplimiento:
                ing_diseno = cumplimiento['ingenieria_diseno']
                with col2:
                    st.metric(
                        "Ingeniería y Diseño", 
                        f"{ing_diseno.get('porcentaje', 0):.1f}%", 
                        delta="Suficiente" if ing_diseno.get('evaluacion') == 'Suficiente' else "Insuficiente",
                        delta_color="normal" if ing_diseno.get('evaluacion') == 'Suficiente' else "inverse"
                    )
                    st.caption(ing_diseno.get('recomendacion', ''))
        
        # Mostrar áreas de refuerzo
        if 'areas_refuerzo' in recomendaciones and recomendaciones['areas_refuerzo']:
            st.markdown("#### Áreas de Refuerzo")
            
            for area in recomendaciones['areas_refuerzo']:
                requisito = area.get('requisito', '')
                cumplimiento = area.get('cumplimiento', 'No evaluado')
                sugerencia = area.get('sugerencia', '')
                
                # Aplicar estilo según nivel de cumplimiento
                if cumplimiento == 'Completo':
                    st.success(f"**{requisito}**  \n{sugerencia}")
                elif cumplimiento == 'Parcial':
                    st.warning(f"**{requisito}**  \n{sugerencia}")
                else:
                    st.error(f"**{requisito}**  \n{sugerencia}")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()