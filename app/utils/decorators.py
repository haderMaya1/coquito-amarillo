from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor inicia sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.rol.nombre != role_name:
                flash('No tienes permisos suficientes para acceder a esta página.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('Administrador')(f)

def seller_required(f):
    return role_required('Vendedor')(f)

def supplier_required(f):
    return role_required('Proveedor')(f)

# Decorador para múltiples roles
def roles_required(*role_names):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor inicia sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.rol.nombre not in role_names:
                flash('No tienes permisos suficientes para acceder a esta página.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator