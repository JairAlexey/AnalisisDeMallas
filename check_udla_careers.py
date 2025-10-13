"""
Script para verificar específicamente las carreras de UDLA en la base de datos
"""
import sys
import os
from pathlib import Path
import traceback
import re

# Añadir el directorio del proyecto al path para importar módulos locales
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Importar módulos propios
from mongodb_connector import MongoDBConnector

def check_udla_careers():
    print("=" * 60)
    print("VERIFICACIÓN DE CARRERAS UDLA")
    print("=" * 60)
    
    # Conectar a MongoDB
    connector = MongoDBConnector()
    print(f"Intentando conectar a {connector.db_name}/{connector.collection_name}")
    
    if not connector.connect():
        print("❌ Error: No se pudo conectar a MongoDB")
        return
    
    print("✅ Conexión exitosa a MongoDB")
    
    # Verificar todas las universidades
    try:
        universities = connector.collection.distinct("universidad")
        print(f"\nSe encontraron {len(universities)} universidades:")
        
        # Mostrar cada universidad con su cantidad de carreras
        for univ in sorted(universities):
            count = connector.collection.count_documents({"universidad": univ})
            print(f"- {univ} ({count} carreras)")
        
        # Buscar universidades que podrían ser UDLA
        print("\nBuscando universidades que podrían ser UDLA:")
        udla_candidates = []
        
        for univ in universities:
            if (re.search(r"UDLA", univ, re.IGNORECASE) or 
                re.search(r"América", univ, re.IGNORECASE) or
                re.search(r"America", univ, re.IGNORECASE)):
                udla_candidates.append(univ)
        
        if udla_candidates:
            print("✅ Posibles coincidencias de UDLA:")
            for candidate in udla_candidates:
                count = connector.collection.count_documents({"universidad": candidate})
                print(f"- {candidate} ({count} carreras)")
                
                # Mostrar las carreras de esta universidad
                careers = connector.collection.distinct("carrera", {"universidad": candidate})
                print("  Carreras disponibles:")
                for career in sorted(careers):
                    print(f"  - {career}")
        else:
            print("❌ No se encontraron universidades que coincidan con UDLA")
            
        # Sugerir solución
        print("\n" + "=" * 60)
        print("SOLUCIÓN RECOMENDADA:")
        print("=" * 60)
        print("1. Revise el archivo data/universidades.json para verificar cómo está")
        print("   escrito el nombre de la UDLA (Universidad de Las Américas).")
        print("\n2. Modifique la función list_udla_careers() para que busque con el nombre correcto:")
        print("   - Si dice 'Universidad de Las Américas', use ese nombre exacto")
        print("   - Si tiene otro formato, actualice la lista de variantes en la función")
        
        print("\n3. Alternativamente, para una solución rápida, modifique sus documentos en MongoDB:")
        
        if udla_candidates:
            candidate = udla_candidates[0]
            print(f"   db.mallas_curriculares.updateMany({{ 'universidad': '{candidate}' }},")
            print(f"                                  {{ $set: {{ 'universidad': 'UDLA' }} }})")
        
    except Exception as e:
        print(f"❌ Error al verificar universidades: {e}")
        traceback.print_exc()
    
    finally:
        connector.close()

if __name__ == "__main__":
    check_udla_careers()
