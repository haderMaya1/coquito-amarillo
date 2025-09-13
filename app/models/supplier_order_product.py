from app import db
from sqlalchemy.orm import relationship

class SupplierOrderProduct(db.Model):
    __tablename__ = 'ordenproveedor_producto'
    
    id_proveedor_producto = db.Column(db.Integer, primary_key=True)
    id_orden_proveedor = db.Column(db.Integer, db.ForeignKey('ordenes_proveedor.id_orden_proveedor'))
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'))
    cantidad = db.Column(db.Integer, nullable=False)
    
    # Relaciones
    orden = relationship('SupplierOrder', back_populates='productos')
    producto = relationship('Product', back_populates='ordenes_proveedor')
    
    def __repr__(self):
        return f'<SupplierOrderProduct id:{self.id_proveedor_producto} orden:{self.id_orden_proveedor} producto:{self.id_producto}>'
