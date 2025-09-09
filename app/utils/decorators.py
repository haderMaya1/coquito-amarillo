from functools import wraps
from flask import flash, redirect, url_for, abort, request
from flask_login import current_user

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
        
        # Verificar que el usuario esté activo
        if not getattr(current_user, 'activo', True):
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.logout'))
        
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Decorador que verifica si el usuario tiene un rol específico.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Verificar si el usuario tiene el rol requerido
            if not hasattr(current_user, 'rol') or not current_user.rol:
                flash('Tu cuenta no tiene un rol asignado.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            if current_user.rol.nombre != role_name:
                flash(f'Se requiere rol de {role_name} para acceder a esta página.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorador específico para requerir rol de Administrador.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'rol') or not current_user.rol:
            flash('Tu cuenta no tiene un rol asignado.', 'danger')
            return redirect(url_for('main.index'))
        
        if current_user.rol.nombre != 'Administrador':
            flash('Se requiere rol de Administrador para acceder a esta página.', 'danger')
            return redirect(url_for('main.unauthorized'))
        
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    """
    Decorador específico para requerir rol de Vendedor.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'rol') or not current_user.rol:
            flash('Tu cuenta no tiene un rol asignado.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        if current_user.rol.nombre != 'Vendedor':
            flash('Se requiere rol de Vendedor para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def supplier_required(f):
    """
    Decorador específico para requerir rol de Proveedor.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'rol') or not current_user.rol:
            flash('Tu cuenta no tiene un rol asignado.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        if current_user.rol.nombre != 'Proveedor':
            flash('Se requiere rol de Proveedor para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*role_names):
    """
    Decorador que verifica si el usuario tiene al menos uno de los roles especificados.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not hasattr(current_user, 'rol') or not current_user.rol:
                flash('Tu cuenta no tiene un rol asignado.', 'danger')
                return redirect(url_for('dashboard.dashboard'))
            
            if current_user.rol.nombre not in role_names:
                flash(f'Se requiere uno de los siguientes roles: {", ".join(role_names)}', 'danger')
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
        if not getattr(current_user, 'activo', True):
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated_function

# Versiones para API (sin cambios significativos)
def api_role_required(role_name):
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