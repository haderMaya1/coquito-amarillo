from app import db
from sqlalchemy.orm import relationship, validates
import re

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

    # --- Validaciones ---
    @validates('cantidad')
    def validate_cantidad(self, key, value):
        if value is None or value <= 0:
            raise ValueError("La cantidad debe ser un número mayor a cero.")
        return value

    @validates('precio_unitario')
    def validate_precio_unitario(self, key, value):
        if value is None or value < 0:
            raise ValueError("El precio unitario no puede ser negativo.")
        return value

    @validates('id_venta', 'id_producto')
    def validate_foreign_keys(self, key, value):
        if not value or not re.match(r'^\d+$', str(value)):
            raise ValueError(f"El campo {key} debe ser un ID válido.")
        return value
    
    def __repr__(self):
        return f'<SaleProduct venta:{self.id_venta} producto:{self.id_producto} cantidad:{self.cantidad}>'