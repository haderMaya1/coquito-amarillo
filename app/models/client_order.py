from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

class ClientOrder(db.Model):
    __tablename__ = 'ordenes_cliente'
    
    id_orden_cliente = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    
    # Relaciones
    cliente = relationship('Client', back_populates='ordenes')
    productos = relationship('ClientOrderProduct', back_populates='orden', cascade='all, delete-orphan')
    
    # --- Validaciones ---
    @validates('estado')
    def validate_estado(self, key, value):
        estados_validos = ['pendiente', 'procesando', 'completada', 'cancelada']
        if value not in estados_validos:
            raise ValueError(f"Estado inválido: {value}. Debe ser uno de {estados_validos}")
        return value

    @validates('cliente_id')
    def validate_cliente_id(self, key, value):
        if not value or not re.match(r'^\d+$', str(value)):
            raise ValueError("El ID del cliente debe ser un número válido.")
        return value

    @validates('fecha')
    def validate_fecha(self, key, value):
        if not isinstance(value, datetime):
            raise ValueError("La fecha debe ser un objeto datetime válido.")
        return value

    def __repr__(self):
        return f'<OrdenCliente id:{self.id_orden_cliente} cliente:{self.cliente_id} estado:{self.estado}>'
