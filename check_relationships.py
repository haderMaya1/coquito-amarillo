import os
import sys
# Añade el directorio raíz del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.models import *

app = create_app()

with app.app_context():
    print("Verificando relaciones entre modelos...")
    
    # Lista de todos los modelos
    models = [Role, User, City, Store, Client, Supplier, Staff, Product, 
              Sale, Invoice, ClientOrder, SupplierOrder, SaleProduct, 
              ClientOrderProduct, SupplierOrderProduct]
    
    for model in models:
        print(f"\nVerificando modelo: {model.__name__}")
        
        # Obtener información de las relaciones
        mapper = db.inspect(model)
        relationships = mapper.relationships
        
        for rel_name, rel in relationships.items():
            print(f"  - {rel_name}: {rel.target.name} ({"one-to-many" if rel.uselist else "one-to-one"})")
    
    print("\nVerificación completada.")