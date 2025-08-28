from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

class Product(db.Model):
    __tablename__ = 'productos'
    
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'))
    activo = db.Column(db.Boolean, default=True)  # Campo para soft delete
    fecha_eliminacion = db.Column(db.DateTime)    # Fecha de desactivación
    
    # Relaciones
    proveedor = relationship('Supplier', back_populates='productos')
    ventas = relationship('SaleProduct', back_populates='producto', cascade='all, delete-orphan')
    ordenes_cliente = relationship('ClientOrderProduct', back_populates='producto', cascade='all, delete-orphan')
    ordenes_proveedor = relationship('SupplierOrderProduct', back_populates='producto', cascade='all, delete-orphan')
    
    def aumentar_stock(self, cantidad: int):
        """Aumenta el stock del producto"""
        if cantidad <= 0:
            raise ValueError("La cantidad a aumentar debe ser mayor a 0")
        self.stock += cantidad
        db.session.commit()
        
    def reducir_stock(self, cantidad: int):
        """Reduce el stock del producto si hay suficiente disponibilidad"""
        if cantidad <= 0:
            raise ValueError("La cantidad a reducir debe ser mayor a 0")
        if self.stock >= cantidad:
            self.stock -= cantidad
            db.session.commit()
            return True
        return False
    
    def desactivar(self):
        """Marca el producto como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
        db.session.commit()
    
    def activar(self):
        """Reactiva un producto previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
        db.session.commit()
    
    @classmethod
    def get_activos(cls):
        """Obtiene solo los productos activos"""
        return cls.query.filter_by(activo=True)
    
    @classmethod
    def get_inactivos(cls):
        """Obtiene solo los productos inactivos"""
        return cls.query.filter_by(activo=False)
    
    @classmethod
    def get_todos(cls):
        """Obtiene todos los productos, activos e inactivos"""
        return cls.query
    
    #Validaciones
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ]+$', nombre):
            raise ValueError('El nombre solo puede contener letras, números y guiones bajos')
        return nombre
    
    @validates('descripcion')
    def validate_descripcion(self, key, descripcion):
        # Es opcional; si viene None, lo dejamos pasar
        if descripcion is None:
            return descripcion
        descripcion = descripcion.strip()
        if descripcion == '':
            return None
        # Texto con puntuación básica
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ.,:;()!?¿¡%&$#@*+\-/\'"–—]+$', descripcion):
            raise ValueError('La descripción contiene caracteres no permitidos. Solo se permiten letras, números, espacios y signos de puntuación comunes.')
        # Límite lógico acorde a la columna
        if len(descripcion) > 150:
            raise ValueError('La descripción no puede exceder 150 caracteres')
        return descripcion
    
    @validates('precio')
    def validate_precio(self, key, precio):
        if precio is None or precio <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        return round(precio, 2)
    
    @validates('stock')
    def validate_stock(self, key, stock):
        if stock is None or stock < 0:
            raise ValueError("El stock no puede ser negativo")
        return stock
    
    def __repr__(self):
        return f'<Producto {self.nombre}>'
    