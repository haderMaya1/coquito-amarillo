from app import db
from sqlalchemy.orm import relationship
from datetime import datetime

class Store(db.Model):
    __tablename__ = 'tiendas'
    
    id_tienda = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(150))
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudades.id_ciudad'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)
    
    # Relaciones
    ciudad = relationship('City', back_populates='tiendas')
    personal = relationship('Staff', back_populates='tienda')
    ventas = relationship('Sale', back_populates='tienda')
    
    def desactivar(self):
        """Marca la tienda como inactiva (soft delete) y desactiva su personal"""
        try:
            self.activo = False
            self.fecha_eliminacion = datetime.utcnow()
            
            # Desactivar todo el personal asociado a esta tienda
            for empleado in self.personal:
                empleado.desactivar()
                
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al desactivar tienda: {str(e)}')
    
    def activar(self):
        """Reactiva una tienda previamente desactivada"""
        try:
            self.activo = True
            self.fecha_eliminacion = None
            return True
        
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al activar tienda: {str(e)}')
    
    @classmethod
    def get_activas(cls):
        """Obtiene solo las tiendas activas"""
        return cls.query.filter_by(activo=True)
    
    @classmethod
    def get_inactivas(cls):
        """Obtiene solo las tiendas inactivas"""
        return cls.query.filter_by(activo=False)
    
    @classmethod
    def get_todas(cls):
        """Obtiene todas las tiendas, activas e inactivas"""
        return cls.query
    
    @classmethod
    def buscar_por_nombre(cls, nombre):
        """Busca tiendas por nombre (búsqueda parcial)"""
        return cls.get_activas().filter(Store.nombre.ilike(f'%{nombre}%')).all()
    
    @classmethod
    def buscar_por_ciudad(cls, ciudad_id):
        """Busca tiendas por ciudad"""
        return cls.get_activas().filter_by(ciudad_id=ciudad_id).all()
    
    def obtener_personal_activo(self):
        """Obtiene el personal activo de esta tienda"""
        return [empleado for empleado in self.personal if empleado.activo]
    

    def __repr__(self):
        return f'<Tienda {self.nombre}>'