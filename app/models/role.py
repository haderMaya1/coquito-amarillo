# app/models/role.py
from app import db
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

class Role(db.Model):
    __tablename__ = 'roles'

    id_rol = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(150))
    activo = db.Column(db.Boolean, default=True)
    fecha_eliminacion = db.Column(db.DateTime)

    # Relaciones (sin delete-orphan para NO borrar usuarios al tocar roles)
    usuarios = relationship('User', back_populates='rol',cascade='save-update, merge')

    def get_id(self):
        return str(self.id_rol)

    def desactivar(self):
        """Marca el rol como inactivo (soft delete). Commit fuera del modelo."""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
        return self

    def activar(self):
        """Reactiva un rol previamente desactivado. Commit fuera del modelo."""
        self.activo = True
        self.fecha_eliminacion = None
        return self

    @classmethod
    def get_activos(cls):
        return cls.query.filter_by(activo=True)

    @classmethod
    def get_inactivos(cls):
        return cls.query.filter_by(activo=False)

    @classmethod
    def get_todos(cls):
        return cls.query

    # Validaciones
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        if nombre is None:
            raise ValueError('El nombre es obligatorio')
        nombre = nombre.strip()
        # Letras, números, guion bajo, espacios y acentos
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ]+$', nombre):
            raise ValueError('El nombre solo puede contener letras, números, espacios y guiones bajos')
        return nombre

    @validates('descripcion')
    def validate_descripcion(self, key, descripcion):
        # Es opcional; si viene None, lo dejamos pasar
        if descripcion is None:
            return descripcion
        descripcion = descripcion.strip()
        if descripcion == '':
            return None
        # Texto con puntuación básica
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ.,:;()\-#]+$', descripcion):
            raise ValueError('La descripción contiene caracteres no permitidos')
        # Límite lógico acorde a la columna
        if len(descripcion) > 150:
            raise ValueError('La descripción no puede exceder 150 caracteres')
        return descripcion

    def __repr__(self):
        return f'<Role {self.nombre}>'