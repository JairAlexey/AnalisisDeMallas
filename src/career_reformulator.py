import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from fuzzywuzzy import fuzz, process
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
import re
import pickle
import os

class CareerReformulator:
    def __init__(self):
        """
        Inicializa el reformulador de carreras con modelos de ML
        """
        self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        self.stemmer = SnowballStemmer('spanish')
        self.career_clusters = {}
        self.subject_clusters = {}
        self.data = None
        
        # Descargar recursos de NLTK si no existen
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            
        self.spanish_stopwords = set(stopwords.words('spanish'))
    
    def load_data(self, json_path):
        """
        Carga los datos del JSON de universidades
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        return self.data
    
    def preprocess_text(self, text):
        """
        Preprocesa texto para análisis de ML
        """
        if not text:
            return ""
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover caracteres especiales y números
        text = re.sub(r'[^a-záéíóúñ\s]', '', text)
        
        # Tokenizar
        tokens = word_tokenize(text)
        
        # Remover stopwords y aplicar stemming
        tokens = [self.stemmer.stem(token) for token in tokens 
                 if token not in self.spanish_stopwords and len(token) > 2]
        
        return ' '.join(tokens)
    
    def extract_career_features(self):
        """
        Extrae características de las carreras para clustering
        """
        careers_data = []
        
        for item in self.data:
            career_name = item['carrera']
            university = item['universidad']
            subjects = []
            
            # Recopilar todas las materias de la carrera
            for semester, subject_list in item['malla_curricular'].items():
                subjects.extend(subject_list)
            
            careers_data.append({
                'universidad': university,
                'carrera': career_name,
                'carrera_procesada': self.preprocess_text(career_name),
                'materias': subjects,
                'materias_procesadas': ' '.join([self.preprocess_text(s) for s in subjects]),
                'total_materias': len(subjects)
            })
        
        return pd.DataFrame(careers_data)
    
    def cluster_careers(self, n_clusters=None):
        """
        Agrupa carreras similares usando técnicas de ML
        """
        df_careers = self.extract_career_features()
        
        # Combinar nombre de carrera y materias para el análisis
        combined_features = df_careers['carrera_procesada'] + ' ' + df_careers['materias_procesadas']
        
        # Usar sentence transformers para obtener embeddings semánticos
        career_embeddings = self.sentence_model.encode(df_careers['carrera'].tolist())
        subject_embeddings = self.sentence_model.encode(combined_features.tolist())
        
        # Combinar embeddings
        combined_embeddings = np.concatenate([career_embeddings, subject_embeddings], axis=1)
        
        # Determinar número óptimo de clusters si no se especifica
        if n_clusters is None:
            # Usar el método del codo o estimar basado en variedad de carreras
            unique_career_types = len(set([self.extract_career_type(name) for name in df_careers['carrera']]))
            n_clusters = min(max(unique_career_types // 2, 3), 15)
        
        # Aplicar K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(combined_embeddings)
        
        # Agregar clusters al dataframe
        df_careers['cluster'] = cluster_labels
        
        # Organizar resultados por clusters
        self.career_clusters = {}
        for cluster_id in range(n_clusters):
            cluster_careers = df_careers[df_careers['cluster'] == cluster_id]
            
            # Determinar nombre representativo del cluster
            career_names = cluster_careers['carrera'].tolist()
            cluster_name = self.get_cluster_representative_name(career_names)
            
            self.career_clusters[cluster_name] = {
                'carreras': cluster_careers.to_dict('records'),
                'universidades': cluster_careers['universidad'].unique().tolist(),
                'total_carreras': len(cluster_careers),
                'cluster_id': cluster_id
            }
        
        return self.career_clusters
    
    def extract_career_type(self, career_name):
        """
        Extrae el tipo base de carrera (ej: Ingeniería, Software, Civil, etc.)
        """
        career_lower = career_name.lower()
        
        # Patrones comunes para identificar tipos de carrera
        if 'software' in career_lower or 'sistemas' in career_lower:
            return 'Software/Sistemas'
        elif 'civil' in career_lower:
            return 'Civil'
        elif 'industrial' in career_lower:
            return 'Industrial'
        elif 'electrónica' in career_lower or 'electrónic' in career_lower:
            return 'Electrónica'
        elif 'ambiental' in career_lower:
            return 'Ambiental'
        elif 'alimentos' in career_lower:
            return 'Alimentos'
        elif 'mecánica' in career_lower or 'mecánic' in career_lower:
            return 'Mecánica'
        elif 'automotriz' in career_lower:
            return 'Automotriz'
        elif 'biotecnología' in career_lower or 'bioingeniería' in career_lower:
            return 'Biotecnología'
        elif 'química' in career_lower or 'químic' in career_lower:
            return 'Química'
        elif 'computación' in career_lower or 'informática' in career_lower:
            return 'Computación'
        elif 'telecomunicaciones' in career_lower:
            return 'Telecomunicaciones'
        elif 'minas' in career_lower:
            return 'Minas'
        elif 'producción' in career_lower:
            return 'Producción'
        else:
            return 'Otros'
    
    def get_cluster_representative_name(self, career_names):
        """
        Obtiene un nombre representativo para el cluster basado en las carreras
        """
        # Contar tipos de carrera
        types_count = {}
        for name in career_names:
            career_type = self.extract_career_type(name)
            types_count[career_type] = types_count.get(career_type, 0) + 1
        
        # Retornar el tipo más común
        if types_count:
            return max(types_count.keys(), key=lambda x: types_count[x])
        return "Cluster General"
    
    def find_equivalent_subjects(self, cluster_name, similarity_threshold=0.7):
        """
        Encuentra materias equivalentes dentro de un cluster de carreras
        """
        if cluster_name not in self.career_clusters:
            return {}
        
        # Recopilar todas las materias del cluster
        all_subjects = []
        subject_origins = []
        
        for career in self.career_clusters[cluster_name]['carreras']:
            for subject in career['materias']:
                all_subjects.append(subject)
                subject_origins.append({
                    'materia': subject,
                    'universidad': career['universidad'],
                    'carrera': career['carrera']
                })
        
        # Generar embeddings para las materias
        subject_embeddings = self.sentence_model.encode(all_subjects)
        
        # Calcular matriz de similitud
        similarity_matrix = cosine_similarity(subject_embeddings)
        
        # Encontrar grupos de materias similares
        equivalent_groups = []
        processed_indices = set()
        
        for i in range(len(all_subjects)):
            if i in processed_indices:
                continue
            
            # Encontrar materias similares
            similar_indices = np.where(similarity_matrix[i] >= similarity_threshold)[0]
            
            if len(similar_indices) > 1:
                group = []
                for idx in similar_indices:
                    if idx not in processed_indices:
                        group.append({
                            'materia': all_subjects[idx],
                            'universidad': subject_origins[idx]['universidad'],
                            'carrera': subject_origins[idx]['carrera'],
                            'similitud': float(similarity_matrix[i][idx])
                        })
                        processed_indices.add(idx)
                
                if len(group) > 1:
                    # Ordenar por similitud
                    group.sort(key=lambda x: x['similitud'], reverse=True)
                    equivalent_groups.append({
                        'grupo_id': len(equivalent_groups) + 1,
                        'materia_representativa': group[0]['materia'],
                        'materias_equivalentes': group,
                        'universidades_involucradas': list(set([item['universidad'] for item in group])),
                        'promedio_similitud': np.mean([item['similitud'] for item in group])
                    })
        
        return equivalent_groups
    
    def analyze_curriculum_differences(self, cluster_name):
        """
        Analiza diferencias en la estructura curricular dentro de un cluster
        """
        if cluster_name not in self.career_clusters:
            return {}
        
        careers = self.career_clusters[cluster_name]['carreras']
        
        analysis = {
            'total_carreras': len(careers),
            'promedio_materias': np.mean([career['total_materias'] for career in careers]),
            'rango_materias': {
                'minimo': min([career['total_materias'] for career in careers]),
                'maximo': max([career['total_materias'] for career in careers])
            },
            'universidades': list(set([career['universidad'] for career in careers])),
            'materias_comunes': self.find_common_subjects(careers),
            'materias_unicas': self.find_unique_subjects(careers)
        }
        
        return analysis
    
    def find_common_subjects(self, careers, min_occurrence=0.5):
        """
        Encuentra materias que aparecen en al menos min_occurrence% de las carreras
        """
        subject_count = {}
        total_careers = len(careers)
        
        for career in careers:
            unique_subjects = set([self.preprocess_text(s) for s in career['materias']])
            for subject in unique_subjects:
                subject_count[subject] = subject_count.get(subject, 0) + 1
        
        min_count = int(total_careers * min_occurrence)
        common_subjects = {
            subject: count for subject, count in subject_count.items() 
            if count >= min_count
        }
        
        return dict(sorted(common_subjects.items(), key=lambda x: x[1], reverse=True))
    
    def find_unique_subjects(self, careers):
        """
        Encuentra materias que son únicas de cada universidad
        """
        all_subjects = {}
        
        # Recopilar materias por universidad
        for career in careers:
            university = career['universidad']
            if university not in all_subjects:
                all_subjects[university] = set()
            
            for subject in career['materias']:
                all_subjects[university].add(self.preprocess_text(subject))
        
        # Encontrar materias únicas
        unique_subjects = {}
        for university, subjects in all_subjects.items():
            other_subjects = set()
            for other_uni, other_subs in all_subjects.items():
                if other_uni != university:
                    other_subjects.update(other_subs)
            
            unique = subjects - other_subjects
            if unique:
                unique_subjects[university] = list(unique)
        
        return unique_subjects
    
    def save_model(self, filepath):
        """
        Guarda el modelo entrenado
        """
        model_data = {
            'career_clusters': self.career_clusters,
            'subject_clusters': self.subject_clusters
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath):
        """
        Carga un modelo previamente entrenado
        """
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                self.career_clusters = model_data.get('career_clusters', {})
                self.subject_clusters = model_data.get('subject_clusters', {})
            return True
        return False