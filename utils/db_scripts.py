"""
Scripts de utilidad para manipular la base de datos MongoDB
Incluye funciones para migrar, resetear y actualizar datos
"""
import os
import json
import logging
import datetime
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from tqdm import tqdm

# Agregar el directorio raíz al path para importar módulos propios
sys.path.append(str(Path(__file__).parent.parent))
from mongodb_connector import MongoDBConnector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mongodb_operations.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def find_json_files(base_dir: str, pattern: str = "_enriched.json") -> List[str]:
    """
    Recorre directorios y encuentra archivos JSON enriquecidos
    
    Args:
        base_dir: Directorio base para buscar
        pattern: Patrón para filtrar archivos (por defecto _enriched.json)
        
    Returns:
        Lista de rutas de archivos encontrados
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
                if file.endswith(pattern):
                    json_files.append(os.path.join(uni_path, file))
    
    logging.info(f"Se encontraron {len(json_files)} archivos JSON para procesar")
    return json_files

def read_json_file(file_path: str) -> Optional[Dict]:
    """
    Lee y retorna el contenido de un archivo JSON
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        Diccionario con el contenido del archivo o None si hay error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logging.error(f"Error al leer el archivo {file_path}: {e}")
        return None

def reset_database() -> int:
    """
    Elimina todos los documentos de la colección configurada en MongoDB
    
    Returns:
        Número de documentos eliminados
    """
    # Conectar a MongoDB
    connector = MongoDBConnector()
    if not connector.connect():
        logging.error("No se pudo conectar a MongoDB")
        return 0
        
    try:
        # Obtener base de datos y colección
        collection = connector.get_collection()
        if not collection:
            logging.error("No se pudo obtener la colección")
            return 0
            
        # Obtener número de documentos antes de eliminar
        docs_count = collection.count_documents({})
        
        # Eliminar todos los documentos
        result = collection.delete_many({})
        
        deleted_count = result.deleted_count
        logging.info(f"Se eliminaron {deleted_count} documentos de {collection.name}")
        print(f"\n🗑️  Se eliminaron {deleted_count} documentos de la colección {collection.name}")
        
        return deleted_count
        
    except Exception as e:
        logging.error(f"Error al eliminar documentos: {e}")
        print(f"\n❌ Error al eliminar documentos: {e}")
        return 0
    finally:
        connector.close()

def migrate_to_mongodb(json_files: List[str]) -> Tuple[int, int]:
    """
    Migra todos los archivos JSON a MongoDB
    
    Args:
        json_files: Lista de rutas a archivos JSON
        
    Returns:
        Tupla con (número de documentos insertados, número de errores)
    """
    # Conectar a MongoDB
    connector = MongoDBConnector()
    if not connector.connect():
        logging.error("No se pudo conectar a MongoDB")
        return (0, 0)
        
    try:
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
                    data["_import_timestamp"] = datetime.datetime.now()
                    
                    # Insertar en MongoDB
                    result = connector.insert_one(data)
                    if result:
                        inserted_count += 1
                        logging.debug(f"Documento insertado con ID: {result}")
                    else:
                        error_count += 1
                except Exception as e:
                    logging.error(f"Error al insertar documento de {file_path}: {e}")
                    error_count += 1
        
        # Resumen final
        logging.info(f"Migración completada: {inserted_count} documentos insertados")
        if error_count > 0:
            logging.warning(f"Hubo {error_count} errores durante la migración")
        
        return (inserted_count, error_count)
    
    finally:
        connector.close()

