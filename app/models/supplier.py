from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re


class Supplier(db.Model):
    __tablename__ = 'proveedores'
    
    id_proveedor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'))
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    ciudad = relationship('City', back_populates='proveedores')
    productos = relationship('Product', back_populates='proveedor', cascade='all, delete-orphan')
    ordenes = relationship('SupplierOrder', back_populates='proveedor', cascade='all, delete-orphan')
    empleados = relationship('Staff', back_populates='proveedor', cascade='all, delete-orphan')
    
    # --- Métodos de negocio ---
    def desactivar(self):
        """Marca el proveedor como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
        db.session.commit()
    
    def activar(self):
        """Reactiva un proveedor previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
        db.session.commit()
    
    @classmethod
    def get_activos(cls):
        """Obtiene solo los proveedores activos"""
        return cls.query.filter_by(activo=True)
    
    @classmethod
    def get_inactivos(cls):
        """Obtiene solo los proveedores inactivos"""
        return cls.query.filter_by(activo=False)
    
    @classmethod
    def get_todos(cls):
        """Obtiene todos los proveedores, activos e inactivos"""
        return cls.query
    
    # --- Validaciones ---
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        if not nombre or len(nombre.strip()) < 3:
            raise ValueError("El nombre del proveedor debe tener al menos 3 caracteres")
        return nombre.strip().title()
    
    @validates('contacto')
    def validate_contacto(self, key, contacto):
        if contacto and not re.match(r'^[\w\s\.\-@]+$', contacto):
            raise ValueError("El contacto contiene caracteres no válidos")
        return contacto.strip() if contacto else None
    
    def __repr__(self):
        return f'<Proveedor {self.nombre}>'