from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re
from sqlalchemy.exc import IntegrityError

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
    
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        """Validar que el nombre solo contenga letras, espacios y algunos caracteres especiales"""
        if not nombre or not nombre.strip():
            raise ValueError('El nombre no puede estar vacío')
        
        if len(nombre) > 100:
            raise ValueError('El nombre no puede exceder 100 caracteres')
        
        # Permitir letras, espacios, apóstrofes, guiones y algunos caracteres especiales comunes en nombres
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\'\-\.]+$', nombre):
            raise ValueError('El nombre contiene caracteres no válidos')
        
        return nombre.strip()
    
    @validates('cargo')
    def validate_cargo(self, key, cargo):
        """Validar el campo cargo"""
        if cargo is not None:
            if len(cargo) > 100:
                raise ValueError('El cargo no puede exceder 100 caracteres')
            
            # Validar que el cargo no contenga caracteres potencialmente peligrosos
            dangerous_patterns = [
                r'<script', r'javascript:', r'onload=', r'onerror=',
                r'union.*select', r'drop.*table', r';.*--'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, cargo, re.IGNORECASE):
                    raise ValueError('El cargo contiene texto no permitido')
        
        return cargo
    
    @validates('salario')
    def validate_salario(self, key, salario):
        """Validar que el salario sea un valor positivo"""
        if salario is not None:
            try:
                salario = float(salario)
                if salario < 0:
                    raise ValueError('El salario no puede ser negativo')
                if salario > 99999999.99:  # Límite basado en la precisión de la columna (10,2)
                    raise ValueError('El salario excede el valor máximo permitido')
            except (ValueError, TypeError):
                raise ValueError('El salario debe ser un valor numérico válido')
        
        return salario
    
    @validates('usuario_id')
    def validate_usuario_id(self, key, usuario_id):
        """Validar que el usuario_id sea único si está presente"""
        if usuario_id is not None:
            # Verificar si ya existe otro empleado con este usuario_id
            existing = Staff.query.filter(
                Staff.usuario_id == usuario_id,
                Staff.id_empleado != self.id_empleado  # Excluir el registro actual en updates
            ).first()
            
            if existing:
                raise ValueError('Este usuario ya está asociado a otro empleado')
        
        return usuario_id
    
    @validates('proveedor_id')
    def validate_proveedor_id(self, key, proveedor_id):
        """Validar la relación con proveedor"""
        if proveedor_id is not None and self.tienda_id is not None:
            raise ValueError('Un empleado no puede estar asociado a un proveedor y a una tienda simultáneamente')
        
        return proveedor_id
    
    @validates('tienda_id')
    def validate_tienda_id(self, key, tienda_id):
        """Validar la relación con tienda"""
        if tienda_id is not None and self.proveedor_id is not None:
            raise ValueError('Un empleado no puede estar asociado a una tienda y a un proveedor simultáneamente')
        
        return tienda_id
    
    def desactivar(self):
        """Marca el empleado como inactivo (soft delete)"""
        try:
            self.activo = False
            self.fecha_eliminacion = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al desactivar empleado: {str(e)}')
    
    def activar(self):
        """Reactiva un empleado previamente desactivado"""
        try:
            self.activo = True
            self.fecha_eliminacion = None
            db.session.commit()
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
    
    @classmethod
    def create_from_dict(cls, data):
        """Crea un nuevo empleado desde un diccionario con validación"""
        try:
            empleado = cls()
            
            # Asignar valores con validación
            for key, value in data.items():
                if hasattr(empleado, key):
                    setattr(empleado, key, value)
            
            db.session.add(empleado)
            db.session.commit()
            return empleado
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al crear empleado: {str(e)}')
    
    def update_from_dict(self, data):
        """Actualiza el empleado desde un diccionario con validación"""
        try:
            # Asignar valores con validación
            for key, value in data.items():
                if hasattr(self, key) and key != 'id_empleado':  # No permitir cambiar el ID
                    setattr(self, key, value)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error al actualizar empleado: {str(e)}')
    
    def __repr__(self):
        return f'<Empleado {self.nombre}>'