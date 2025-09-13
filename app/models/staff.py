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
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id_proveedor'))
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    ciudad = relationship('City', back_populates='personal')
    tienda = relationship('Store', back_populates='personal')
    usuario = relationship('User', back_populates='empleado_asociado')
    proveedor = relationship('Supplier', back_populates='empleados')
    ventas = relationship('Sale', back_populates='empleado')
 
    def desactivar(self):
        """Marca el empleado como inactivo (soft delete)"""
        try:
            self.activo = False
            self.fecha_eliminacion = datetime.utcnow()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al desactivar empleado: {str(e)}')
    
    def activar(self):
        """Reactiva un empleado previamente desactivado"""
        try:
            self.activo = True
            self.fecha_eliminacion = None
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al activar empleado: {str(e)}')
    
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
    
    def to_dict(self):
        """Convierte el objeto a diccionario para serialización"""
        return {
            'id_empleado': self.id_empleado,
            'nombre': self.nombre,
            'cargo': self.cargo,
            'salario': float(self.salario) if self.salario else None,
            'ciudad_id': self.ciudad_id,
            'tienda_id': self.tienda_id,
            'usuario_id': self.usuario_id,
            'proveedor_id': self.proveedor_id,
            'activo': self.activo,
            'fecha_eliminacion': self.fecha_eliminacion.isoformat() if self.fecha_eliminacion else None
        }
        
    def __repr__(self):
        return f'<Empleado {self.nombre}>'