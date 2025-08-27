# app/models/user.py
from flask_login import UserMixin
from app import db, bcrypt
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    activo = db.Column(db.Boolean, default=True)  # Campo para soft delete
    fecha_eliminacion = db.Column(db.DateTime)    # Fecha de desactivación
     
    #Relación con Rol y Empleado
    rol = relationship('Role', back_populates='usuarios')
    empleado = relationship('Staff', back_populates='usuario', uselist=False, cascade='all, delete-orphan')
    
    def get_id(self):
        return str(self.id_usuario)
    
    #Propiedades
    @property
    def password(self):
        raise AttributeError('La contraseña no es legible')
    
    @password.setter
    def password(self, raw_password):
        self.validate_password_strength(raw_password)
        self._password_hash = bcrypt.generate_password_hash(raw_password).decode('utf-8')
    
    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password, raw_password)
    
    def validate_password_strength(self, password):
        """Valida la fortaleza de la contraseña"""
        if len(password) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', password):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not re.search(r'[a-z]', password):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not re.search(r'\d', password):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('La contraseña debe contener al menos un carácter especial')
    
    def desactivar(self):
        """Marca el usuario como inactivo (soft delete)"""
        self.activo = False
        self.fecha_eliminacion = datetime.utcnow()
        db.session.commit()
    
    def activar(self):
        """Reactiva un usuario previamente desactivado"""
        self.activo = True
        self.fecha_eliminacion = None
        db.session.commit()
    
    @classmethod
    def get_activos(cls):
        """Obtiene solo los usuarios activos"""
        return cls.query.filter_by(activo=True)
    
    @classmethod
    def get_inactivos(cls):
        """Obtiene solo los usuarios inactivos"""
        return cls.query.filter_by(activo=False)
    
    @classmethod
    def get_todos(cls):
        """Obtiene todos los usuarios, activos e inactivos"""
        return cls.query
    
    #Validaciones
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        if not re.match(r'^[\w\sáéíóúÁÉÍÓÚñÑ]+$', nombre):
            raise ValueError('El nombre solo puede contener letras, números y guiones bajos')
        return nombre
    
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Email invalido')
        return email
    
    def __repr__(self):
        return f'<User {self.nombre}>'
    