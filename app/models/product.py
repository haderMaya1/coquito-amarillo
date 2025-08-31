from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

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
    ventas = relationship('SaleProduct', back_populates='producto')
    ordenes_cliente = relationship('ClientOrderProduct', back_populates='producto')
    ordenes_proveedor = relationship('SupplierOrderProduct', back_populates='producto')
    
    def aumentar_stock(self, cantidad: int):
        """Aumenta el stock del producto"""
        if cantidad <= 0:
            raise ValueError("La cantidad a aumentar debe ser mayor a 0")
        self.stock += cantidad
        
    def reducir_stock(self, cantidad: int):
        """Reduce el stock del producto si hay suficiente disponibilidad"""
        if cantidad <= 0:
            raise ValueError("La cantidad a reducir debe ser mayor a 0")
        if self.stock >= cantidad:
            self.stock -= cantidad
            return True
        return False
    
    def desactivar(self):
        """Marca el producto como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
    
    def activar(self):
        """Reactiva un producto previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
    
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
    
    def __repr__(self):
        return f'<Producto {self.nombre}>'
    