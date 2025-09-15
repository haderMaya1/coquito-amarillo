from flask import Blueprint, render_template, redirect, flash, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        # Redirigir según el rol del usuario
        if current_user.rol.nombre == 'Administrador':
            return redirect(url_for('admin.dashboard'))
        elif current_user.rol.nombre == 'Vendedor':
            return redirect(url_for('dashboard.dashboard'))
        elif current_user.rol.nombre == 'Proveedor':
            if current_user.empleado_asociado and current_user.empleado_asociado.proveedor:
                return redirect(url_for('suppliers.view_supplier', supplier_id=current_user.empleado_asociado.proveedor_id))
            else:
                flash('Usuario proveedor no tiene empleado asociado', 'danger')
                return redirect(url_for('dashboard.dashboard'))
    return render_template('main/index.html')

@main_bp.route('/unauthorized')
def unauthorized():
    return render_template('errors/403.html'), 403