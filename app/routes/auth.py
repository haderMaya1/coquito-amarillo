from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.models import User, Role
from app.utils.decorators import admin_required
from app import bcrypt, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user)
            next_page = request.args.get('next')
            flash('Inicio de sesión exitoso', 'success')
            
            # Redirección según rol
            if user.rol.nombre == 'Administrador':
                return redirect(next_page or url_for('admin.dashboard'))
            elif user.rol.nombre == 'Vendedor':
                return redirect(next_page or url_for('dashboard.dashboard'))
            elif user.rol.nombre == 'Proveedor':
                # Verificar si el usuario tiene un empleado asociado con proveedor
                if user.empleado and user.empleado.proveedor:
                    return redirect(next_page or url_for('suppliers.view_supplier', supplier_id=user.empleado.proveedor_id))
                else:
                    flash('Usuario proveedor no tiene empleado asociado', 'danger')
                    return redirect(url_for('auth.login'))
            
            return redirect(next_page or url_for('dashboard.dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        rol_id = request.form.get('rol_id')
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('auth.register'))
        
        # Crear nuevo usuario
        nuevo_usuario = User(
            nombre=nombre,
            email=email,
            rol_id=rol_id
        )
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('admin.dashboard'))
    
    roles = Role.query.all()
    return render_template('auth/register.html', roles=roles)