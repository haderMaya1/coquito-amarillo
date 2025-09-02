from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class City(db.Model):
    __tablename__ = 'ciudades'
    
    id_ciudad = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    # tiendas = relationship('Store', back_populates='ciudad')
    clientes = relationship('Client', back_populates='ciudad')
    # proveedores = relationship('Supplier', back_populates='ciudad')
    personal = relationship('Staff', back_populates='ciudad')
    
    # -------- Métodos de consulta ----------
    @classmethod
    def get_all(cls):
        """Obtiene todas las ciudades"""
        return cls.query.order_by(cls.nombre).all()
    
    @classmethod
    def get_by_name(cls, nombre):
        """Obtiene una ciudad por nombre (insensible a mayúsculas/minúsculas)"""
        return cls.query.filter(db.func.lower(cls.nombre) == nombre.lower()).first()
    
    def desactivar(self):
        """Marca el cliente como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
    
    def activar(self):
        """Reactiva un cliente previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
    
    @classmethod
    def get_activos(cls):
        """Obtiene solo los clientes activos"""
        return cls.query.filter_by(activo=True)
    
    @classmethod
    def get_inactivos(cls):
        """Obtiene solo los clientes inactivos"""
        return cls.query.filter_by(activo=False)
    
    def __repr__(self):
        return f'<Ciudad {self.nombre}>'