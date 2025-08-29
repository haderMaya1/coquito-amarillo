from app import db
from sqlalchemy.orm import relationship
from datetime import datetime


class Sale(db.Model):
    __tablename__ = 'ventas'
    
    id_venta = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    estado = db.Column(db.String(20), nullable=False, default='activa')  # activa | anulada
    activo = db.Column(db.Boolean, default=True, nullable=False)

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('personal.id_empleado'), nullable=False)
    tienda_id = db.Column(db.Integer, db.ForeignKey('tiendas.id_tienda'), nullable=False)
    
    # Relaciones
    cliente = relationship('Client', back_populates='ventas')
    empleado = relationship('Staff', back_populates='ventas')
    tienda = relationship('Store', back_populates='ventas')
    factura = relationship('Invoice', back_populates='venta', uselist=False, cascade='all, delete-orphan')
    productos = relationship('SaleProduct', back_populates='venta', cascade='all, delete-orphan')
    
    # --- Métodos de negocio ---
    def calcular_total(self):
        """Recalcula el total de la venta sumando los subtotales de productos."""
        self.total = sum([p.subtotal() for p in self.productos if p.activo])
        return self.total

    def anular(self):
        """Anula la venta y desactiva sus productos asociados."""
        self.estado = 'anulada'
        self.activo = False
        for p in self.productos:
            p.activo = False

    def activar(self):
        """Reactiva una venta anulada (si aplica)."""
        self.estado = 'activa'
        self.activo = True
        for p in self.productos:
            p.activo = True
    
    def __repr__(self):
        return f'<Venta {self.id_venta} - Total: {self.total}>'
