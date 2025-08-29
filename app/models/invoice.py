from app import db
from sqlalchemy.orm import relationship
from datetime import datetime


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
    
    def __repr__(self):
        return f'<Factura {self.id_factura} - Venta {self.venta_id} - Total {self.total}>'