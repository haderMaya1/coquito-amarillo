from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clientes'
    
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(150))
    telefono = db.Column(db.String(50))
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'))
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    ciudad = relationship('City', back_populates='clientes')
    ventas = relationship('Sale', back_populates='cliente')
    ordenes = relationship('ClientOrder', back_populates='cliente')
    
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
    
    @classmethod
    def get_todos(cls):
        """Obtiene todos los clientes, activos e inactivos"""
        return cls.query
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'