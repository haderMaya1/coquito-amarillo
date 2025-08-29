from app import db
from sqlalchemy.orm import relationship

class SaleProduct(db.Model):
    __tablename__ = 'venta_producto'
    
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'), primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # precio en el momento de la venta
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relaciones
    venta = relationship('Sale', back_populates='productos')
    producto = relationship('Product', back_populates='ventas')
    
    # --- Métodos de negocio ---
    def subtotal(self):
        """Calcula el subtotal del producto en la venta."""
        return float(self.cantidad) * float(self.precio_unitario)

    def desactivar(self):
        """Soft delete del producto en la venta."""
        self.activo = False
    
    def activar(self):
        """Reactivar producto en la venta."""
        self.activo = True
    
    def __repr__(self):
        return f'<SaleProduct venta:{self.id_venta} producto:{self.id_producto} cantidad:{self.cantidad}>'