from app import db
from sqlalchemy.orm import relationship

class Store(db.Model):
    __tablename__ = 'tiendas'
    
    id_tienda = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(150))
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    ciudad = relationship('City', back_populates='tiendas')
    personal = relationship('Staff', back_populates='tienda', cascade='all, delete-orphan')
    ventas = relationship('Sale', back_populates='tienda', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tienda {self.nombre}>'