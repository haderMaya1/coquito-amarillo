from functools import wraps
from flask import flash, redirect, url_for, abort, request
from flask_login import current_user, login_required as flask_login_required

def login_required(f):
    """
    Decorador que verifica si el usuario está autenticado.
    Versión mejorada del login_required de Flask-Login con mensajes flash.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Decorador que verifica si el usuario tiene un rol específico.
    """
    def decorator(f):
        @wraps(f)
        @login_required  # Asegura que el usuario esté autenticado primero
        def decorated_function(*args, **kwargs):
            # Verificar si el usuario tiene el rol requerido
            if not hasattr(current_user, 'rol') or not current_user.rol:
                flash('Tu cuenta no tiene un rol asignado.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            if current_user.rol.nombre != role_name:
                flash('No tienes permisos suficientes para acceder a esta página.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorador específico para requerir rol de Administrador.
    """
    return role_required('Administrador')(f)

def seller_required(f):
    """
    Decorador específico para requerir rol de Vendedor.
    """
    return role_required('Vendedor')(f)

def supplier_required(f):
    """
    Decorador específico para requerir rol de Proveedor.
    """
    return role_required('Proveedor')(f)

def roles_required(*role_names):
    """
    Decorador que verifica si el usuario tiene al menos uno de los roles especificados.
    """
    def decorator(f):
        @wraps(f)
        @login_required  # Asegura que el usuario esté autenticado primero
        def decorated_function(*args, **kwargs):
            # Verificar si el usuario tiene al menos uno de los roles requeridos
            if not hasattr(current_user, 'rol') or not current_user.rol:
                flash('Tu cuenta no tiene un rol asignado.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            if current_user.rol.nombre not in role_names:
                flash('No tienes permisos suficientes para acceder a esta página.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def active_user_required(f):
    """
    Decorador que verifica si el usuario está activo.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.logout'))  # Cerrar sesión forzadamente
        return f(*args, **kwargs)
    return decorated_function

def api_role_required(role_name):
    """
    Versión para API del decorador role_required que devuelve JSON en lugar de redireccionar.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'rol') or not current_user.rol:
                return {'error': 'Tu cuenta no tiene un rol asignado.'}, 403
            
            if current_user.rol.nombre != role_name:
                return {'error': 'No tienes permisos suficientes para acceder a este recurso.'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_roles_required(*role_names):
    """
    Versión para API del decorador roles_required que devuelve JSON en lugar de redireccionar.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'rol') or not current_user.rol:
                return {'error': 'Tu cuenta no tiene un rol asignado.'}, 403
            
            if current_user.rol.nombre not in role_names:
                return {'error': 'No tienes permisos suficientes para acceder a este recurso.'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Alias para compatibilidad con versiones anteriores
admin_required = role_required('Administrador')
seller_required = role_required('Vendedor')
supplier_required = role_required('Proveedor')