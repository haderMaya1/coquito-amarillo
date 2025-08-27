from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

class Client(db.Model):
    __tablename__ = 'clientes'
    
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(150))
    telefono = db.Column(db.String(50), unique=True)
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'))
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    ciudad = relationship('City', back_populates='clientes')
    ventas = relationship('Sale', back_populates='cliente', cascade='all, delete-orphan')
    ordenes = relationship('ClientOrder', back_populates='cliente', cascade='all, delete-orphan')
    
    def desactivar(self):
        """Marca el cliente como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
        db.session.commit()
    
    def activar(self):
        """Reactiva un cliente previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
        db.session.commit()
    
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
    
     # ------------ Validaciones ----------------
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        if not nombre or len(nombre.strip()) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        if len(nombre) > 100:
            raise ValueError("El nombre no puede exceder 100 caracteres")
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ]+$', nombre.strip()):
            raise ValueError("El nombre contiene caracteres inválidos")
        return nombre.strip()
    
    @validates('direccion')
    def validate_direccion(self, key, direccion):
        if direccion:
            direccion = direccion.strip()
            if len(direccion) < 3:
                raise ValueError("La dirección debe tener al menos 3 caracteres")
            if len(direccion) > 150:
                raise ValueError("La dirección no puede exceder 150 caracteres")
        return direccion
    
    @validates('telefono')
    def validate_telefono(self, key, telefono):
        if not telefono:
            raise ValueError("El teléfono es obligatorio")
        telefono = telefono.strip()
        if len(telefono) < 7 or len(telefono) > 50:
            raise ValueError("El teléfono debe tener entre 7 y 50 caracteres")
        # Acepta números, espacios, guiones y paréntesis (ej: (57) 320-123-4567)
        if not re.match(r'^[0-9\-\s()+]+$', telefono):
            raise ValueError("El teléfono contiene caracteres inválidos")
        return telefono
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'