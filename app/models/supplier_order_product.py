from app import db
from sqlalchemy.orm import relationship

class SupplierOrderProduct(db.Model):
    __tablename__ = 'ordenproveedor_producto'
    
    id_orden_proveedor = db.Column(db.Integer, db.ForeignKey('ordenes_proveedor.id_orden_proveedor'), primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    
    # Relaciones
    orden = relationship('SupplierOrder', back_populates='productos')
    producto = relationship('Product', back_populates='ordenes_proveedor')
    
    def __repr__(self):
        return f'<SupplierOrderProduct orden:{self.id_orden_proveedor} producto:{self.id_producto}>'
