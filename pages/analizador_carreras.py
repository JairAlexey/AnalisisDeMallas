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

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Carreras - Reformulador de Carreras Universitarias",
    page_icon="🔍",
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
    
    # Mostrar información de depuración en la consola
    print(f"Intentando conectar a MongoDB: {connector.db_name}/{connector.collection_name}")
    
    if connector.connect():
        print("Conexión a MongoDB exitosa en analizador_carreras.py")
        # Pasamos la configuración correcta al analizador
        analyzer = CurriculumAnalyzer(
            db_name=connector.db_name,
            collection_name=connector.collection_name
        )
        
        # Forzar la verificación del estado de conexión real
        if analyzer.check_status()["database_connected"]:
            return analyzer
        else:
            print("Conexión a MongoDB no disponible en el analizador")
    else:
        print("Error al conectar a MongoDB en analizador_carreras.py")
    
    # En caso de error, crear analizador con modo offline
    return CurriculumAnalyzer()

def main():
    # Encabezado
    st.title("🔍 Analizador de Carreras Universitarias")
    st.markdown("""
    Esta herramienta te permite analizar mallas curriculares de diferentes universidades
    y generar recomendaciones para la UDLA basadas en materias troncales identificadas.
    """)
    
    # Inicializar analizador
    analyzer = get_analyzer()
    
    # Verificar estado del analizador
    status = analyzer.check_status()
    if not status["database_connected"]:
        st.error("⚠️ No se pudo conectar a la base de datos MongoDB.")
        st.markdown("""
        <div class="error-box">
        <strong>Problemas de conexión a la base de datos:</strong><br>
        1. Asegúrate de que MongoDB está instalado y en ejecución<br>
        2. Ejecuta el script <code>python init_database.py</code> para inicializar la base de datos<br>
        3. Verifica que el archivo <code>data/universidades.json</code> existe y contiene datos válidos
        </div>
        """, unsafe_allow_html=True)
        
        # Añadir botón para diagnóstico
        if st.button("Ejecutar Diagnóstico"):
            import subprocess
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join(project_root, "diagnose_mongodb.py")],
                    capture_output=True,
                    text=True
                )
                st.code(result.stdout)
            except Exception as e:
                st.error(f"Error al ejecutar diagnóstico: {e}")
        
        if st.button("Reintentar conexión"):
            st.rerun()  # Usar st.rerun() en lugar de st.experimental_rerun()
        return
        
    # Obtener lista de carreras disponibles
    careers = analyzer.list_available_careers()
    
    # Modificación: Filtrar para mostrar solo carreras que tienen documento en UDLA
    udla_careers = analyzer.list_udla_careers()
    
    if not udla_careers:
        st.warning("No se encontraron carreras de UDLA en la base de datos")
        st.markdown("""
        <div class="info-box">
        <strong>No hay datos de carreras UDLA disponibles:</strong><br>
        1. Ejecuta el script <code>python init_database.py</code> para cargar los datos de universidades<br>
        2. Verifica que el archivo <code>data/universidades.json</code> contiene carreras de UDLA
        </div>
        """, unsafe_allow_html=True)
        
        # Agregar diagnóstico adicional
        st.subheader("Diagnóstico de Universidades")
        if st.button("Mostrar universidades disponibles"):
            with st.spinner("Consultando universidades..."):
                # Obtener universidades directamente de la colección
                try:
                    universities = analyzer.db[analyzer.collection_name].distinct("universidad")
                    if universities:
                        st.write("Universidades encontradas en la base de datos:")
                        for univ in sorted(universities):
                            count = analyzer.db[analyzer.collection_name].count_documents({"universidad": univ})
                            st.write(f"- {univ} ({count} carreras)")
                        
                        st.info("Si ves 'Universidad de Las Américas' o similar en lugar de 'UDLA', necesitas modificar el código para reconocer este nombre.")
                    else:
                        st.error("No se encontraron universidades en la base de datos")
                except Exception as e:
                    st.error(f"Error al consultar universidades: {e}")
        
        # Opción para usar todas las carreras como alternativa
        if st.button("Usar todas las carreras disponibles"):
            st.session_state.show_all_careers = True
            st.rerun()
            return
        
        if st.button("Verificar nuevamente"):
            if "show_all_careers" in st.session_state:
                del st.session_state.show_all_careers
            st.rerun()
        return
    
    # Crear dos secciones: análisis y resultados
    tab1, tab2, tab3 = st.tabs(["Realizar Análisis", "Ver Resultados Anteriores", "Diagnóstico"])
    
    with tab1:
        show_analysis_form(careers, analyzer)
    
    with tab2:
        show_previous_results()
        
    with tab3:
        show_diagnostics(analyzer, status)

