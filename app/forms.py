from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, DecimalField, IntegerField, DateTimeField, BooleanField, SelectField, SubmitField, RadioField, DateField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo
from wtforms import ValidationError
from datetime import datetime
import re

class BaseForm(FlaskForm):
    """Formulario base con validaciones comunes"""
    
    def validate_safe_string(self, field):
        """Validar que no contenga caracteres peligrosos"""
        dangerous_patterns = [
            r'<script', r'javascript:', r'onload=', r'onerror=',
            r'union.*select', r'drop.*table', r';.*--'
        ]
        value = field.data or ''
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError('El texto contiene caracteres no permitidos')
            
class EmptyForm(FlaskForm):
    pass
class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField('Confirmar eliminación')
    
#----------Usuario-------------
class UserForm(BaseForm):
    nombre = StringField('Usuario', validators=[
        DataRequired(message='El nombre de usuario es requerido'),
        Length(min=3, max=100, message='Debe tener entre 3 y 100 caracteres')
    ])
    
    email = EmailField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Debe ser un email válido')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        Length(min=8, message='Debe tener almenos 8 caracteres')
    ])
    
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Por favor confirma tu contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    
    rol_id = SelectField('Rol', coerce=int, validators=[
        DataRequired(message='Escoge un rol')
    ])
    
    activo =  BooleanField('Estado')
    
    fecha_eliminacion = DateTimeField('Fecha de Desactivacion', format='%Y-%m-%d %H:%M')
    
    fecha_registro = DateTimeField('Fecha de Registro', format='%Y-%m-%d %H:%M')
    
    submit = SubmitField('Guardar')

#------------Roles--------------
class RolForm(BaseForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=50, message='Debe tener entre 2 y 50 caracteres')
    ])
    
    descripcion = StringField('Descripcion', validators=[
        Optional(),
        Length(min=2, max=150, message='Debe tener entre 2 a 150 caracteres')
    ])
    
    activo = BooleanField('Estado')
    
    submit = SubmitField('Guardar')
    
