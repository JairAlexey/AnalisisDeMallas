import os
import json
from typing import Dict, List, Any, Optional, Union
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MongoDBConnector:
    """
    Clase para gestionar la conexión y operaciones con MongoDB
    """
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        # Configuración MongoDB
        self.host = os.getenv("MONGODB_HOST", "localhost")
        self.port = int(os.getenv("MONGODB_PORT", "27017"))
        self.db_name = os.getenv("MONGODB_DB", "carreras_universitarias")
        self.collection_name = os.getenv("MONGODB_COLLECTION", "mallas_curriculares")
        self.use_auth = os.getenv("MONGODB_USE_AUTH", "false").lower() == "true"
        
        # Inicializar como None
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self) -> bool:
        """
        Establece conexión con MongoDB
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Construir string de conexión
            if self.use_auth:
                username = os.getenv("MONGODB_USERNAME")
                password = os.getenv("MONGODB_PASSWORD")
                connection_string = f"mongodb://{username}:{password}@{self.host}:{self.port}/"
            else:
                connection_string = f"mongodb://{self.host}:{self.port}/"
            
            # Conectar a MongoDB
            self.client = MongoClient(connection_string)
            
            # Verificar la conexión
            self.client.admin.command('ping')
            
            # Seleccionar base de datos y colección
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            logging.info(f"Conexión exitosa a MongoDB en {self.host}:{self.port}")
            logging.info(f"Base de datos: {self.db_name}, Colección: {self.collection_name}")
            
            return True
        
        except Exception as e:
            logging.error(f"Error al conectar con MongoDB: {e}")
            return False
    
    def close(self) -> None:
        """Cierra la conexión con MongoDB"""
        if self.client:
            self.client.close()
            logging.info("Conexión a MongoDB cerrada")
    
    def get_collection(self) -> Optional[Collection]:
        """Retorna la colección actual o None si no hay conexión"""
        return self.collection
    
    def get_database(self) -> Optional[Database]:
        """Retorna la base de datos actual o None si no hay conexión"""
        return self.db
    
    # Métodos para operaciones CRUD
    
    def find_one(self, query: Dict = None) -> Optional[Dict]:
        """
        Busca un documento en la colección
        
        Args:
            query: Diccionario con criterios de búsqueda
            
        Returns:
            Diccionario con el documento encontrado o None
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return None
        
        try:
            return self.collection.find_one(query or {})
        except Exception as e:
            logging.error(f"Error al buscar documento: {e}")
            return None
    
    def find_many(self, 
                  query: Dict = None, 
                  projection: Dict = None, 
                  limit: int = 0, 
                  sort: List = None) -> List[Dict]:
        """
        Busca múltiples documentos en la colección
        
        Args:
            query: Diccionario con criterios de búsqueda
            projection: Campos a incluir/excluir
            limit: Límite de resultados (0 = sin límite)
            sort: Lista de tuplas (campo, dirección) para ordenar
            
        Returns:
            Lista de documentos
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return []
        
        try:
            cursor = self.collection.find(query or {}, projection or {})
            
            if limit > 0:
                cursor = cursor.limit(limit)
            
            if sort:
                cursor = cursor.sort(sort)
            
            return list(cursor)
        except Exception as e:
            logging.error(f"Error al buscar documentos: {e}")
            return []
    
    def insert_one(self, document: Dict) -> Optional[str]:
        """
        Inserta un documento en la colección
        
        Args:
            document: Diccionario con el documento a insertar
            
        Returns:
            ID del documento insertado o None si hay error
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return None
        
        try:
            result = self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error al insertar documento: {e}")
            return None
    
    def update_one(self, query: Dict, update: Dict) -> bool:
        """
        Actualiza un documento en la colección
        
        Args:
            query: Diccionario con criterios de búsqueda
            update: Diccionario con los cambios a realizar
            
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return False
        
        try:
            result = self.collection.update_one(query, update)
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error al actualizar documento: {e}")
            return False
    
    def delete_one(self, query: Dict) -> bool:
        """
        Elimina un documento de la colección
        
        Args:
            query: Diccionario con criterios de búsqueda
            
        Returns:
            True si la eliminación fue exitosa, False en caso contrario
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return False
        
        try:
            result = self.collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error al eliminar documento: {e}")
            return False
    
    # Métodos específicos para la colección de carreras universitarias
    
    def get_universities(self) -> List[str]:
        """
        Obtiene la lista de universidades disponibles
        
        Returns:
            Lista de nombres de universidades
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return []
        
        try:
            return sorted(self.collection.distinct("universidad"))
        except Exception as e:
            logging.error(f"Error al obtener universidades: {e}")
            return []
    
    def get_careers_by_university(self, university: str) -> List[Dict]:
        """
        Obtiene las carreras de una universidad específica
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Lista de documentos de carreras
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return []
        
        try:
            return list(self.collection.find(
                {"universidad": university},
                {"carrera": 1, "duracion_ciclos": 1, "modalidad": 1, "titulo": 1}
            ))
        except Exception as e:
            logging.error(f"Error al obtener carreras por universidad: {e}")
            return []
    
    def get_curriculum_by_university_career(self, university: str, career: str) -> Optional[Dict]:
        """
        Obtiene la malla curricular de una carrera específica
        
        Args:
            university: Nombre de la universidad
            career: Nombre de la carrera
            
        Returns:
            Documento completo con la malla curricular
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return None
        
        try:
            return self.collection.find_one({
                "universidad": university,
                "carrera": career
            })
        except Exception as e:
            logging.error(f"Error al obtener malla curricular: {e}")
            return None
    
    def search_careers(self, keyword: str) -> List[Dict]:
        """
        Busca carreras que contengan la palabra clave
        
        Args:
            keyword: Palabra clave a buscar
            
        Returns:
            Lista de documentos de carreras
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return []
        
        try:
            return list(self.collection.find(
                {"carrera": {"$regex": keyword, "$options": "i"}},
                {"universidad": 1, "carrera": 1, "duracion_ciclos": 1}
            ))
        except Exception as e:
            logging.error(f"Error al buscar carreras: {e}")
            return []
    
    def search_subjects(self, keyword: str) -> List[Dict]:
        """
        Busca materias que contengan la palabra clave
        
        Args:
            keyword: Palabra clave a buscar
            
        Returns:
            Lista de documentos de carreras con las materias que coinciden
        """
        if self.collection is None:
            logging.error("No hay conexión a MongoDB")
            return []
        
        try:
            # En MongoDB 4.4+ podría hacerse con agregación más eficiente
            # Esta es una versión más compatible con versiones anteriores
            results = []
            
            # Primero obtenemos todas las carreras
            all_careers = self.collection.find({})
            
            for career in all_careers:
                matching_semesters = {}
                
                # Por cada semestre, buscamos materias que coincidan
                for semester, subjects in career.get("malla_curricular", {}).items():
                    # Si las materias son strings simples
                    if isinstance(subjects, list) and all(isinstance(s, str) for s in subjects):
                        matching_subjects = [s for s in subjects if keyword.lower() in s.lower()]
                        if matching_subjects:
                            matching_semesters[semester] = matching_subjects
                    
                    # Si las materias son objetos con propiedad "nombre"
                    elif isinstance(subjects, list) and all(isinstance(s, dict) for s in subjects):
                        matching_subjects = [s for s in subjects if keyword.lower() in s.get("nombre", "").lower()]
                        if matching_subjects:
                            matching_semesters[semester] = matching_subjects
                
                if matching_semesters:
                    results.append({
                        "universidad": career.get("universidad"),
                        "carrera": career.get("carrera"),
                        "materias_coincidentes": matching_semesters
                    })
            
            return results
        
        except Exception as e:
            logging.error(f"Error al buscar materias: {e}")
            return []

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del conector
    mongo = MongoDBConnector()
    
    # Conectar a MongoDB
    if mongo.connect():
        try:
            # Obtener lista de universidades
            universities = mongo.get_universities()
            print(f"Universidades disponibles ({len(universities)}):")
            for uni in universities:
                print(f"- {uni}")
            
            # Mostrar ejemplo de consulta
            if universities:
                sample_uni = universities[0]
                careers = mongo.get_careers_by_university(sample_uni)
                print(f"\nCarreras de {sample_uni} ({len(careers)}):")
                for career in careers[:5]:  # Mostrar solo las primeras 5
                    print(f"- {career.get('carrera')}")
                
                if careers:
                    sample_career = careers[0].get('carrera')
                    print(f"\nConsulta de ejemplo: Buscando materias con 'Cálculo'...")
                    results = mongo.search_subjects("Cálculo")
                    print(f"Se encontraron coincidencias en {len(results)} carreras")
            
        finally:
            # Cerrar conexión
            mongo.close()
    else:
        print("No se pudo establecer conexión con MongoDB")
