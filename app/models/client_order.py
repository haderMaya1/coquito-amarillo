from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class ClientOrder(db.Model):
    __tablename__ = 'ordenes_cliente'
    
    id_orden_cliente = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    
    # Relaciones
    cliente = relationship('Client', back_populates='ordenes')
    productos = relationship('ClientOrderProduct', back_populates='orden')

    def __repr__(self):
        return f'<OrdenCliente id:{self.id_orden_cliente} cliente:{self.cliente_id} estado:{self.estado}>'
