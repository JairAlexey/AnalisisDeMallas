"""
Script simple para probar la conexión a MongoDB
"""
from pymongo import MongoClient
from mongodb_connector import MongoDBConnector
import os
import sys
from pathlib import Path

# Añadir directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_direct_connection():
    """Prueba conexión directa a MongoDB sin usar el conector personalizado"""
    print("\n=== PRUEBA DE CONEXIÓN DIRECTA A MONGODB ===")
    try:
        # Intentar conexión directa
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ Conexión directa exitosa")
        
        # Verificar bases de datos
        dbs = client.list_database_names()
        print(f"Bases de datos disponibles: {', '.join(dbs)}")
        
        # Verificar colecciones en la base de datos objetivo
        db_name = "carreras_universitarias"
        if db_name in dbs:
            db = client[db_name]
            collections = db.list_collection_names()
            print(f"Colecciones en {db_name}: {', '.join(collections)}")
            
            # Verificar contenido en la colección
            collection_name = "mallas_curriculares"
            if collection_name in collections:
                count = db[collection_name].count_documents({})
                print(f"Documentos en {collection_name}: {count}")
                
                # Mostrar ejemplo
                doc = db[collection_name].find_one({})
                if doc:
                    print("\nEjemplo de documento:")
                    print(f"Universidad: {doc.get('universidad', 'N/A')}")
                    print(f"Carrera: {doc.get('carrera', 'N/A')}")
                    print(f"Semestres: {len(doc.get('malla_curricular', {}))}")
            else:
                print(f"❌ No se encontró la colección {collection_name}")
        else:
            print(f"❌ No se encontró la base de datos {db_name}")
            
    except Exception as e:
        print(f"❌ Error al conectar directamente a MongoDB: {e}")
        
def test_connector():
    """Prueba la conexión usando el MongoDBConnector"""
    print("\n=== PRUEBA DE CONEXIÓN USANDO MONGODBCONNECTOR ===")
    connector = MongoDBConnector()
    connector.db_name = "carreras_universitarias"
    connector.collection_name = "mallas_curriculares"
    
    print(f"Intentando conectar a {connector.host}:{connector.port}")
    print(f"Base de datos: {connector.db_name}")
    print(f"Colección: {connector.collection_name}")
    
    if connector.connect():
        print("✅ Conexión exitosa usando MongoDBConnector")
        
        # Verificar obtención de base de datos
        db = connector.get_database()
        if db is not None:
            print("✅ Database object recuperado correctamente")
            
            # Prueba correcta de verificación booleana
            print("Prueba de comparación con None: ", db is not None)
            
            # Verificar obtención de colección
            collection = connector.get_collection()
            if collection is not None:
                print("✅ Collection object recuperado correctamente")
                
                # Contar documentos
                try:
                    count = collection.count_documents({})
                    print(f"✅ Documentos contados correctamente: {count}")
                except Exception as e:
                    print(f"❌ Error al contar documentos: {e}")
            else:
                print("❌ No se pudo obtener el objeto Collection")
        else:
            print("❌ No se pudo obtener el objeto Database")
    else:
        print("❌ No se pudo conectar usando MongoDBConnector")

if __name__ == "__main__":
    test_direct_connection()
    test_connector()
    
    print("\nSi las pruebas de conexión son exitosas pero la aplicación sigue fallando,")
    print("asegúrate de que estás usando la comparación correcta: 'self.db is not None'")
    print("en lugar de 'if self.db' en cualquier parte del código.")
