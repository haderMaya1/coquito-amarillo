from app import create_app, db
from app.models import Role, User, City, Store, Client, Supplier, Staff, Product

app = create_app()

with app.app_context():
    # Crear todas las tablas
    db.create_all()
    
    # Insertar datos iniciales
    # 1. Roles básicos
    roles = [
        Role(nombre='Administrador', descripcion='Acceso total al sistema'),
        Role(nombre='Vendedor', descripcion='Puede gestionar ventas y clientes'),
        Role(nombre='Proveedor', descripcion='Puede gestionar sus órdenes y productos')
    ]
    
    for role in roles:
        if not Role.query.filter_by(nombre=role.nombre).first():
            db.session.add(role)
    
    db.session.commit()
    
    # 2. Usuario administrador por defecto
    admin_role = Role.query.filter_by(nombre='Administrador').first()
    if admin_role and not User.query.filter_by(email='admin@coquitoamarrillo.com').first():
        admin_user = User(
            nombre='Administrador',
            email='admin@coquitoamarrillo.com',
            rol_id=admin_role.id_rol
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    # 3. Ciudades de ejemplo
    ciudades = ['Medellín', 'Bogotá', 'Cali', 'Barranquilla', 'Cartagena']
    for ciudad_nombre in ciudades:
        if not City.query.filter_by(nombre=ciudad_nombre).first():
            ciudad = City(nombre=ciudad_nombre)
            db.session.add(ciudad)
    
    db.session.commit()
    
    print("Migración completada exitosamente")