def show_diagnostics(analyzer, status):
    """Muestra información de diagnóstico del sistema"""
    st.header("Diagnóstico del Sistema")
    
    # Estado general
    st.subheader("Estado general")
    cols = st.columns(3)
    with cols[0]:
        if status["database_connected"]:
            st.success("✅ Base de datos conectada")
        else:
            st.error("❌ Sin conexión a base de datos")
    
    with cols[1]:
        if status["model_loaded"]:
            st.success("✅ Modelo de ML cargado")
        else:
            st.error("❌ Error en modelo de ML")
            
    with cols[2]:
        if status["careers_count"] > 0:
            st.success(f"✅ {status['careers_count']} carreras disponibles")
        else:
            st.error("❌ No hay carreras disponibles")
    
    # Información detallada
    st.subheader("Información detallada")
    st.markdown(f"""
    - **Universidades disponibles:** {status['universities_count']}
    - **Carreras totales:** {status['careers_count']}
    - **Carreras UDLA:** {status['udla_careers_count']}
    """)
    
    # Ejecutar diagnóstico completo
    if st.button("Ejecutar diagnóstico completo"):
        with st.spinner("Ejecutando diagnóstico completo..."):
            try:
                # Importar pymongo y verificar conexión
                import pymongo
                from pymongo import MongoClient
                
                # Verificar conexión a MongoDB
                try:
                    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
                    client.admin.command('ping')
                    st.success("✅ Conexión a MongoDB establecida correctamente")
                    
                    # Verificar base de datos mallas_curriculares
                    db = client["mallas_curriculares"]
                    collection = db["universidades"]
                    count = collection.count_documents({})
                    st.success(f"✅ La colección 'universidades' contiene {count} documentos")
                    
                    # Mostrar universidades disponibles
                    universities = collection.distinct("universidad")
                    st.write(f"Universidades disponibles ({len(universities)}): {', '.join(sorted(universities))}")
                    
                except Exception as e:
                    st.error(f"❌ Error de conexión a MongoDB: {str(e)}")
                
                # Verificar modelo de embeddings
                try:
                    from utils.embedding_utils import get_embedding, get_embedding_model
                    model = get_embedding_model("paraphrase-multilingual-MiniLM-L12-v2")
                    if model:
                        st.success("✅ Modelo de embeddings cargado correctamente")
                        
                        # Probar embeddings con un texto simple
                        text = "Texto de prueba para embeddings"
                        embedding = get_embedding(text)
                        st.write(f"Dimensión del embedding: {len(embedding)}")
                    else:
                        st.error("❌ No se pudo cargar el modelo de embeddings")
                except Exception as e:
                    st.error(f"❌ Error al verificar modelo de embeddings: {str(e)}")
                
                # Verificar AgglomerativeClustering de sklearn
                try:
                    from sklearn.cluster import AgglomerativeClustering
                    st.success("✅ AgglomerativeClustering importado correctamente")
                except Exception as e:
                    st.error(f"❌ Error al importar AgglomerativeClustering: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ Error durante el diagnóstico: {str(e)}")
    
    # Botón para inicializar la base de datos
    st.subheader("Acciones de mantenimiento")
    if st.button("Inicializar base de datos"):
        with st.spinner("Inicializando base de datos..."):
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, str(Path(project_root) / "init_database.py")],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    st.success("✅ Base de datos inicializada correctamente")
                    st.code(result.stdout)
                else:
                    st.error("❌ Error al inicializar la base de datos")
                    st.code(result.stderr)
            except Exception as e:
                st.error(f"❌ Error al ejecutar script de inicialización: {str(e)}")

