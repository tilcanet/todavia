
import os
import django
import csv
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_todavia.settings")
django.setup()

from core.models import Localidad

def import_csv(file_path):
    print(f"Iniciando importación desde: {file_path}")
    count = 0
    errors = 0
    
    # Probamos latin-1 que es común en sistemas Windows/Excel viejos
    with open(file_path, 'r', encoding='latin-1') as f:
        # Detect delimiter
        line = f.readline()
        f.seek(0)
        delimiter = ';' if ';' in line else ','
        print(f"Delimitador detectado: '{delimiter}'")
        
        reader = csv.DictReader(f, delimiter=delimiter)
        
        # Limpiar tabla anterior si se desea (opcional)
        # Localidad.objects.all().delete() 
        
        for row in reader:
            try:
                # Normalizar floats (cambiar , por .)
                lat_str = row.get('Latitud', '').replace(',', '.')
                lon_str = row.get('Longitud', '').replace(',', '.')
                
                if not lat_str or not lon_str:
                    print(f"Fila incompleta: {row}")
                    continue

                nombre = row.get('Nombre', '').strip()
                municipio = row.get('Municipio', '').strip()
                departamento = row.get('Departamento', '').strip()
                provincia = row.get('Provincia', 'JUJUY').strip()

                Localidad.objects.get_or_create(
                    nombre=nombre,
                    latitud=float(lat_str),
                    longitud=float(lon_str),
                    defaults={
                        'municipio': municipio,
                        'departamento': departamento,
                        'provincia': provincia
                    }
                )
                count += 1
                if count % 10 == 0:
                    print(f"Procesadas {count} localidades...", end='\r')
                    
            except Exception as e:
                print(f"Error en fila {row}: {e}")
                errors += 1

    print(f"\nImportación finalizada. Creados/Verificados: {count}. Errores: {errors}")

if __name__ == "__main__":
    csv_path = r"c:\Users\Tilcanet\Desktop\Proyecto\proyecto_todavia\Salud\localidades\localidades_jujuy.csv"
    import_csv(csv_path)
