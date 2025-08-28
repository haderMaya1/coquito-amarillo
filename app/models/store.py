from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re
from sqlalchemy.exc import IntegrityError

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
    personal = relationship('Staff', back_populates='tienda', cascade='all, delete-orphan')
    ventas = relationship('Sale', back_populates='tienda', cascade='all, delete-orphan')
    
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        """Validar que el nombre de la tienda sea válido"""
        if not nombre or not nombre.strip():
            raise ValueError('El nombre de la tienda no puede estar vacío')
        
        if len(nombre) > 100:
            raise ValueError('El nombre no puede exceder 100 caracteres')
        
        # Validar que el nombre solo contenga caracteres permitidos
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s\-\'\.&]+$', nombre):
            raise ValueError('El nombre contiene caracteres no válidos')
        
        return nombre.strip()
    
    @validates('direccion')
    def validate_direccion(self, key, direccion):
        """Validar que la dirección sea válida"""
        if direccion is not None:
            if len(direccion) > 150:
                raise ValueError('La dirección no puede exceder 150 caracteres')
            
            # Validar que la dirección no contenga caracteres potencialmente peligrosos
            dangerous_patterns = [
                r'<script', r'javascript:', r'onload=', r'onerror=',
                r'union.*select', r'drop.*table', r';.*--'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, direccion, re.IGNORECASE):
                    raise ValueError('La dirección contiene texto no permitido')
        
        return direccion
    
    @validates('ciudad_id')
    def validate_ciudad_id(self, key, ciudad_id):
        """Validar que la ciudad exista en la base de datos"""
        from app.models import City  # Importación local para evitar circular imports
        
        if not ciudad_id:
            raise ValueError('La ciudad es requerida')
        
        # Verificar que la ciudad existe
        ciudad = City.query.get(ciudad_id)
        if not ciudad:
            raise ValueError('La ciudad especificada no existe')
        
        return ciudad_id
    
    def desactivar(self):
        """Marca la tienda como inactiva (soft delete) y desactiva su personal"""
        try:
            self.activo = False
            self.fecha_eliminacion = datetime.utcnow()
            
            # Desactivar todo el personal asociado a esta tienda
            for empleado in self.personal:
                empleado.desactivar()
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al desactivar tienda: {str(e)}')
    
    def activar(self):
        """Reactiva una tienda previamente desactivada"""
        try:
            self.activo = True
            self.fecha_eliminacion = None
            db.session.commit()
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
    
    def obtener_ventas_por_rango_fechas(self, fecha_inicio, fecha_fin):
        """Obtiene las ventas de esta tienda en un rango de fechas"""
        from app.models import Sale  # Importación local para evitar circular imports
        
        return Sale.query.filter(
            Sale.tienda_id == self.id_tienda,
            Sale.fecha_venta >= fecha_inicio,
            Sale.fecha_venta <= fecha_fin
        ).all()
    
    def to_dict(self):
        """Convierte el objeto a diccionario para serialización"""
        return {
            'id_tienda': self.id_tienda,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'ciudad_id': self.ciudad_id,
            'activo': self.activo,
            'fecha_eliminacion': self.fecha_eliminacion.isoformat() if self.fecha_eliminacion else None,
            'cantidad_personal': len(self.obtener_personal_activo())
        }
    
    @classmethod
    def create_from_dict(cls, data):
        """Crea una nueva tienda desde un diccionario con validación"""
        try:
            tienda = cls()
            
            # Asignar valores con validación
            for key, value in data.items():
                if hasattr(tienda, key):
                    setattr(tienda, key, value)
            
            db.session.add(tienda)
            db.session.commit()
            return tienda
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al crear tienda: {str(e)}')
    
    def update_from_dict(self, data):
        """Actualiza la tienda desde un diccionario con validación"""
        try:
            # Asignar valores con validación
            for key, value in data.items():
                if hasattr(self, key) and key != 'id_tienda':  # No permitir cambiar el ID
                    setattr(self, key, value)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al actualizar tienda: {str(e)}')
    
    def __repr__(self):
        return f'<Tienda {self.nombre}>'