def update_document(file_path: str) -> bool:
    """
    Actualiza un documento específico en MongoDB basado en un archivo JSON
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    data = read_json_file(file_path)
    if not data:
        return False
        
    # Conectar a MongoDB
    connector = MongoDBConnector()
    if not connector.connect():
        logging.error("No se pudo conectar a MongoDB")
        return False
        
    try:
        # Verificar si el documento ya existe
        universidad = data.get("universidad")
        carrera = data.get("carrera")
        
        if not universidad or not carrera:
            logging.error(f"El archivo {file_path} no contiene universidad o carrera")
            return False
            
        # Buscar el documento por universidad y carrera
        existing = connector.find_one({"universidad": universidad, "carrera": carrera})
        
        # Agregar metadata sobre el archivo de origen
        file_name = os.path.basename(file_path)
        data["_source_file"] = file_name
        data["_import_timestamp"] = datetime.datetime.now()
        data["_updated_timestamp"] = datetime.datetime.now()
        
        if existing:
            # Actualizar documento existente
            result = connector.update_one(
                {"universidad": universidad, "carrera": carrera},
                {"$set": data}
            )
            
            if result:
                logging.info(f"Documento actualizado: {universidad} - {carrera}")
                return True
            else:
                logging.warning(f"No se pudo actualizar el documento: {universidad} - {carrera}")
                return False
        else:
            # Insertar nuevo documento
            result = connector.insert_one(data)
            
            if result:
                logging.info(f"Documento insertado: {universidad} - {carrera}")
                return True
            else:
                logging.warning(f"No se pudo insertar el documento: {universidad} - {carrera}")
                return False
    
    except Exception as e:
        logging.error(f"Error al actualizar documento de {file_path}: {e}")
        return False
    
    finally:
        connector.close()

def reset_and_migrate():
    """
    Función principal para resetear y migrar datos a MongoDB
    """
    logging.info("Iniciando reseteo y migración completa de datos a MongoDB local")
    
    # Solicitar confirmación al usuario
    print("\n" + "="*50)
    print("RESETEO Y MIGRACIÓN DE DATOS")
    print("="*50)
    confirmation = input("\n⚠️  ¿Estás seguro de que deseas ELIMINAR TODOS los documentos de la base de datos? (s/n): ")
    
    if confirmation.lower() != 's':
        print("\nOperación cancelada por el usuario.")
        return
    
    # Paso 1: Eliminar todos los documentos
    print("\n" + "="*50)
    print("FASE 1: ELIMINACIÓN DE DATOS EXISTENTES")
    print("="*50)
    deleted_count = reset_database()
    
    # Paso 2: Encontrar archivos JSON
    print("\n" + "="*50)
    print("FASE 2: MIGRACIÓN DE DATOS NUEVOS")
    print("="*50)
    
    base_dir = str(Path(__file__).parent.parent)  # Directorio raíz del proyecto
    json_files = find_json_files(base_dir)
    
    if not json_files:
        logging.warning("No se encontraron archivos JSON para migrar.")
        return
    
    # Paso 3: Migrar a MongoDB
    inserted, errors = migrate_to_mongodb(json_files)
    
    # Paso 4: Mostrar resumen
    print("\n" + "="*50)
    print(f"RESETEO Y MIGRACIÓN COMPLETADOS")
    print(f"- Documentos eliminados: {deleted_count}")
    print(f"- Archivos procesados: {len(json_files)}")
    print(f"- Documentos insertados: {inserted}")
    print(f"- Errores: {errors}")
    print("="*50)
    print(f"Puedes verificar los datos en MongoDB Compass")
    print("="*50)

def migrate_only():
    """
    Función para migrar datos sin resetear la base de datos
    """
    logging.info("Iniciando migración de datos a MongoDB local")
    
    # Encontrar archivos JSON
    base_dir = str(Path(__file__).parent.parent)
    json_files = find_json_files(base_dir)
    
    if not json_files:
        logging.warning("No se encontraron archivos JSON para migrar.")
        return
    
    # Migrar a MongoDB
    inserted, errors = migrate_to_mongodb(json_files)
    
    # Mostrar resumen
    print("\n" + "="*50)
    print(f"MIGRACIÓN COMPLETADA")
    print(f"- Archivos procesados: {len(json_files)}")
    print(f"- Documentos insertados: {inserted}")
    print(f"- Errores: {errors}")
    print("="*50)

def update_specific_file(file_path: str):
    """
    Actualiza un archivo específico en la base de datos
    
    Args:
        file_path: Ruta al archivo a actualizar
    """
    if not os.path.exists(file_path):
        print(f"Error: No se encontró el archivo {file_path}")
        return
        
    print(f"Actualizando documento desde {file_path}...")
    success = update_document(file_path)
    
    if success:
        print("✅ Documento actualizado correctamente")
    else:
        print("❌ Error al actualizar el documento")

if __name__ == "__main__":
    import argparse
    
    # Configurar argumentos del comando
    parser = argparse.ArgumentParser(description="Utilidad para manipular la base de datos MongoDB")
    
    # Crear subparsers para diferentes comandos
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando para resetear y migrar
    reset_parser = subparsers.add_parser("reset", help="Resetear y migrar todos los datos")
    
    # Comando para solo migrar
    migrate_parser = subparsers.add_parser("migrate", help="Migrar datos sin resetear")
    
    # Comando para actualizar un archivo específico
    update_parser = subparsers.add_parser("update", help="Actualizar un archivo específico")
    update_parser.add_argument("file", help="Ruta al archivo JSON a actualizar")
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Ejecutar el comando correspondiente
    if args.command == "reset":
        reset_and_migrate()
    elif args.command == "migrate":
        migrate_only()
    elif args.command == "update" and hasattr(args, "file"):
        update_specific_file(args.file)
    else:
        parser.print_help()
