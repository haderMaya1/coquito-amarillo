from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

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
    
    # --- Validaciones ---
    @validates('estado')
    def validate_estado(self, key, value):
        if value not in ['activa', 'anulada']:
            raise ValueError("El estado de la venta debe ser 'activa' o 'anulada'.")
        return value

    @validates('total')
    def validate_total(self, key, value):
        if value is None or value < 0:
            raise ValueError("El total de la venta no puede ser negativo ni nulo.")
        return value

    @validates('cliente_id', 'empleado_id', 'tienda_id')
    def validate_foreign_keys(self, key, value):
        if not value or not re.match(r'^\d+$', str(value)):
            raise ValueError(f"El campo {key} debe ser un ID válido.")
        return value

    def validate(self):
        """Validaciones adicionales a nivel de instancia"""
        errors = []
        if not self.cliente_id:
            errors.append("Debe asociarse un cliente a la venta.")
        if not self.empleado_id:
            errors.append("Debe asociarse un empleado (vendedor) a la venta.")
        if not self.tienda_id:
            errors.append("La venta debe estar ligada a una tienda.")
        if not self.productos or len(self.productos) == 0:
            errors.append("La venta debe incluir al menos un producto.")
        return errors
    
    def __repr__(self):
        return f'<Venta {self.id_venta} - Total: {self.total}>'
