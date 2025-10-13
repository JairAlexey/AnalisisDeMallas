"""
Script para diagnosticar la conexión a MongoDB
"""
import sys
import pymongo
from pymongo import MongoClient
from mongodb_connector import MongoDBConnector
import os
from dotenv import load_dotenv

def run_diagnostics():
    print("=" * 60)
    print("DIAGNÓSTICO DE CONEXIÓN A MONGODB")
    print("=" * 60)
    
    # 1. Comprobar si MongoDB está ejecutándose
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB está ejecutándose")
    except Exception as e:
        print(f"❌ MongoDB NO está ejecutándose: {e}")
        print("\nPosibles soluciones:")
        print("  - Asegúrate de que MongoDB está instalado")
        print("  - Verifica que el servicio de MongoDB está en ejecución")
        return
    
    # 2. Verificar la configuración en .env
    print("\nComprobando configuración en .env:")
    load_dotenv()
    
    env_host = os.getenv("MONGODB_HOST", "localhost")
    env_port = os.getenv("MONGODB_PORT", "27017")
    env_db = os.getenv("MONGODB_DB", "No definido")
    env_collection = os.getenv("MONGODB_COLLECTION", "No definido")
    
    print(f"  MONGODB_HOST: {env_host}")
    print(f"  MONGODB_PORT: {env_port}")
    print(f"  MONGODB_DB: {env_db}")
    print(f"  MONGODB_COLLECTION: {env_collection}")
    
    # 3. Verificar bases de datos disponibles
    print("\nBases de datos disponibles en MongoDB:")
    try:
        dbs = client.list_database_names()
        for db in dbs:
            print(f"  - {db}")
    except Exception as e:
        print(f"❌ Error al listar bases de datos: {e}")
    
    # 4. Probar conexión usando MongoDBConnector
    print("\nProbando conexión con MongoDBConnector:")
    connector = MongoDBConnector()
    print(f"  Configuración por defecto: {connector.db_name}/{connector.collection_name}")
    
    if connector.connect():
        print(f"✅ Conexión exitosa a {connector.db_name}/{connector.collection_name}")
        
        # Verificar colecciones en la base de datos
        collections = connector.db.list_collection_names()
        print(f"  Colecciones en {connector.db_name}:")
        for col in collections:
            print(f"    - {col}")
        
        # Verificar documentos en la colección
        doc_count = connector.collection.count_documents({})
        print(f"  Documentos en {connector.collection_name}: {doc_count}")
        
        # Mostrar universidades disponibles
        if doc_count > 0:
            universities = connector.collection.distinct("universidad")
            print(f"  Universidades disponibles ({len(universities)}):")
            for uni in universities:
                print(f"    - {uni}")
    else:
        print("❌ Error al conectar usando MongoDBConnector")
    
    # 5. Probar conexión con configuración alternativa
    print("\nProbando configuración alternativa:")
    alt_db_name = "mallas_curriculares" if connector.db_name != "mallas_curriculares" else "carreras_universitarias"
    alt_collection = "universidades" if connector.collection_name != "universidades" else "mallas_curriculares"
    
    connector2 = MongoDBConnector()
    connector2.db_name = alt_db_name
    connector2.collection_name = alt_collection
    
    print(f"  Probando: {connector2.db_name}/{connector2.collection_name}")
    
    if connector2.connect():
        print(f"✅ Conexión alternativa exitosa a {connector2.db_name}/{connector2.collection_name}")
        
        # Verificar documentos en la colección
        doc_count = connector2.collection.count_documents({})
        print(f"  Documentos en {connector2.collection_name}: {doc_count}")
    else:
        print(f"❌ Error al conectar a {connector2.db_name}/{connector2.collection_name}")
    
    print("\nRECOMENDACIONES:")
    print("1. Verifica que los valores en .env sean correctos")
    print("2. Si existen documentos en otra base de datos o colección, actualiza .env")
    print("3. Si necesitas recrear la base de datos, ejecuta: python init_database.py")
    print("\n¡Diagnóstico completado!")

if __name__ == "__main__":
    run_diagnostics()
