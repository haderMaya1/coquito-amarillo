from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

class Invoice(db.Model):
    __tablename__ = 'facturas'
    
    id_factura = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'), nullable=False, unique=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    # Relación
    venta = relationship('Sale', back_populates='factura')

    # --- Métodos de negocio ---
    def desactivar(self):
        """Soft delete de la factura."""
        self.activo = False
    
    def activar(self):
        """Reactivar factura previamente desactivada."""
        self.activo = True

    # --- Validaciones ---
    @validates('total')
    def validate_total(self, key, value):
        if value is None or value < 0:
            raise ValueError("El total de la factura no puede ser negativo.")
        return value

    @validates('venta_id')
    def validate_venta_id(self, key, value):
        if not value or not re.match(r'^\d+$', str(value)):
            raise ValueError("El ID de la venta debe ser válido.")
        return value
    
    def __repr__(self):
        return f'<Factura {self.id_factura} - Venta {self.venta_id} - Total {self.total}>'