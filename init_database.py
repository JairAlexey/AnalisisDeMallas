"""
Script para inicializar la base de datos MongoDB con los datos de universidades
"""
import os
import json
import logging
from pathlib import Path
from mongodb_connector import MongoDBConnector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def initialize_database():
    """Inicializa la base de datos con datos de universidades"""
    print("="*50)
    print("INICIALIZACIÓN DE BASE DE DATOS MONGODB")
    print("="*50)
    
    # Conectar a MongoDB
    connector = MongoDBConnector()
    connector.db_name = "carreras_universitarias"
    connector.collection_name = "mallas_curriculares"
    
    if not connector.connect():
        print("❌ Error: No se pudo conectar a MongoDB.")
        print("   Asegúrate de que MongoDB está instalado y en ejecución.")
        return False
    
    # Verificar si la colección ya tiene datos
    collection = connector.get_collection()
    doc_count = collection.count_documents({})
    
    if doc_count > 0:
        print(f"ℹ️ La base de datos ya contiene {doc_count} documentos.")
        option = input("¿Deseas eliminar y volver a cargar los datos? (s/n): ").lower()
        if option == 's':
            result = collection.delete_many({})
            print(f"🗑️ Se eliminaron {result.deleted_count} documentos existentes.")
        else:
            print("✅ Operación cancelada. Los datos existentes se mantienen.")
            connector.close()
            return True
    
    # Cargar datos del archivo JSON
    data_file = Path(__file__).parent / "data" / "universidades.json"
    
    if not data_file.exists():
        print(f"❌ Error: No se encontró el archivo {data_file}")
        return False
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            universities_data = json.load(f)
        
        print(f"📊 Se cargaron {len(universities_data)} registros de universidades del archivo JSON.")
        
        # Insertar datos en MongoDB
        inserted_count = 0
        for university_data in universities_data:
            result = connector.insert_one(university_data)
            if result:
                inserted_count += 1
        
        print(f"✅ Se insertaron {inserted_count} documentos en la base de datos.")
        return True
    
    except Exception as e:
        print(f"❌ Error al cargar o insertar datos: {e}")
        return False
    
    finally:
        connector.close()

if __name__ == "__main__":
    if initialize_database():
        print("="*50)
        print("BASE DE DATOS INICIALIZADA CORRECTAMENTE")
        print("="*50)
    else:
        print("="*50)
        print("ERROR AL INICIALIZAR LA BASE DE DATOS")
        print("="*50)
