from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class Staff(db.Model):
    __tablename__ = 'personal'
    
    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100))
    salario = db.Column(db.Numeric(10, 2))
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'))
    tienda_id = db.Column(db.Integer, db.ForeignKey('tiendas.id_tienda'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), unique=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'))
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    ciudad = relationship('City', back_populates='personal')
    tienda = relationship('Store', back_populates='personal')
    usuario = relationship('User', back_populates='empleado', uselist=False)
    proveedor = relationship('Supplier', back_populates='empleados')
    ventas = relationship('Sale', back_populates='empleado', cascade='all, delete-orphan')
    
    def desactivar(self):
        """Marca el empleado como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
        db.session.commit()
    
    def activar(self):
        """Reactiva un empleado previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
        db.session.commit()
    
    @classmethod
    def get_activos(cls):
        """Obtiene solo los empleados activos"""
        return cls.query.filter_by(activo=True)
    
    @classmethod
    def get_inactivos(cls):
        """Obtiene solo los empleados inactivos"""
        return cls.query.filter_by(activo=False)
    
    @classmethod
    def get_todos(cls):
        """Obtiene todos los empleados, activos e inactivos"""
        return cls.query
    
    def __repr__(self):
        return f'<Empleado {self.nombre}>'