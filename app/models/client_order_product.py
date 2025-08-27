from app import db
from sqlalchemy.orm import relationship, validates
import re

class ClientOrderProduct(db.Model):
    __tablename__ = 'ordencliente_producto'
    
    id_orden_cliente = db.Column(db.Integer, db.ForeignKey('ordenes_cliente.id_orden_cliente'), primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    
    # Relaciones
    orden = relationship('ClientOrder', back_populates='productos')
    producto = relationship('Product', back_populates='ordenes_cliente')
    
    # --- Validaciones ---
    @validates('cantidad')
    def validate_cantidad(self, key, value):
        if value is None or value <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        return value
    
    @validates('id_producto')
    def validate_id_producto(self, key, value):
        if not value or not re.match(r'^\d+$', str(value)):
            raise ValueError("El ID del producto debe ser un número válido.")
        return value

    @validates('id_orden_cliente')
    def validate_id_orden(self, key, value):
        if not value or not re.match(r'^\d+$', str(value)):
            raise ValueError("El ID de la orden de cliente debe ser un número válido.")
        return value
    
    def __repr__(self):
        return f'<ClientOrderProduct orden:{self.id_orden_cliente} producto:{self.id_producto} cantidad:{self.cantidad}>'