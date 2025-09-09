from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.models import User, Role
from app.forms import LoginForm, RegisterForm, ChangePasswordForm, ProfileForm
from app.utils.decorators import admin_required, login_required
from app.utils.security import sanitize_form_data
from app import bcrypt, db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if not current_user.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
            logout_user()
            return redirect(url_for('auth.login'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            email = form.email.data.strip()
            password = form.password.data
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if not user.activo:
                    flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                    return render_template('auth/login.html', form=form)
                
                login_user(user)
                next_page = request.args.get('next')
                
                # Validar que next_page sea una URL segura (mismo sitio)
                if next_page and not next_page.startswith('/'):
                    next_page = None
                
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
                        return redirect(url_for('auth.logout'))
                else:
                    flash('Tu rol no está configurado correctamente.', 'danger')
                    return redirect(url_for('main.index'))
            else:
                # No revelar si el email existe o no por seguridad
                flash('Credenciales incorrectas', 'danger')
                
        except SQLAlchemyError as e:
            flash('Error en la base de datos durante el inicio de sesión', 'danger')
            
        except Exception as e:
            flash(f'Error durante el inicio de sesión: {str(e)}', 'danger')
    
    elif request.method == 'POST':
        # Si el formulario no pasa la validación, mostrar errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    form = RegisterForm()
    
    # Cargar opciones para el campo de rol
    form.rol_id.choices = [(r.id_rol, r.nombre) for r in Role.query.all()]
    
    if form.validate_on_submit():
        try:
            # Sanitizar los datos del formulario
            
            nombre = form.nombre.data.strip()
            email = form.email.data.strip().lower()
            password = form.password.data
            rol_id = form.rol_id.data
            
            # Verificar si el usuario ya existe
            if User.query.filter_by(email=email).first():
                flash('El email ya está registrado', 'danger')
                return render_template('auth/register.html', form=form)
            
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
        
        except IntegrityError:
            db.session.rollback()
            flash('Error de base de datos al registrar usuario', 'danger')
            
        except SQLAlchemyError as e:
            flash('Error en la base de datos durante el inicio de sesión', 'danger')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar usuario: {str(e)}', 'danger')
    
    elif request.method == 'POST':
        # Si el formulario no pasa la validación, mostrar errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        try:
            current_password = form.current_password.data
            new_password = form.new_password.data
            confirm_password = form.confirm_password.data
            
            # Verificar que la contraseña actual sea correcta
            if not current_user.check_password(current_password):
                flash('La contraseña actual es incorrecta', 'danger')
                return render_template('auth/change_password.html', form=form)
            
            # Verificar que las nuevas contraseñas coincidan
            if new_password != confirm_password:
                flash('Las nuevas contraseñas no coinciden', 'danger')
                return render_template('auth/change_password.html', form=form)
            
            # Actualizar la contraseña
            current_user.set_password(new_password)
            db.session.commit()
            
            flash('Contraseña actualizada exitosamente', 'success')
            return redirect(url_for('dashboard.dashboard'))
        
        except SQLAlchemyError as e:
            flash('Error en la base de datos durante el inicio de sesión', 'danger')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al cambiar la contraseña: {str(e)}', 'danger')
    
    elif request.method == 'POST':
        # Si el formulario no pasa la validación, mostrar errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # Implementación básica de recuperación de contraseña
    flash('Funcionalidad de recuperación de contraseña en desarrollo', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        try:
            # Sanitizar los datos del formulario
            current_user.nombre = form.nombre.data.strip()
            current_user.email = form.email.data.strip().lower
            
            db.session.commit()
            flash('Perfil actualizado exitosamente', 'success')
            return redirect(url_for('auth.profile'))
        
        except IntegrityError:
            db.session.rollback()
            flash('El email ya está registrado por otro usuario', 'danger')
        
        except SQLAlchemyError:
            db.session.rollback()
            flash('Error de base de datos al actualizar perfil', 'danger')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')
    
    elif request.method == 'POST':
        # Si el formulario no pasa la validación, mostrar errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return render_template('auth/profile.html', form=form)