#----------Producto-------------
class ProductForm(BaseForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    
    categoria = StringField('Categoria', validators=[
        DataRequired(message='La categoria es requerida'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    
    descripcion = StringField('Descripcion', validators=[
        Optional(),
        Length(min=2, max=150, message='Debe tener entre 2 a 150 caracteres')
    ])
    
    precio = DecimalField('Precio', validators=[
        DataRequired(message='El precio es requerido'),
        NumberRange(min=0, message='El precio no puede ser negativo')
    ])
    
    stock = IntegerField('Stock', validators=[
        DataRequired(message='El stock es requerido'),
        NumberRange(min=0, message='El stock no puede ser negativo')
    ])
    
    proveedor_id = SelectField('Proveedor', coerce=int, validators=[
        DataRequired(message='Debe seleccionar un proveedor')
    ])
    
    activo =  BooleanField('Estado')
    
    fecha_eliminacion = DateTimeField('Fecha de Desactivacion', format='%Y-%m-%d %H:%M')
    
    submit = SubmitField('Guardar')

#----------Stock-------------
class StockForm(FlaskForm):
    accion = RadioField('Acción', choices=[
        ('aumentar', 'Aumentar'),
        ('reducir', 'Reducir')
    ], validators=[DataRequired(message='Debe seleccionar una acción')])
    
    cantidad = IntegerField('Cantidad', validators=[
        DataRequired(message='Debe ingresar una cantidad'),
        NumberRange(min=1, message='La cantidad debe ser al menos 1')
    ])
    
    submit = SubmitField('Actualizar stock')

#----------Cliente-------------

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre de cliente es requerido'),
        Length(min=3, max=100, message='Debe tener entre 3 y 100 caracteres')
    ])
    
    direccion = StringField('Direccion', validators=[
        Optional(),
        Length(min=3, max=150, message='Debe tener entre 3 y 150 caracteres')
    ])
    
    telefono = StringField('Telefono', validators=[
        DataRequired(message='Ingrese un telefono para comunicacion con el cliente'),
        Length(min=3, max=15, message='Debe tener entre 3 y 15 caracteres')
    ])
    ciudad_id = SelectField('ciudad_id', coerce=int, validators=[
        DataRequired(message='Escoge una ciudad')
    ])
    
    activo = BooleanField('Estado')
    
    fecha_eliminacion = DateTimeField('Fecha de Desactivacion', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    submit = SubmitField('Guardar')
#----------Ciudad-------------

class CiudadForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre de la ciudad es necesario'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    
    activo =  BooleanField('Estado')
    
    fecha_eliminacion = DateTimeField('Fecha de Desactivacion', format='%Y-%m-%d %H:%M')
    
    submit = SubmitField('Guardar')
    
class SaleForm(FlaskForm):
    fecha = DateTimeField(
        'Fecha de la venta',
        format='%Y-%m-%d %H:%M',
        default=datetime.utcnow,
        validators=[DataRequired(message='La fecha de la venta es obligatoria')]
    )

    total = DecimalField(
        'Total',
        places=2,
        validators=[
            DataRequired(message='El total de la venta es obligatorio'),
            NumberRange(min=0, message='El total debe ser mayor o igual a 0')
        ]
    )

    estado = SelectField(
        'Estado',
        choices=[('activa', 'Activa'), ('anulada', 'Anulada')], default='activa',  # 👈 corregido, debe ser lista de tuplas
        validators=[Optional()]
    )

    activo = BooleanField('Estado')

    cliente_id = SelectField(
        'Cliente',
        coerce=int,
        choices=[],   # 👈 importante
        validators=[Optional()]
    )

    empleado_id = SelectField(
        'Empleado',
        coerce=int,
        choices=[],   # 👈 importante
        validators=[Optional()]
    )

    tienda_id = SelectField(
        'Tienda',
        coerce=int,
        choices=[],   # 👈 importante
        validators=[Optional()]
    )

    submit = SubmitField('Guardar Venta')

#-----------Venta producto--------------
class SaleProductForm(FlaskForm):
    id_venta = SelectField('Venta', coerce = int,
                           validators=[
                               DataRequired(message='Debe seleccinar una venta')
                           ])
    
    id_producto = SelectField(
        'Producto', coerce = int,
        validators=[DataRequired(message='Debe seleccionar un producto')]
    )
    
    cantidad = IntegerField(
        'Cantidad',
        validators=[
            DataRequired(message='Debe indicar la cantidad'),
            NumberRange(min=1, message='La cantidad debe ser al menos 1')
        ]
    )
    
    precio_unitario = DecimalField(
        'Precio unitario',
        places=2,
        validators=[
            DataRequired(message='Debe indicar el subtotal'),
            NumberRange(min=0, message='El subtotal debe ser mayor o igual a 0')
        ]
    )
    
    submit = SubmitField('Agregar Producto a Venta')
    
#-----------Factura--------------
class InvoiceForm(FlaskForm):
    fecha = DateTimeField(
        'Fecha de Factura',
        format='%Y-%m-%d %H:%M',
        default=datetime.utcnow,
        validators=[DataRequired(message='La fecha es obligatoria')]
    )
    
    total = DecimalField(
        'Total',
        places=2,
        validators=[
            DataRequired(message='Debe indicar el total'),
            NumberRange(min=0, message='El total debe ser mayor o igual a 0')
        ]
    )
    
    venta_id = SelectField(
        'Venta', coerce =int,
        validators=[DataRequired(message='Debe asociar esta factura a una venta')]
    )
    
    submit = SubmitField('Guardar Factura')
    
#-----------orden cliente--------------
class ClientOrderForm(FlaskForm):
    fecha = DateTimeField(
        'Fecha de la Orden',
        format='%Y-%m-%d',
        default=datetime.utcnow,
        validators=[DataRequired(message='Debe indicar la fecha de la orden')]
    )
    
    estado = SelectField(
        'Estado', choices=[
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')],
        validators=[
            DataRequired(message='El estado de la orden es obligatorio'),
            Length(min=3, max=50, message='Debe tener entre 3 y 50 caracteres')
        ]
    )
    
    descripcion = StringField('Descripcion', validators=[
        Optional(),
        Length(min=2, max=150, message='Debe tener entre 2 a 150 caracteres')
    ])
    

    submit = SubmitField('Guardar Orden de Cliente')
    
#-----------Cliente orden producto--------------
class ClientOrderProductForm(FlaskForm):
    id_orden_cliente = IntegerField(
        'Orden de Cliente',
        validators=[DataRequired(message='Debe asociar un pedido de cliente')]
    )
    
    id_producto = SelectField(
        'Producto', coerce=int,
        validators=[DataRequired(message='Debe seleccionar un producto')]
    )
    
    cantidad = IntegerField(
        'Cantidad',
        validators=[
            DataRequired(message='Debe indicar la cantidad'),
            NumberRange(min=1, message='La cantidad debe ser al menos 1')
        ]
    )
    
    submit = SubmitField('Agregar Producto a Orden')

#----------Proveedor------------
class SupplierForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(max=100, message="Máximo 100 caracteres")
    ])
    
    contacto = StringField('Contacto', validators=[
        Optional(),
        Length(max=100, message="Máximo 100 caracteres")
    ])
    
    ciudad_id = SelectField('Ciudad', coerce=int, validators=[Optional()])
    
    activo = BooleanField('Activo', default=True)
    
    fecha_eliminacion = DateTimeField('Fecha de Desactivacion', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    submit = SubmitField('Guardar')
    
#-------------Orden proveedor-------------
class SupplierOrderForm(FlaskForm):
    proveedor_id = SelectField('Proveedor', coerce=int, validators=[
        DataRequired(message="El proveedor es obligatorio")
    ])
    
    fecha = DateTimeField(
        'Fecha de la Orden',
        format='%Y-%m-%d',
        default=datetime.utcnow,
        validators=[DataRequired(message='Debe indicar la fecha de la orden')]
    )
    
    estado = SelectField('Estado', choices=[
        ('pendiente', 'Pendiente'),
        ('recibida', 'Recibida'),
        ('cancelada', 'Cancelada')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Guardar')
    
#----------Orden, Producto proveedor---------
class SupplierOrderProductForm(FlaskForm):
    id_orden_proveedor = SelectField('Orden de Proveedor', coerce=int, validators=[
        DataRequired(message="Debe seleccionar un producto")
    ])
    
    id_producto = SelectField('Producto', coerce=int, validators=[
        DataRequired(message="Debe seleccionar un producto")
    ])
    
    cantidad = IntegerField('Cantidad', validators=[
        DataRequired(message="La cantidad es obligatoria"),
        NumberRange(min=1, message="Debe ingresar al menos 1 unidad")
    ])
    
    submit = SubmitField('Agregar Producto')

#-------------Personal----------------
class StaffForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    cargo = StringField('Cargo', validators=[
        Optional(),
        Length(max=100, message='No puede exceder 100 caracteres')
    ])
    salario = DecimalField('Salario', validators=[
        Optional(),
        NumberRange(min=0, message='El salario no puede ser negativo')
    ])
    ciudad_id = SelectField('Ciudad', coerce=int, validators=[
        DataRequired(message='La ciudad es requerida')
    ])
    tienda_id = SelectField('Tienda', coerce=int, validators=[
        Optional()
    ])
    usuario_id = SelectField('Usuario', coerce=int, validators=[
        Optional()
    ])
    proveedor_id = SelectField('Proveedor', coerce=int, validators=[
        Optional()
    ])
    
    activo = BooleanField('Activo', default=True)
    
    fecha_eliminacion = DateTimeField('Fecha de Desactivacion', format='%Y-%m-%d %H:%M', validators=[Optional()])
    
    submit = SubmitField('Guardar')

#------------Tienda----------------
class StoreForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    direccion = StringField('Dirección', validators=[
        Optional(),
        Length(max=150, message='No puede exceder 150 caracteres')
    ])
    ciudad_id = SelectField('Ciudad', coerce=int, validators=[
        DataRequired(message='La ciudad es requerida')
    ])
    
    activo = BooleanField('Activo', default=True)
    
    submit = SubmitField('Guardar')

#--------------Login---------------------
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Debe ser un email válido')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida')
    ])
    
    submit = SubmitField('Guardar')

#----------------Registro-----------------
class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Debe ser un email válido')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        Length(min=8, message='Debe tener al menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Debe confirmar la contraseña'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    rol_id = SelectField('Rol', coerce=int, validators=[
        DataRequired(message='El rol es requerido')
    ])
    
    submit = SubmitField('Guardar')

