from app import db
from sqlalchemy.orm import relationship

class City(db.Model):
    __tablename__ = 'ciudades'
    
    id_ciudad = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    
    # Relaciones
    tiendas = relationship('Store', back_populates='ciudad', cascade='all, delete-orphan')
    clientes = relationship('Client', back_populates='ciudad', cascade='all, delete-orphan')
    proveedores = relationship('Supplier', back_populates='ciudad', cascade='all, delete-orphan')
    personal = relationship('Staff', back_populates='ciudad', cascade='all, delete-orphan')
    
    # -------- Métodos de consulta ----------
    @classmethod
    def get_all(cls):
        """Obtiene todas las ciudades"""
        return cls.query.order_by(cls.nombre).all()
    
    @classmethod
    def get_by_name(cls, nombre):
        """Obtiene una ciudad por nombre (insensible a mayúsculas/minúsculas)"""
        return cls.query.filter(db.func.lower(cls.nombre) == nombre.lower()).first()
    
    def __repr__(self):
        return f'<Ciudad {self.nombre}>'
    
    def __repr__(self):
        return f'<Ciudad {self.nombre}>'