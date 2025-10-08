"""
Servicio de datos para obtener información de universidades y carreras desde MongoDB
"""
from typing import List, Dict, Any, Optional
import logging
from mongodb_connector import MongoDBConnector

class UniversityDataService:
    """
    Clase para proveer servicios de datos relacionados con universidades y carreras
    """
    def __init__(self):
        self.db_connector = MongoDBConnector()
        self.is_connected = False
        
    def connect(self) -> bool:
        """Establece conexión con la base de datos"""
        self.is_connected = self.db_connector.connect()
        return self.is_connected
    
    def close(self):
        """Cierra la conexión con la base de datos"""
        if self.is_connected:
            self.db_connector.close()
            self.is_connected = False
    
    def get_universities(self) -> List[str]:
        """Obtiene la lista de todas las universidades disponibles"""
        if not self.is_connected and not self.connect():
            logging.error("No se pudo conectar a la base de datos")
            return []
        
        return self.db_connector.get_universities()
    
    def get_careers_by_university(self, university: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las carreras de una universidad específica
        
        Args:
            university: Nombre de la universidad
            
        Returns:
            Lista de diccionarios con información de las carreras
        """
        if not self.is_connected and not self.connect():
            logging.error("No se pudo conectar a la base de datos")
            return []
            
        return self.db_connector.get_careers_by_university(university)
    
    def get_curriculum(self, university: str, career: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la malla curricular de una carrera específica
        
        Args:
            university: Nombre de la universidad
            career: Nombre de la carrera
            
        Returns:
            Diccionario con la malla curricular o None si no se encuentra
        """
        if not self.is_connected and not self.connect():
            logging.error("No se pudo conectar a la base de datos")
            return None
            
        return self.db_connector.get_curriculum_by_university_career(university, career)
    
    def search_subjects(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Busca materias que contengan una palabra clave
        
        Args:
            keyword: Palabra clave a buscar en los nombres de las materias
            
        Returns:
            Lista de resultados con las materias que coinciden
        """
        if not self.is_connected and not self.connect():
            logging.error("No se pudo conectar a la base de datos")
            return []
            
        return self.db_connector.search_subjects(keyword)
    
    def get_all_subjects(self) -> Dict[str, List[str]]:
        """
        Obtiene todas las materias agrupadas por universidad y carrera
        
        Returns:
            Diccionario con materias agrupadas por universidad y carrera
        """
        if not self.is_connected and not self.connect():
            logging.error("No se pudo conectar a la base de datos")
            return {}
        
        result = {}
        universities = self.get_universities()
        
        for university in universities:
            result[university] = {}
            careers = self.get_careers_by_university(university)
            
            for career_data in careers:
                career = career_data.get('carrera', '')
                if not career:
                    continue
                    
                curriculum = self.get_curriculum(university, career)
                if not curriculum or 'malla_curricular' not in curriculum:
                    continue
                    
                subjects = []
                for semester, semester_subjects in curriculum['malla_curricular'].items():
                    # Las materias pueden ser strings o diccionarios con propiedad 'nombre'
                    if all(isinstance(s, str) for s in semester_subjects):
                        subjects.extend(semester_subjects)
                    elif all(isinstance(s, dict) for s in semester_subjects):
                        subjects.extend([s.get('nombre', '') for s in semester_subjects if 'nombre' in s])
                
                result[university][career] = subjects
        
        return result

    def get_subject_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre las materias en la base de datos
        
        Returns:
            Diccionario con estadísticas sobre materias
        """
        if not self.is_connected and not self.connect():
            logging.error("No se pudo conectar a la base de datos")
            return {}
            
        universities = self.get_universities()
        stats = {
            'total_universities': len(universities),
            'total_careers': 0,
            'total_subjects': 0,
            'subjects_per_university': {},
            'careers_per_university': {},
            'subjects_per_career': {},
            'common_subjects': []
        }
        
        # Obtener todas las materias
        all_subjects = {}
        subject_count = {}
        
        for university in universities:
            careers = self.get_careers_by_university(university)
            stats['subjects_per_university'][university] = 0
            stats['careers_per_university'][university] = len(careers)
            
            for career_data in careers:
                career = career_data.get('carrera', '')
                if not career:
                    continue
                    
                stats['total_careers'] += 1
                curriculum = self.get_curriculum(university, career)
                if not curriculum or 'malla_curricular' not in curriculum:
                    continue
                
                career_subjects = 0
                for semester, semester_subjects in curriculum['malla_curricular'].items():
                    # Las materias pueden ser strings o diccionarios con propiedad 'nombre'
                    if all(isinstance(s, str) for s in semester_subjects):
                        subjects = semester_subjects
                    elif all(isinstance(s, dict) for s in semester_subjects):
                        subjects = [s.get('nombre', '') for s in semester_subjects if 'nombre' in s]
                    else:
                        subjects = []
                    
                    career_subjects += len(subjects)
                    
                    # Contar ocurrencias de cada materia
                    for subject in subjects:
                        if subject:
                            if subject not in subject_count:
                                subject_count[subject] = 0
                            subject_count[subject] += 1
                
                stats['subjects_per_career'][f"{university} - {career}"] = career_subjects
                stats['subjects_per_university'][university] += career_subjects
                stats['total_subjects'] += career_subjects
        
        # Encontrar materias comunes (que aparecen en al menos 3 carreras)
        common_threshold = 3
        stats['common_subjects'] = [
            {'subject': subject, 'count': count}
            for subject, count in subject_count.items()
            if count >= common_threshold
        ]
        stats['common_subjects'].sort(key=lambda x: x['count'], reverse=True)
        
        return stats