def show_analysis_form(careers, analyzer):
    """Muestra el formulario para realizar un nuevo análisis"""
    st.header("Nuevo Análisis")
    
    # Decidir si mostrar todas las carreras o solo las de UDLA
    if st.session_state.get("show_all_careers", False):
        all_careers = analyzer.list_available_careers()
        career = st.selectbox(
            "Selecciona una carrera para analizar (ADVERTENCIA: solo carreras de UDLA tienen análisis completo):", 
            all_careers
        )
        st.warning("⚠️ Has seleccionado mostrar todas las carreras. Solo las carreras de UDLA tendrán análisis completo.")
    else:
        # Usar solo las carreras de UDLA
        udla_careers = analyzer.list_udla_careers()
        career = st.selectbox("Selecciona una carrera para analizar:", udla_careers)
    
    # Configuración avanzada
    with st.expander("Configuración avanzada"):
        similarity = st.slider(
            "Umbral de similitud para materias equivalentes:",
            min_value=0.5, max_value=0.9, value=0.7, step=0.05,
            help="Un valor más alto requiere mayor similitud entre materias para considerarlas equivalentes"
        )
        
        core_threshold = st.slider(
            "Umbral para identificar materias troncales:",
            min_value=0.4, max_value=0.9, value=0.7, step=0.05,
            help="Porcentaje de universidades en las que debe aparecer una materia para considerarla troncal"
        )
        
        model_options = [
            "paraphrase-multilingual-MiniLM-L12-v2",
            "all-MiniLM-L6-v2",
            "distiluse-base-multilingual-cased-v1"
        ]
        model_name = st.selectbox(
            "Modelo de embeddings:",
            model_options,
            help="Modelo para calcular similitud semántica entre materias"
        )
    
    # Botón para iniciar análisis
    if st.button("Iniciar Análisis", type="primary"):
        # Crear placeholder para mensajes de progreso
        progress_placeholder = st.empty()
        
        # Iniciar spinner
        progress_placeholder.info("Preparando análisis...")
        time.sleep(1)
        
        # Actualizar configuración del analizador
        analyzer.similarity_threshold = similarity
        analyzer.core_threshold = core_threshold
        analyzer.model_name = model_name
        
        try:
            # Actualizar mensaje de progreso
            progress_placeholder.info(f"Analizando la carrera '{career}'... (Extrayendo documentos)")
            time.sleep(1)
            
            # Realizar análisis
            result = analyzer.analyze_career(career)
            
            if "error" in result:
                progress_placeholder.empty()
                st.error(result["error"])
            else:
                # Actualizar mensaje de progreso
                progress_placeholder.info("Guardando resultados del análisis...")
                time.sleep(1)
                
                # Guardar resultado
                file_path = analyzer.save_analysis_result(result)
                
                # Limpiar mensaje de progreso
                progress_placeholder.empty()
                
                # Mostrar resultado
                show_analysis_result(result)
                
                # Mensaje de éxito
                st.success(f"Análisis completado exitosamente. Resultados guardados en {file_path}")
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"Error durante el análisis: {e}")

def show_previous_results():
    """Muestra resultados de análisis previos"""
    st.header("Resultados Anteriores")
    
    # Buscar archivos de análisis
    output_dir = Path("output")
    if not output_dir.exists():
        st.info("No hay análisis previos disponibles")
        return
    
    analysis_files = list(output_dir.glob("analisis_*.json"))
    
    if not analysis_files:
        st.info("No hay análisis previos disponibles")
        return
    
    # Ordenar archivos por fecha de modificación (más recientes primero)
    analysis_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Crear selector de archivo
    file_names = [file.name for file in analysis_files]
    selected_file = st.selectbox("Selecciona un análisis previo:", file_names)
    
    # Cargar archivo seleccionado
    file_path = output_dir / selected_file
    
    if st.button("Cargar Análisis"):
        with st.spinner("Cargando análisis..."):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                show_analysis_result(result)
                
                # Opción para descargar
                with open(file_path, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="Descargar análisis (JSON)",
                        data=f,
                        file_name=selected_file,
                        mime="application/json"
                    )
            except Exception as e:
                st.error(f"Error al cargar el análisis: {e}")

def show_analysis_result(result):
    """Muestra el resultado del análisis"""
    st.subheader(f"Análisis de la carrera: {result['carrera_objetivo']}")
    
    # Información general
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Información General")
    st.write(f"**Universidades analizadas:** {', '.join(result['universidades_analizadas'])}")
    st.write(f"**Total de universidades:** {len(result['universidades_analizadas'])}")
    st.write(f"**Malla base UDLA:** {result['udla_base']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Materias troncales
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Materias Troncales Identificadas")
    
    materias_fuertes = result['analisis']['materias_fuertes']
    
    # Crear dos columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Materias ya presentes en UDLA")
        presentes = [m for m in materias_fuertes if m['presente_en_udla']]
        if presentes:
            for materia in presentes:
                st.markdown(f"""
                <div class="highlight">
                    <strong>{materia['nombre_general']}</strong><br>
                    <small>Equivalentes: {', '.join(materia['materias_equivalentes'][:3])}</small><br>
                    <small>Frecuencia: {int(materia['frecuencia']*100)}% de las universidades</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No se encontraron materias troncales ya presentes en UDLA")
    
    with col2:
        st.markdown("#### Materias a agregar")
        faltantes = [m for m in materias_fuertes if not m['presente_en_udla']]
        if faltantes:
            for materia in faltantes:
                st.markdown(f"""
                <div class="highlight">
                    <strong>{materia['nombre_general']}</strong><br>
                    <small>Equivalentes: {', '.join(materia['materias_equivalentes'][:3])}</small><br>
                    <small>Frecuencia: {int(materia['frecuencia']*100)}% de las universidades</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("¡La malla de UDLA ya incluye todas las materias troncales!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Malla recomendada
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Malla Curricular Recomendada")
    
    # Usar la nueva función para mostrar la malla recomendada
    from src.ui_components import display_recommended_curriculum
    # Obtener materias nuevas agregadas a la malla (faltantes)
    materias_fuertes = result['analisis']['materias_fuertes']
    nuevas_materias = [m['nombre_general'] for m in materias_fuertes if not m['presente_en_udla']]
    display_recommended_curriculum(result["malla_recomendada_udla"], nuevas_materias=nuevas_materias)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()