#-----------Cambiar Contraseña-------------
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña Actual', validators=[
        DataRequired(message='La contraseña actual es requerida')
    ])
    new_password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(message='La nueva contraseña es requerida'),
        Length(min=8, message='Debe tener al menos 8 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[
        DataRequired(message='Debe confirmar la nueva contraseña'),
        EqualTo('new_password', message='Las contraseñas no coinciden')
    ])
    
    submit = SubmitField('Guardar')
# ... (otros formularios existentes)
class ProfileForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=100, message='Debe tener entre 2 y 100 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Debe ser un email válido')
    ])
    
    submit = SubmitField('Guardar')

class DateRangeForm(FlaskForm):
    """Formulario para seleccionar un rango de fechas."""
    start_date = DateField('Fecha de inicio', validators=[Optional()])
    end_date = DateField('Fecha de fin', validators=[Optional()])
    submit = SubmitField('Filtrar')
    
    submit = SubmitField('Guardar')

class SalesFilterForm(FlaskForm):
    """Formulario para filtrar y agrupar ventas."""
    start_date = DateField('Fecha de inicio', validators=[Optional()])
    end_date = DateField('Fecha de fin', validators=[Optional()])
    group_by = SelectField(
        'Agrupar por',
        choices=[
            ('day', 'Día'),
            ('week', 'Semana'),
            ('month', 'Mes')
        ],
        default='day',
        validators=[DataRequired()]
    )
    submit = SubmitField('Aplicar Filtro')

class QuickStatsForm(FlaskForm):
    """Formulario para seleccionar períodos rápidos de estadísticas."""
    period = SelectField(
        'Seleccionar Período',
        choices=[
            ('today', 'Hoy'),
            ('last_7_days', 'Últimos 7 días'),
            ('last_30_days', 'Últimos 30 días'),
            ('this_month', 'Este mes'),
            ('this_year', 'Este año')
        ],
        default='last_7_days',
        validators=[DataRequired()]
    )
    submit = SubmitField('Actualizar')