from app import db
from app.models import Role, User, City, Store, Supplier, Staff, Product

def init_db():
    """Inicializa la base de datos con datos de ejemplo"""
    try:
        # 1. Crear roles básicos
        create_roles()
        
        # 2. Crear usuario administrador
        create_admin_user()
        
        # 3. Crear ciudades de ejemplo
        create_cities()
        
        # 4. Crear tiendas de ejemplo
        create_stores()
        
        # 5. Crear proveedores de ejemplo
        create_suppliers()
        
        # 6. Crear empleados de ejemplo
        create_staff()
        
        # 7. Crear productos de ejemplo
        create_products()
        
        db.session.commit()
        print("Datos iniciales creados exitosamente")
    except Exception as e:
        db.session.rollback()
        print(f"Error al inicializar la base de datos: {str(e)}")
        raise 

def create_roles():
    """Crear roles básicos del sistema"""
    roles = [
        {'nombre': 'Administrador', 'descripcion': 'Acceso total al sistema'},
        {'nombre': 'Vendedor', 'descripcion': 'Puede gestionar, ventas y clientes'},
        {'nombre': 'Proveedor', 'descripcion': 'Puede gestionar, sus órdenes y productos'}
    ]
    
    for role_data in roles:
        if not Role.query.filter_by(nombre=role_data['nombre']).first():
            role = Role(**role_data)
            db.session.add(role)

def create_admin_user():
    """Crear usuario administrador por defecto"""
    admin_role = Role.query.filter_by(nombre='Administrador').first()
    
    if admin_role and not User.query.filter_by(email='admin@coquitoamarrillo.com').first():
        admin_user = User(
            nombre='Administrador Principal',
            email='admin@coquitoamarrillo.com',
            rol_id=admin_role.id_rol
        )
        admin_user.password ='Admin123!'
        db.session.add(admin_user)

def create_cities():
    """Crear ciudades de ejemplo"""
    ciudades = [
        'Medellín', 'Bogotá', 'Cali', 'Barranquilla', 'Cartagena',
        'Bucaramanga', 'Pereira', 'Manizales', 'Cúcuta', 'Ibagué'
    ]
    
    for ciudad_nombre in ciudades:
        if not City.query.filter_by(nombre=ciudad_nombre).first():
            ciudad = City(nombre=ciudad_nombre)
            db.session.add(ciudad)

def create_stores():
    """Crear tiendas de ejemplo"""
    ciudades = City.query.all()
    
    tiendas = [
        {'nombre': 'Tienda Principal Medellín', 'ciudad': 'Medellín', 'direccion': 'Centro Comercial Santafé'},
        {'nombre': 'Tienda Bogotá Norte', 'ciudad': 'Bogotá', 'direccion': 'Centro Comercial Andino'},
        {'nombre': 'Tienda Cali Centro', 'ciudad': 'Cali', 'direccion': 'Centro Comercial Chipichape'},
    ]
    
    for tienda_data in tiendas:
        if not Store.query.filter_by(nombre=tienda_data['nombre']).first():
            ciudad = City.query.filter_by(nombre=tienda_data['ciudad']).first()
            if ciudad:
                tienda = Store(
                    nombre=tienda_data['nombre'],
                    direccion=tienda_data['direccion'],
                    ciudad_id=ciudad.id_ciudad
                )
                db.session.add(tienda)
            else:
                print(f"Advertencia: Ciudad {tienda_data['ciudad']} no encontrada para la tienda {tienda_data['nombre']}")

