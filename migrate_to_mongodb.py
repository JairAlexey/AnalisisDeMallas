import os
import json
import pymongo
from pymongo import MongoClient
import urllib.parse
from dotenv import load_dotenv
from tqdm import tqdm
import sys
import logging
import datetime  # Agregar importación del módulo datetime estándar

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mongodb_migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def connect_to_mongodb():
    """
    Conecta a la base de datos MongoDB local (MongoDB Compass)
    """
    # Cargar variables de entorno desde .env si existe
    load_dotenv()
    
    # Configuración para MongoDB local
    mongodb_host = os.getenv("MONGODB_HOST", "localhost")
    mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
    
    # Verificar si se necesita autenticación
    use_auth = os.getenv("MONGODB_USE_AUTH", "false").lower() == "true"
    
    if use_auth:
        username = os.getenv("MONGODB_USERNAME")
        password = os.getenv("MONGODB_PASSWORD")
        
        if not username or not password:
            username = input("Ingrese usuario MongoDB local: ")
            password = urllib.parse.quote_plus(input("Ingrese contraseña MongoDB local: "))
        
        connection_string = f"mongodb://{username}:{password}@{mongodb_host}:{mongodb_port}/"
    else:
        # Conexión sin autenticación
        connection_string = f"mongodb://{mongodb_host}:{mongodb_port}/"
    
    # Conectar a MongoDB local
    try:
        client = MongoClient(connection_string)
        # Verificar la conexión
        client.admin.command('ping')
        logging.info(f"Conexión exitosa a MongoDB local en {mongodb_host}:{mongodb_port}")
        return client
    except Exception as e:
        logging.error(f"Error de conexión a MongoDB local: {e}")
        print(f"\nError de conexión: {e}")
        print("Asegúrate que MongoDB esté ejecutándose en tu máquina local")
        print("Si usas MongoDB Compass, verifica que el servicio de MongoDB esté activo")
        return None

def find_json_files(base_dir):
    """
    Recorre directorios y encuentra archivos JSON enriquecidos
    """
    json_files = []
    universidad_dirs = os.path.join(base_dir, 'data', 'Universidades')
    
    if not os.path.exists(universidad_dirs):
        logging.error(f"El directorio {universidad_dirs} no existe")
        return []
    
    # Recorrer directorios de universidades
    for universidad in os.listdir(universidad_dirs):
        uni_path = os.path.join(universidad_dirs, universidad)
        
        # Verificar que sea un directorio
        if os.path.isdir(uni_path):
            # Buscar archivos JSON en el directorio de la universidad
            for file in os.listdir(uni_path):
                if file.endswith("_enriched.json"):
                    json_files.append(os.path.join(uni_path, file))
    
    logging.info(f"Se encontraron {len(json_files)} archivos JSON para procesar")
    return json_files

def read_json_file(file_path):
    """
    Lee y retorna el contenido de un archivo JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logging.error(f"Error al leer el archivo {file_path}: {e}")
        return None

def migrate_to_mongodb(client, json_files):
    """
    Migra todos los archivos JSON a MongoDB
    """
    # Seleccionar base de datos y colección
    db_name = os.getenv("MONGODB_DB", "carreras_universitarias")
    collection_name = os.getenv("MONGODB_COLLECTION", "mallas_curriculares")
    
    db = client[db_name]
    collection = db[collection_name]
    
    # Contador de documentos insertados
    inserted_count = 0
    error_count = 0
    
    # Procesar cada archivo JSON con barra de progreso
    for file_path in tqdm(json_files, desc="Migrando datos a MongoDB"):
        data = read_json_file(file_path)
        
        if data:
            try:
                # Agregar metadata sobre el archivo de origen
                file_name = os.path.basename(file_path)
                data["_source_file"] = file_name
                data["_import_timestamp"] = datetime.datetime.now()  # Corregido: usar datetime estándar
                
                # Insertar en MongoDB
                result = collection.insert_one(data)
                inserted_count += 1
                logging.debug(f"Documento insertado con ID: {result.inserted_id}")
            except Exception as e:
                logging.error(f"Error al insertar documento de {file_path}: {e}")
                error_count += 1
    
    # Resumen final
    logging.info(f"Migración completada: {inserted_count} documentos insertados")
    if error_count > 0:
        logging.warning(f"Hubo {error_count} errores durante la migración")
    
    return inserted_count, error_count

def main():
    """
    Función principal que ejecuta todo el proceso
    """
    logging.info("Iniciando migración de datos a MongoDB local")
    
    # Paso 1: Conectar a MongoDB
    client = connect_to_mongodb()
    if not client:
        logging.error("No se pudo conectar a MongoDB local. Abortando.")
        return
    
    # Paso 2: Encontrar archivos JSON
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Directorio actual del script
    json_files = find_json_files(base_dir)
    
    if not json_files:
        logging.warning("No se encontraron archivos JSON para migrar.")
        return
    
    # Paso 3: Migrar a MongoDB
    inserted, errors = migrate_to_mongodb(client, json_files)
    
    # Paso 4: Mostrar resumen
    print("\n" + "="*50)
    print(f"MIGRACIÓN COMPLETADA")
    print(f"- Total archivos procesados: {len(json_files)}")
    print(f"- Documentos insertados: {inserted}")
    print(f"- Errores: {errors}")
    print("="*50)
    print(f"Puedes verificar los datos en MongoDB Compass conectándote a localhost:27017")
    print(f"Base de datos: {os.getenv('MONGODB_DB', 'carreras_universitarias')}")
    print(f"Colección: {os.getenv('MONGODB_COLLECTION', 'mallas_curriculares')}")
    print("="*50)
    
    # Cerrar conexión
    client.close()
    logging.info("Conexión a MongoDB local cerrada")

if __name__ == "__main__":
    main()
