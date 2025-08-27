from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Role
from app.utils.decorators import admin_required
from sqlalchemy.exc import IntegrityError
from app.forms import UserForm, RolForm, ConfirmDeleteForm
from app.utils.security import sanitize_form_data

admin_bp = Blueprint('admin', __name__)

# En app/routes/admin.py
@admin_bp.route('/test-relation')
@login_required
@admin_required
def test_relation():
    # Probar la relación usuario-rol
    user = User.query.first()
    if user:
        return f"Usuario: {user.nombre}, Rol: {user.rol.nombre}"
    return "No hay usuarios"

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
    
    if mostrar_inactivos:
        users = User.get_todos().all()
    else:
        users = User.get_activos().all()
    
    return render_template('admin/users.html', users=users, mostrar_inactivos=mostrar_inactivos)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserForm()
    
    #Cargar roles
    roles = Role.query.all()
    form.rol_id.choices = [(role.id_rol, role.nombre) for role in roles]
    
    if form.validate_on_submit():
        try:
            email = form.email.data
            if User.query.filter_by(email=email).first():
                flash('El email ya está registrado', 'danger')
                return redirect(url_for('admin.create_user'), form=form, roles=roles)
            
            sanitize_data = sanitize_form_data(form.data)
            
            nuevo_usuario = User(
                nombre = sanitize_data['nombre'],
                email = sanitize_data['email'],
                password = sanitize_data['password'],
                rol_id = sanitize_data['rol_id'],
                activo = sanitize_data['activo']
            )
            
            if not form.activo.data:
                nuevo_usuario.fecha_eliminacion = form.fecha_eliminacion.data
            else:
                nuevo_usuario.fecha_eliminacion = None
                
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('admin.manage_users'))
        
        except IntegrityError:
            db.session.rollback()
            flash('Error: Violación de integridad en base de datos', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'error')
        
    return render_template('admin/create_user.html', form=form, roles=roles)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    form = UserForm()
    
    #Cargar roles
    roles = Role.query.all()
    form.rol_id.choices = [(role.id_rol, role.nombre) for role in roles]
    
    actualizar_usuario = User.query.get_or_404(user_id)
    
    if form.validate_on_submit():
        try:
            sanitize_data = sanitize_form_data(form.data)
                
            actualizar_usuario.nombre = sanitize_data['nombre']
            actualizar_usuario.email = sanitize_data['email']
            actualizar_usuario.rol_id = sanitize_data['rol_id']
            actualizar_usuario.activo = sanitize_data['activo']
            
            if User.query.filter(User.email == form.email.data, User.id_usuario != actualizar_usuario.id_usuario).first():
                flash('El nombre ya está registrado en otro cliente', 'danger')
                return redirect(url_for('admin.edit_user', user_id=actualizar_usuario.id_usuario))
            
            new_password = sanitize_data.get('new_password')    
            if new_password:
                actualizar_usuario.password(new_password)
                    
            if not form.activo.data:
                actualizar_usuario.fecha_eliminacion = form.fecha_eliminacion.data
            else:
                actualizar_usuario.fecha_eliminacion = None
                
            db.session.commit()
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('admin.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'error')
        
    return render_template('admin/edit_user.html', usuario=actualizar_usuario, roles=roles)  
    
@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(user_id)

        if user.id_usuario == current_user.id_usuario:
            flash('No puedes desactivar tu propia cuenta', 'danger')
            return redirect(url_for('admin.manage_users'))

        try:
            user.desactivar()
            flash('Usuario desactivado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al desactivar usuario: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.activo:
        flash('El usuario ya está activo', 'info')
        return redirect(url_for('admin.manage_users'))      
    
    try:
        user.activar()
        flash('Usuario reactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar el usuario: {str(e)}', 'danger')
        
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/roles')
@login_required
@admin_required
def manage_roles():
    mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
    
    if mostrar_inactivos:
        roles = Role.get_todos().all()
    else:
        roles = Role.get_activos().all()
        
    return render_template('admin/roles.html', roles=roles, mostrar_inactivos = mostrar_inactivos)

@admin_bp.route('/roles/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_role():
    form = RolForm()
    
    if form.validate_on_submit():
        try:
            nombre = form.nombre.data
            if Role.query.filter_by(nombre=nombre).firts():
                flash('El rol ya existe', 'danger')
                return redirect(url_for('admin.create_role'))
            
            sanitize_data = sanitize_form_data(form.data)
            
            nuevo_rol = Role(
                nombre = sanitize_data['nombre'],
                descripcion = sanitize_data['description'],
                activo = sanitize_data['activo']
            )
            
            if not form.activo.data:
                nuevo_rol.fecha_eliminacion = form.fecha_eliminacion.data
            else:
                nuevo_rol.fecha_eliminacion = None
            
            db.session.add(nuevo_rol)
            db.session.commit()
            
            flash('Rol creado exitosamente', 'success')
            return redirect(url_for('admin.manage_role'))
        
        except IntegrityError:
            db.session.rollback()
            flash('Error: Violación de integridad en base de datos', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear Rol: {str(e)}', 'error')
        
    return render_template('admin/create_role.html')

@admin_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RolForm()
    
    if form.validate_on_submit():
        try:
            sanitize_data = sanitize_form_data(form.data)
            
            role.nombre = sanitize_data['nombre']
            role.descripcion = sanitize_data['descripcion']
            
            if Role.query.filter(Role.nombre == form.nombre.data, Role.id_rol != Role.id_rol).first():
                flash('El nombre ya está registrado en otro Rol', 'danger')
                return redirect(url_for('admin.edit_role', role_id=role_id.id_rol))
            
            if not form.activo.data:
                role.fecha_eliminacion = form.fecha_eliminacion.data
            else:
                role.fecha_eliminacion = None
                
            db.session.commit()
            flash('Rol actualizado exitosamente', 'success')
            return redirect(url_for('admin.manage_roles'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear Rol: {str(e)}', 'error')
            
    return render_template('admin/edit_role.html', role=role, form=form)

@admin_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        # Verificar si hay usuarios con este rol
        try:
            if role.usuarios:
                flash('No se puede eliminar el rol porque hay usuarios asignados a él', 'danger')
                return redirect(url_for('admin.manage_roles'))
        
            role.desactivar()
            flash('Rol desactivado exitosamente', 'success')
        except Exception as e:
            flash(f'Error al desactivar rol: {str(e)}', 'danger')
            
    return redirect(url_for('admin.manage_roles'))

@admin_bp.route('/roles/<int:role_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_role(role_id):
    role = Role.query.get_or_404(role_id)
    
    if role.activo:
        flash('El rol ya está activo', 'info')
        return redirect(url_for('admin.manage_roles'))
    
    try:
        role.activar()
        flash('Rol reactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar el rol: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_roles'))

""""""
"CODIGOS ANTIGUOS NO FORMS, NO TOCAR"
""""""
"""Código anterior para crear usuario NO TOCAR"""
    # if request.method == 'POST':
    #     nombre = request.form.get('nombre')
    #     email = request.form.get('email')
    #     password = request.form.get('password')
    #     rol_id = request.form.get('rol_id')
        
    #     # Verificar si el usuario ya existe
    #     if User.query.filter_by(email=email).first():
    #         flash('El email ya está registrado', 'danger')
    #         return redirect(url_for('admin.create_user'))
        
    #     # Crear nuevo usuario
    #     nuevo_usuario = User(
    #         nombre=nombre,
    #         email=email,
    #         rol_id=rol_id
    #     )
    #     nuevo_usuario.set_password(password)
        
    #     db.session.add(nuevo_usuario)
    #     db.session.commit()
        
    #     flash('Usuario registrado exitosamente', 'success')
    #     return redirect(url_for('admin.manage_users'))
    
    # roles = Role.query.all()
    # return render_template('admin/create_user.html', roles=roles)
    
""""""
""""""
"""Codigo anterior para editar Usuario"""
    # user = User.query.get_or_404(user_id)
    
    # if request.method == 'POST':
    #     user.nombre = request.form.get('nombre')
    #     user.email = request.form.get('email')
    #     user.rol_id = request.form.get('rol_id')
        
    #     # Si se proporciona una nueva contraseña, actualizarla
    #     new_password = request.form.get('new_password')
    #     if new_password:
    #         user.set_password(new_password)
        
    #     db.session.commit()
    #     flash('Usuario actualizado exitosamente', 'success')
    #     return redirect(url_for('admin.manage_users'))
    
    # roles = Role.get.activos().all()
    # return render_template('admin/edit_user.html', user=user, roles=roles)

""""""
""""""
"""Codigo anterior para eliminar Usuario"""
    # user = User.query.get_or_404(user_id)   
    
    # # No permitir eliminar el propio usuario
    # if user.id_usuario == current_user.id_usuario:
    #     flash('No puedes desactivar tu propia cuenta', 'danger')
    #     return redirect(url_for('admin.manage_users'))
    
    # try:
    #     # Soft delete
    #     user.desactivar()
    #     flash('Usuario eliminado exitosamente', 'success')
    # except Exception as e:
    #     db.session.rollback()
    #     flash(f'Error al desactivar usuario: {str(e)}', 'danger')
        
    # return redirect(url_for('admin.manage_users'))

""""""
""""""
"""Codigo anterior para crear rol"""
    # if request.method == 'POST':
    #     nombre = request.form.get('nombre')
    #     descripcion = request.form.get('descripcion')
        
    #     if Role.query.filter_by(nombre=nombre).first():
    #         flash('El rol ya existe', 'danger')
    #         return redirect(url_for('admin.create_role'))
        
    #     nuevo_rol = Role(nombre=nombre, descripcion=descripcion)
    #     db.session.add(nuevo_rol)
    #     db.session.commit()
        
    #     flash('Rol creado exitosamente', 'success')
    #     return redirect(url_for('admin.manage_roles'))
    
    # return render_template('admin/create_role.html')