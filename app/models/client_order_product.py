from app import db
from sqlalchemy.orm import relationship

class ClientOrderProduct(db.Model):
    __tablename__ = 'ordencliente_producto'
    
    id_orden_cliente = db.Column(db.Integer, db.ForeignKey('ordenes_cliente.id_orden_cliente'), primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    
    # Relaciones
    orden = relationship('ClientOrder', back_populates='productos')
    producto = relationship('Product', back_populates='ordenes_cliente')
    
    def __repr__(self):
        return f'<ClientOrderProduct orden:{self.id_orden_cliente} producto:{self.id_producto} cantidad:{self.cantidad}>'