def create_suppliers():
    """Crear proveedores de ejemplo"""
    ciudades = City.query.all()
    
    proveedores = [
        {
            'nombre': 'Distribuidora Alimentos S.A.',
            'contacto': 'Juan Pérez - juan@dalimentos.com',
            'ciudad': 'Medellín'
        },
        {
            'nombre': 'Importaciones Delicias Ltda.',
            'contacto': 'María Rodríguez - maria@idelicias.com',
            'ciudad': 'Bogotá'
        },
        {
            'nombre': 'Productos Naturales Orgánicos',
            'contacto': 'Carlos Gómez - carlos@productosnaturales.com',
            'ciudad': 'Cali'
        }
    ]
    
    for prov_data in proveedores:
        if not Supplier.query.filter_by(nombre=prov_data['nombre']).first():
            ciudad = City.query.filter_by(nombre=prov_data['ciudad']).first()
            if ciudad:
                proveedor = Supplier(
                    nombre=prov_data['nombre'],
                    contacto=prov_data['contacto'],
                    ciudad_id=ciudad.id_ciudad
                )
                db.session.add(proveedor)
            else:
                print(f"Advertencia: Ciudad {prov_data['ciudad']} no encontrada para el proveedor {prov_data['nombre']}")

def create_staff():
    """Crear empleados de ejemplo"""
    # Obtener roles y tiendas
    rol_vendedor = Role.query.filter_by(nombre='Vendedor').first()
    tienda_medellin = Store.query.filter_by(nombre='Tienda Principal Medellín').first()
    ciudad_medellin = City.query.filter_by(nombre='Medellín').first()
    
    if not all([rol_vendedor, tienda_medellin, ciudad_medellin]):
        print("Advertencia: No se pudo crear el empleado de ejemplo - faltan datos requeridos")
        return
    
    if rol_vendedor and tienda_medellin and ciudad_medellin:
        # Crear usuario vendedor
        if not User.query.filter_by(email='vendedor@coquitoamarrillo.com').first():
            user_vendedor = User(
                nombre='Carlos Vendedor',
                email='vendedor@coquitoamarrillo.com',
                rol_id=rol_vendedor.id_rol
            )
            user_vendedor.password= 'Vendedor123!'
            db.session.add(user_vendedor)
            db.session.flush()  # Para obtener el ID del usuario
            
            # Crear empleado asociado al usuario
            empleado = Staff(
                nombre='Carlos Vendedor',
                cargo='Vendedor Senior',
                salario=2500000,
                ciudad_id=ciudad_medellin.id_ciudad,
                tienda_id=tienda_medellin.id_tienda,
                usuario_id=user_vendedor.id_usuario
            )
            db.session.add(empleado)
            
def create_products():
    """Crear productos de ejemplo"""
    proveedores = Supplier.query.all()
    
    productos = [
        {
            'nombre': 'Arroz Blanco',
            'descripcion': 'Arroz blanco de primera calidad, pacas de 1kg',
            'precio': 2500,
            'stock': 100,
            'proveedor': 'Distribuidora Alimentos S.A.'
        },
        {
            'nombre': 'Aceite de Oliva',
            'descripcion': 'Aceite de oliva extra virgen, botella 500ml',
            'precio': 18000,
            'stock': 50,
            'proveedor': 'Importaciones Delicias Ltda.'
        },
        {
            'nombre': 'Miel Natural',
            'descripcion': 'Miel 100% natural, frasco de 250g',
            'precio': 8500,
            'stock': 75,
            'proveedor': 'Productos Naturales Orgánicos'
        },
        {
            'nombre': 'Café Premium',
            'descripcion': 'Café tostado premium, paquete de 500g',
            'precio': 12000,
            'stock': 60,
            'proveedor': 'Importaciones Delicias Ltda.'
        },
        {
            'nombre': 'Azúcar Orgánica',
            'descripcion': 'Azúcar morena orgánica, paquete de 1kg',
            'precio': 3800,
            'stock': 90,
            'proveedor': 'Productos Naturales Orgánicos'
        }
    ]
    
    for prod_data in productos:
        if not Product.query.filter_by(nombre=prod_data['nombre']).first():
            proveedor = Supplier.query.filter_by(nombre=prod_data['proveedor']).first()
            if proveedor:
                producto = Product(
                    nombre=prod_data['nombre'],
                    descripcion=prod_data['descripcion'],
                    precio=prod_data['precio'],
                    stock=prod_data['stock'],
                    proveedor_id=proveedor.id_proveedor
                )
                db.session.add(producto)
            else:
                print(f"Advertencia: Proveedor {prod_data['proveedor']} no encontrado para el producto {prod_data['nombre']}")