"""
Script para diagnosticar problemas con la aplicación
"""
import sys
import os
from pathlib import Path
import json
import traceback

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

print("="*60)
print("DIAGNÓSTICO DE LA APLICACIÓN")
print("="*60)

# 1. Verificar archivos de datos
print("\n1. Verificando archivos de datos...")
data_file = project_root / "data" / "universidades.json"
if data_file.exists():
    print(f"✅ Archivo de datos encontrado: {data_file}")
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Archivo JSON válido con {len(data)} registros")
    except Exception as e:
        print(f"❌ Error al leer el archivo JSON: {e}")
else:
    print(f"❌ Archivo de datos no encontrado: {data_file}")

# 2. Verificar conexión a MongoDB
print("\n2. Verificando conexión a MongoDB...")
try:
    from mongodb_connector import MongoDBConnector
    connector = MongoDBConnector()
    print(f"Configuración: {connector.db_name}/{connector.collection_name}")
    
    if connector.connect():
        print("✅ Conexión a MongoDB exitosa")
        # Verificar contenido
        docs_count = connector.collection.count_documents({})
        print(f"✅ Documentos en la colección: {docs_count}")
        connector.close()
    else:
        print("❌ No se pudo conectar a MongoDB")
except Exception as e:
    print(f"❌ Error al probar la conexión: {e}")
    traceback.print_exc()

# 3. Verificar CurriculumAnalyzer
print("\n3. Verificando CurriculumAnalyzer...")
try:
    from src.curriculum_analyzer import CurriculumAnalyzer
    analyzer = CurriculumAnalyzer()
    print("✅ CurriculumAnalyzer instanciado correctamente")
    
    status = analyzer.check_status()
    print(f"✅ Estado: {status}")
    
    if status["database_connected"]:
        print("✅ Conexión a base de datos correcta")
    else:
        print("❌ No hay conexión a la base de datos")
except Exception as e:
    print(f"❌ Error al verificar CurriculumAnalyzer: {e}")
    traceback.print_exc()

# 4. Verificar versiones de bibliotecas
print("\n4. Verificando versiones de bibliotecas...")
try:
    import streamlit
    print(f"✅ Streamlit versión: {streamlit.__version__}")
    
    import pymongo
    print(f"✅ PyMongo versión: {pymongo.__version__}")
    
    import pandas
    print(f"✅ Pandas versión: {pandas.__version__}")
    
    import numpy
    print(f"✅ NumPy versión: {numpy.__version__}")
    
    try:
        import sentence_transformers
        print(f"✅ Sentence-Transformers versión: {sentence_transformers.__version__}")
    except ImportError:
        print("❓ Sentence-Transformers no instalado")
        
    try:
        import sklearn
        print(f"✅ Scikit-learn versión: {sklearn.__version__}")
    except ImportError:
        print("❓ Scikit-learn no instalado")
except Exception as e:
    print(f"❌ Error al verificar bibliotecas: {e}")

print("\n" + "="*60)
print("DIAGNÓSTICO COMPLETADO")
print("="*60)
