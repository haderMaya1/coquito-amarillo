import sys
import os
# Añadir el directorio raíz al path de Python
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app
from app.seeds import init_db

app = create_app()

with app.app_context():
    print("Ejecutando semillas de datos iniciales...")
    init_db()
    print("Semillas ejecutadas exitosamente")