"""
Clase principal para análisis de mallas curriculares
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import traceback
from pathlib import Path

from utils.text_processing import normalize_text
from utils.embedding_utils import get_embedding, batch_embed_documents
from utils.curriculum_analysis import (
    group_similar_subjects, 
    identify_core_subjects, 
    compare_curricula, 
    generate_recommendations
)
from utils.data_utils import flatten_curriculum
from utils.abet_utils import (
    load_abet_criteria,
    evaluate_curriculum_against_abet,
    generate_abet_recommendations
)
from mongodb_connector import MongoDBConnector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CurriculumAnalyzer:
    """Clase para análisis y reformulación de mallas curriculares"""
    
    def __init__(self, 
                connection_string: Optional[str] = None,
                db_name: str = "carreras_universitarias",
                collection_name: str = "mallas_curriculares",
                model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                similarity_threshold: float = 0.8,
                core_threshold: float = 0.7,
                abet_criteria_path: str = None):
        """
        Inicializa el analizador de mallas curriculares.
        
        Args:
            connection_string: String de conexión a MongoDB
            db_name: Nombre de la base de datos
            collection_name: Nombre de la colección
            model_name: Nombre del modelo de embeddings
            similarity_threshold: Umbral de similitud para materias equivalentes
            core_threshold: Umbral para identificar materias troncales
            abet_criteria_path: Ruta al archivo JSON con criterios ABET
        """
        try:
            # Usar MongoDBConnector en lugar de connect_to_mongodb
            self.connector = MongoDBConnector()
            # Asignar explícitamente los valores de base de datos y colección
            self.connector.db_name = db_name
            self.connector.collection_name = collection_name
            
            if self.connector.connect():
                self.db = self.connector.get_database()
                logger.info(f"Conexión a MongoDB establecida exitosamente. Base de datos: {db_name}, Colección: {collection_name}")
            else:
                self.db = None
                logger.error(f"No se pudo conectar a MongoDB con db_name={db_name}, collection_name={collection_name}")
                
            self.collection_name = collection_name
            self.model_name = model_name
            self.similarity_threshold = similarity_threshold
            self.core_threshold = core_threshold
            
            # Cargar criterios ABET
            self.abet_criteria = load_abet_criteria(abet_criteria_path)
            if not self.abet_criteria:
                logger.warning("No se pudieron cargar los criterios ABET correctamente")
            else:
                logger.info("Criterios ABET cargados correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar CurriculumAnalyzer: {e}")
            logger.error(traceback.format_exc())
            # Crear un objeto db vacío para evitar errores de NoneType
            self.db = None
            print(f"Error de conexión a MongoDB: {e}")
    
    def get_career_documents(self, career_name: str) -> List[Dict]:
        """
        Obtiene documentos de carreras desde MongoDB.
        
        Args:
            career_name: Nombre de la carrera a buscar
            
        Returns:
            Lista de documentos encontrados
        """
        if self.db is None:
            logger.error("No hay conexión a la base de datos MongoDB")
            return []
            
        try:
            # Crear expresión regular para búsqueda insensible a mayúsculas/minúsculas
            import re
            regex = re.compile(f".*{re.escape(career_name)}.*", re.IGNORECASE)
            
            # Realizar consulta
            collection = self.db[self.collection_name]
            cursor = collection.find({"carrera": {"$regex": regex}})
            
            # Convertir cursor a lista
            return list(cursor)
        except Exception as e:
            logger.error(f"Error al obtener documentos de carreras: {e}")
            return []

    def get_udla_curriculum(self, career_name: str) -> Dict:
        """
        Obtiene el documento de malla curricular de la UDLA para una carrera específica.
        
        Args:
            career_name: Nombre de la carrera
            
        Returns:
            Documento de la malla curricular o None si no se encuentra
        """
        if self.db is None:
            logger.error("No hay conexión a la base de datos MongoDB")
            return None
            
        try:
            # Crear expresión regular para búsqueda insensible a mayúsculas/minúsculas
            import re
            regex = re.compile(f".*{re.escape(career_name)}.*", re.IGNORECASE)
            
            # Realizar consulta (con el nombre completo de la universidad)
            collection = self.db[self.collection_name]
            return collection.find_one({
                "universidad": "Universidad de las Américas (UDLA)",  # Nombre correcto de la universidad
                "carrera": {"$regex": regex}
            })
        except Exception as e:
            logger.error(f"Error al obtener malla curricular de UDLA: {e}")
            return None

    def analyze_career(self, career_name: str) -> Dict:
        """
        Analiza una carrera y genera recomendaciones para la UDLA.
        
        Args:
            career_name: Nombre de la carrera a analizar
            
        Returns:
            Resultados del análisis y recomendaciones
        """
        if self.db is None:
            return {"error": "No hay conexión a la base de datos MongoDB"}
        
        logger.info(f"Iniciando análisis para la carrera: {career_name}")
        print(f"Iniciando análisis para la carrera: {career_name}")
        
        try:
            # Paso 1: Obtener documentos de la carrera
            career_docs = self.get_career_documents(career_name)
            logger.info(f"Encontrados {len(career_docs)} documentos para la carrera")
            print(f"Encontrados {len(career_docs)} documentos para la carrera")
            
            if not career_docs:
                return {"error": f"No se encontraron documentos para la carrera '{career_name}'"}
            
            # Paso 2: Obtener el documento de la UDLA
            udla_doc = self.get_udla_curriculum(career_name)
            
            if not udla_doc:
                return {"error": f"No se encontró documento de la UDLA para la carrera '{career_name}'"}
            
            # Paso 3: Extraer todas las materias
            all_subjects = []
            for doc in career_docs:
                subjects = flatten_curriculum(doc)
                all_subjects.extend(subjects)
            
            print(f"Total de materias extraídas: {len(all_subjects)}")
            
            # Paso 4: Agrupar materias similares
            subject_groups = group_similar_subjects(
                all_subjects,
                self.similarity_threshold,
                self.model_name
            )
            
            logger.info(f"Se identificaron {len(subject_groups)} grupos de materias similares")
            print(f"Se identificaron {len(subject_groups)} grupos de materias similares")
            
            # Paso 5: Identificar universidades analizadas
            universities = list(set([doc["universidad"] for doc in career_docs]))
            
            # Paso 6: Identificar materias troncales
            core_subjects = identify_core_subjects(
                subject_groups,
                universities,
                self.core_threshold
            )
            
            logger.info(f"Se identificaron {len(core_subjects)} materias troncales")
            print(f"Se identificaron {len(core_subjects)} materias troncales")
            
            # Paso 7: Comparar con la malla de la UDLA
            udla_subjects = flatten_curriculum(udla_doc)
            
            comparison = compare_curricula(
                core_subjects,
                udla_subjects,
                self.similarity_threshold,
                self.model_name
            )
            
            logger.info(f"Materias existentes en UDLA: {len(comparison['materias_existentes'])}")
            logger.info(f"Materias recomendadas a agregar: {len(comparison['materias_a_agregar'])}")
            print(f"Materias existentes en UDLA: {len(comparison['materias_existentes'])}")
            print(f"Materias recomendadas a agregar: {len(comparison['materias_a_agregar'])}")
            
            # Paso 8: Generar recomendaciones con detección de duplicados mejorada
            recommended_curriculum = generate_recommendations(
                comparison,
                udla_doc,
                core_subjects,
                similarity_threshold=90  # Usar un umbral alto para ser más estrictos con los duplicados
            )
            
            # Paso 9: Análisis ABET si los criterios están disponibles
            abet_recommendations = {}
            if self.abet_criteria:
                try:
                    abet_recommendations = generate_abet_recommendations(
                        udla_doc,
                        self.abet_criteria,
                        core_subjects
                    )
                    logger.info("Análisis ABET completado exitosamente")
                except Exception as e:
                    logger.error(f"Error durante análisis ABET: {e}")
                    abet_recommendations = {"error": str(e)}
            
            # Paso 10: Preparar resultados
            result = {
                "carrera_objetivo": career_name,
                "universidades_analizadas": universities,
                "udla_base": udla_doc["carrera"],
                "analisis": {
                    "materias_fuertes": [
                        {
                            "nombre_general": subject["nombre_general"],
                            "materias_equivalentes": subject["materias_equivalentes"][:5],
                            "frecuencia": subject["frecuencia_relativa"],
                            "area_predominante": subject["area_predominante"],
                            "tipo_predominante": subject["tipo_predominante"],
                            "presente_en_udla": any(
                                m["materia_troncal"] == subject["nombre_general"]
                                for m in comparison["materias_existentes"]
                            )
                        }
                        for subject in core_subjects
                    ],
                    "recomendaciones_udla": {
                        "materias_existentes": [m["materia_udla"] for m in comparison["materias_existentes"]],
                        "materias_a_agregar": [m["nombre_recomendado"] for m in comparison["materias_a_agregar"]]
                    }
                },
                "malla_recomendada_udla": recommended_curriculum,
                "analisis_abet": abet_recommendations
            }
            
            # Guardar análisis ABET en MongoDB para referencia futura
            if self.abet_criteria and not "error" in abet_recommendations:
                try:
                    self.connector.save_abet_evaluation(
                        "Universidad de las Américas (UDLA)", 
                        udla_doc["carrera"], 
                        abet_recommendations
                    )
                except Exception as e:
                    logger.error(f"Error al guardar evaluación ABET en MongoDB: {e}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error durante el análisis de la carrera {career_name}: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Error durante el análisis: {str(e)}"}

    def save_analysis_result(self, result: Dict, output_dir: str = "output") -> str:
        """
        Guarda el resultado del análisis en un archivo JSON.
        
        Args:
            result: Resultado del análisis
            output_dir: Directorio de salida
            
        Returns:
            Ruta al archivo guardado
        """
        try:
            # Crear directorio si no existe
            os.makedirs(output_dir, exist_ok=True)
            
            # Generar nombre de archivo
            if "error" in result:
                filename = f"error_analisis_{result.get('carrera_objetivo', 'desconocido')}.json"
            else:
                career_name = result["carrera_objetivo"].replace(" ", "_").lower()
                filename = f"analisis_{career_name}_{len(result['universidades_analizadas'])}_universidades.json"
            
            file_path = os.path.join(output_dir, filename)
            
            # Guardar archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Resultado guardado en {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Error al guardar el resultado: {e}")
            return "Error al guardar el resultado"
    
    def list_available_careers(self) -> List[str]:
        """
        Lista las carreras disponibles para análisis.
        
        Returns:
            Lista de nombres de carreras
        """
        if self.db is None:
            logger.error("No hay conexión a la base de datos")
            return []
            
        try:
            collection = self.db[self.collection_name]
            careers = collection.distinct("carrera")
            return sorted(careers)
        except Exception as e:
            logger.error(f"Error al listar carreras disponibles: {e}")
            return []

    def list_udla_careers(self) -> List[str]:
        """
        Lista las carreras disponibles de UDLA para análisis.
        
        Returns:
            Lista de nombres de carreras que tienen documento en UDLA
        """
        if self.db is None:
            logger.error("No hay conexión a la base de datos")
            return []
            
        try:
            collection = self.db[self.collection_name]
            
            # Usar el nombre correcto de UDLA en la base de datos
            udla_careers = collection.distinct("carrera", {"universidad": "Universidad de las Américas (UDLA)"})
            
            # Log para depuración
            logger.info(f"Se encontraron {len(udla_careers)} carreras de UDLA")
            print(f"Se encontraron {len(udla_careers)} carreras de UDLA")
            
            return sorted(udla_careers)
        except Exception as e:
            logger.error(f"Error al listar carreras de UDLA disponibles: {e}")
            return []

    def analyze_abet_compliance(self, university: str, career_name: str) -> Dict[str, Any]:
        """
        Analiza el cumplimiento de una carrera con los criterios ABET.
        
        Args:
            university: Nombre de la universidad
            career_name: Nombre de la carrera
            
        Returns:
            Resultados de la evaluación ABET
        """
        if self.db is None:
            return {"error": "No hay conexión a la base de datos MongoDB"}
        
        if not self.abet_criteria:
            return {"error": "No se han cargado los criterios ABET"}
        
        logger.info(f"Iniciando análisis ABET para la carrera: {career_name} de {university}")
        print(f"Iniciando análisis ABET para la carrera: {career_name} de {university}")
        
        try:
            # Paso 1: Obtener el documento de la carrera
            curriculum = self.connector.get_curriculum_by_university_career(university, career_name)
            
            if not curriculum:
                return {"error": f"No se encontró la carrera '{career_name}' en {university}"}
            
            # Paso 2: Realizar evaluación contra criterios ABET
            abet_evaluation = evaluate_curriculum_against_abet(curriculum, self.abet_criteria)
            
            # Paso 3: Analizar la carrera para obtener materias troncales y enriquecer evaluación
            career_docs = self.get_career_documents(career_name)
            all_subjects = []
            for doc in career_docs:
                subjects = flatten_curriculum(doc)
                all_subjects.extend(subjects)
                
            # Agrupar materias similares
            subject_groups = group_similar_subjects(
                all_subjects,
                self.similarity_threshold,
                self.model_name
            )
            
            # Identificar universidades analizadas
            universities = list(set([doc["universidad"] for doc in career_docs]))
            
            # Identificar materias troncales
            core_subjects = identify_core_subjects(
                subject_groups,
                universities,
                self.core_threshold
            )
            
            # Paso 4: Generar recomendaciones ABET basadas en análisis
            abet_recommendations = generate_abet_recommendations(
                curriculum, 
                self.abet_criteria,
                core_subjects
            )
            
            # Combinar evaluación y recomendaciones
            result = {
                "carrera": career_name,
                "universidad": university,
                "evaluacion_abet": abet_evaluation,
                "recomendaciones_abet": abet_recommendations
            }
            
            # Paso 5: Guardar resultados en MongoDB
            self.connector.save_abet_evaluation(university, career_name, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error durante el análisis ABET de la carrera {career_name}: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Error durante el análisis ABET: {str(e)}"}
    
    def check_status(self) -> Dict:
        """
        Verifica el estado del analizador y de la conexión a la base de datos.
        
        Returns:
            Diccionario con información de estado
        """
        status = {
            "database_connected": False,
            "model_loaded": False,
            "universities_count": 0,
            "careers_count": 0,
            "udla_careers_count": 0,
            "abet_criteria_loaded": self.abet_criteria is not None and len(self.abet_criteria) > 0
        }
        
        # Verificar conexión a la base de datos
        try:
            if self.db is not None:  # Usar comparación explícita con None
                # Prueba rápida para verificar que la conexión está realmente activa
                collection = self.db[self.collection_name]
                # Hacer una consulta simple para verificar la conexión real
                count = collection.count_documents({}, limit=1)
                
                status["database_connected"] = True
                
                # Contar universidades y carreras
                status["universities_count"] = len(collection.distinct("universidad"))
                status["careers_count"] = collection.count_documents({})
                # Actualizar para usar el nombre correcto de UDLA
                status["udla_careers_count"] = collection.count_documents({"universidad": "Universidad de las Américas (UDLA)"})
                
                print(f"Estado de la base de datos: Conectada con {status['careers_count']} carreras")
        except Exception as e:
            print(f"Error al verificar estado de la base de datos: {e}")
            status["database_connected"] = False
        
        # Verificar modelo
        try:
            from utils.embedding_utils import get_embedding_model
            model = get_embedding_model(self.model_name)
            status["model_loaded"] = model is not None
        except Exception as e:
            print(f"Error al cargar modelo: {e}")
            status["model_loaded"] = False
        
        return status