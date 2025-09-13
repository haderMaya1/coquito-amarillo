from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class Supplier(db.Model):
    __tablename__ = 'proveedores'
    
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'))
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    
    # Relaciones
    ciudad = relationship('City', back_populates='proveedores')
    productos = relationship('Product', back_populates='proveedor')
    ordenes = relationship('SupplierOrder', back_populates='proveedor')
    empleados = relationship('Staff', back_populates='proveedor')
    usuarios = relationship('User', back_populates='empleados')
    
    
        
    # --- Métodos de negocio ---
    def desactivar(self):
        """Marca el proveedor como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
    
    def activar(self):
        """Reactiva un proveedor previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
        
    @classmethod
    def get_activos(cls):
        """Obtiene solo los proveedores activos"""
        return cls.query.filter_by(activo=True)
    
    @classmethod
    def get_activas(cls):
        """Alias para get_activos (para consistencia con otros modelos)"""
        return cls.get_activos()
    
    @classmethod
    def get_inactivos(cls):
        """Obtiene solo los proveedores inactivos"""
        return cls.query.filter_by(activo=False)
    
    @classmethod
    def get_todos(cls):
        """Obtiene todos los proveedores, activos e inactivos"""
        return cls.query

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'