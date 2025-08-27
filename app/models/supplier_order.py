from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re


class SupplierOrder(db.Model):
    __tablename__ = 'ordenes_proveedor'
    
    id_orden_proveedor = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'), nullable=False)
    
    # Relaciones
    proveedor = relationship('Supplier', back_populates='ordenes')
    productos = relationship('SupplierOrderProduct', back_populates='orden', cascade='all, delete-orphan')
    
    # --- Métodos de negocio ---
    def recibir_orden(self):
        """Marca la orden como recibida y actualiza el inventario"""
        if self.estado == 'pendiente':
            self.estado = 'recibida'
            
            # Actualizar stock de productos
            for item in self.productos:
                producto = item.producto
                producto.stock += item.cantidad
            
            db.session.commit()
    
    def cancelar_orden(self):
        """Cancela la orden si aún está pendiente"""
        if self.estado == 'pendiente':
            self.estado = 'cancelada'
            db.session.commit()
    
    # --- Validaciones ---
    @validates('estado')
    def validate_estado(self, key, estado):
        estado = estado.strip().lower()
        valores_permitidos = ['pendiente', 'recibida', 'cancelada']
        if estado not in valores_permitidos:
            raise ValueError(f"El estado '{estado}' no es válido. Debe ser uno de: {', '.join(valores_permitidos)}")
        return estado
    
    def __repr__(self):
        return f'<OrdenProveedor {self.id_orden_proveedor}>'