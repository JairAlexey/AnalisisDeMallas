#!/usr/bin/env python
"""
Script para reparar problemas comunes en la base de datos
"""
import os
import sys
import json
from pathlib import Path
import logging
from pymongo import MongoClient, errors
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def repair_database():
    """Repara problemas comunes en la base de datos"""
    print("=" * 60)
    print("REPARACIÓN DE BASE DE DATOS MONGODB")
    print("=" * 60)
    
    # 1. Verificar conexión a MongoDB
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Conexión a MongoDB establecida")
    except Exception as e:
        print(f"❌ Error: No se puede conectar a MongoDB: {e}")
        print("   Verifica que MongoDB está instalado y en ejecución")
        return False
    
    # 2. Verificar existencia de base de datos y colección
    db_names = client.list_database_names()
    print(f"Bases de datos existentes: {', '.join(db_names)}")
    
    target_db = "carreras_universitarias"
    target_collection = "mallas_curriculares"
    
    if target_db not in db_names:
        print(f"⚠️ La base de datos '{target_db}' no existe, se creará")
    
    db = client[target_db]
    collection_names = db.list_collection_names()
    
    if target_collection not in collection_names:
        print(f"⚠️ La colección '{target_collection}' no existe, se creará")
    
    # 3. Cargar datos desde archivo JSON
    json_file = Path(__file__).parent / "data" / "universidades.json"
    if not json_file.exists():
        print(f"❌ Error: No se encontró el archivo {json_file}")
        return False
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Se cargaron {len(data)} documentos del archivo JSON")
    except Exception as e:
        print(f"❌ Error al cargar el archivo JSON: {e}")
        return False
    
    # 4. Respaldar datos existentes
    collection = db[target_collection]
    existing_count = collection.count_documents({})
    
    if existing_count > 0:
        print(f"⚠️ La colección ya contiene {existing_count} documentos")
        backup_collection = f"{target_collection}_backup_{int(time.time())}"
        try:
            # Crear backup
            db.command("cloneCollection", 
                      {"from": f"{target_collection}", "collection": backup_collection})
            print(f"✅ Se creó una copia de seguridad en la colección '{backup_collection}'")
        except Exception as e:
            print(f"⚠️ No se pudo crear copia de seguridad: {e}")
    
    # 5. Limpiar y reinsertar los datos
    try:
        collection.delete_many({})
        print(f"✅ Se eliminaron todos los documentos existentes")
        
        # Insertar datos
        result = collection.insert_many(data)
        print(f"✅ Se insertaron {len(result.inserted_ids)} documentos nuevos")
        
        # Verificar que los datos se insertaron correctamente
        count = collection.count_documents({})
        if count == len(data):
            print(f"✅ Verificación exitosa: {count} documentos disponibles")
        else:
            print(f"⚠️ Advertencia: Se esperaban {len(data)} documentos pero se encontraron {count}")
        
        # Mostrar universidades disponibles
        universities = collection.distinct("universidad")
        print(f"✅ Universidades disponibles ({len(universities)}): {', '.join(sorted(universities))}")
        
        return True
    except Exception as e:
        print(f"❌ Error al reiniciar la colección: {e}")
        return False

if __name__ == "__main__":
    if repair_database():
        print("\n✅ ¡Base de datos reparada exitosamente!")
        print("Ahora puedes ejecutar la aplicación con: streamlit run app.py")
    else:
        print("\n❌ Error al reparar la base de datos")
        print("Por favor, revisa los errores y vuelve a intentarlo")
