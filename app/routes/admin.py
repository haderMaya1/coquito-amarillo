from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Role, Sale, Staff, Store
from app.utils.decorators import admin_required, active_user_required, roles_required
from sqlalchemy.exc import IntegrityError
from app.forms import UserForm, RolForm, ConfirmDeleteForm
from app.utils.security import sanitize_form_data
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

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
@active_user_required
def manage_users():
    """Gestión de usuarios"""
    try:
        mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
        
        if mostrar_inactivos:
            usuarios = User.query.all()
        else:
            usuarios = User.query.filter_by(activo=True).all()
        
        return render_template('admin/users.html', usuarios=usuarios, mostrar_inactivos=mostrar_inactivos)
    except Exception as e:
        flash(f'Error al cargar usuarios: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))
    
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

#----Codigos provenientes de auth, para prevenir errores de sobre-escritura

@admin_bp.route('/dashboard')
@login_required
@admin_required
@active_user_required
def dashboard():
    """Panel de control principal de administración"""
    try:
        # Estadísticas para el dashboard
        total_usuarios = User.query.count()
        total_empleados = Staff.get_activos().count()
        total_tiendas = Store.get_activas().count()
        total_productos = Product.get_activos().count()
        
        # Ventas de los últimos 7 días
        fecha_inicio = datetime.utcnow() - timedelta(days=7)
        ventas_recientes = Sale.query.filter(Sale.fecha_venta >= fecha_inicio).count()
        
        # Usuarios recientes (últimos 30 días)
        usuarios_recientes = User.query.filter(User.fecha_registro >= datetime.utcnow() - timedelta(days=30)).count()
        
        return render_template('admin/dashboard.html',
                             total_usuarios=total_usuarios,
                             total_empleados=total_empleados,
                             total_tiendas=total_tiendas,
                             total_productos=total_productos,
                             ventas_recientes=ventas_recientes,
                             usuarios_recientes=usuarios_recientes)
    except Exception as e:
        flash(f'Error al cargar el dashboard: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
@active_user_required
def toggle_user_status(user_id):
    """Activar/desactivar usuario"""
    try:
        usuario = User.query.get_or_404(user_id)
        
        if usuario.activo:
            usuario.activo = False
            flash('Usuario desactivado exitosamente', 'success')
        else:
            usuario.activo = True
            flash('Usuario activado exitosamente', 'success')
        
        db.session.commit()
        return redirect(url_for('admin.manage_users'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado del usuario: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_users'))

@admin_bp.route('/stores')
@login_required
@admin_required
@active_user_required
def manage_stores():
    """Gestión de tiendas"""
    try:
        mostrar_inactivas = request.args.get('mostrar_inactivas', False, type=bool)
        
        if mostrar_inactivas:
            tiendas = Store.get_todas().all()
        else:
            tiendas = Store.get_activas().all()
        
        return render_template('admin/stores.html', tiendas=tiendas, mostrar_inactivas=mostrar_inactivas)
    except Exception as e:
        flash(f'Error al cargar tiendas: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/staff')
@login_required
@admin_required
@active_user_required
def manage_staff():
    """Gestión de personal"""
    try:
        mostrar_inactivos = request.args.get('mostrar_inactivos', False, type=bool)
        
        if mostrar_inactivos:
            empleados = Staff.get_todos().all()
        else:
            empleados = Staff.get_activos().all()
        
        return render_template('admin/staff.html', empleados=empleados, mostrar_inactivos=mostrar_inactivos)
    except Exception as e:
        flash(f'Error al cargar personal: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/sales-report')
@login_required
@admin_required
@active_user_required
def sales_report():
    """Reporte de ventas"""
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        # Si no se proporcionan fechas, usar el mes actual
        if not fecha_inicio or not fecha_fin:
            hoy = datetime.utcnow()
            fecha_inicio = hoy.replace(day=1).date()  # Primer día del mes
            fecha_fin = hoy.date()
        
        # Convertir a objetos datetime si son strings
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Ajustar fecha_fin para incluir todo el día
        fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
        
        # Obtener ventas en el rango de fechas
        ventas = Sale.query.filter(
            Sale.fecha_venta >= fecha_inicio,
            Sale.fecha_venta <= fecha_fin
        ).all()
        
        # Calcular totales
        total_ventas = sum(venta.total for venta in ventas if venta.total)
        total_articulos = sum(len(venta.productos) for venta in ventas)
        
        return render_template('admin/sales_report.html',
                             ventas=ventas,
                             fecha_inicio=fecha_inicio.date(),
                             fecha_fin=fecha_fin.date(),
                             total_ventas=total_ventas,
                             total_articulos=total_articulos)
    
    except Exception as e:
        flash(f'Error al generar reporte de ventas: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

# ===== API ENDPOINTS =====

@admin_bp.route('/api/sales-data')
@login_required
@roles_required('Administrador', 'Vendedor')  # Usando el decorador mejorado
def api_sales_data():
    """Endpoint de API para datos de ventas (para gráficos)"""
    try:
        # Obtener parámetros
        dias = request.args.get('dias', 30, type=int)
        
        # Calcular fechas
        fecha_fin = datetime.utcnow()
        fecha_inicio = fecha_fin - timedelta(days=dias)
        
        # Consultar ventas agrupadas por día
        resultados = db.session.query(
            db.func.date(Sale.fecha_venta).label('fecha'),
            db.func.count(Sale.id_venta).label('ventas'),
            db.func.sum(Sale.total).label('ingresos')
        ).filter(
            Sale.fecha_venta >= fecha_inicio,
            Sale.fecha_venta <= fecha_fin
        ).group_by(
            db.func.date(Sale.fecha_venta)
        ).order_by(
            db.func.date(Sale.fecha_venta)
        ).all()
        
        # Formatear datos para el gráfico
        fechas = []
        ventas_por_dia = []
        ingresos_por_dia = []
        
        for resultado in resultados:
            fechas.append(resultado.fecha.strftime('%Y-%m-%d'))
            ventas_por_dia.append(resultado.ventas)
            ingresos_por_dia.append(float(resultado.ingresos) if resultado.ingresos else 0)
        
        return jsonify({
            'success': True,
            'data': {
                'fechas': fechas,
                'ventas': ventas_por_dia,
                'ingresos': ingresos_por_dia
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener datos de ventas: {str(e)}'
        }), 500

@admin_bp.route('/api/user-stats')
@login_required
@admin_required
def api_user_stats():
    """Endpoint de API para estadísticas de usuarios"""
    try:
        # Estadísticas de usuarios por rol
        stats = db.session.query(
            Role.nombre,
            db.func.count(User.id_usuario)
        ).join(
            User.rol
        ).group_by(
            Role.nombre
        ).all()
        
        # Formatear datos
        roles = []
        cantidades = []
        
        for stat in stats:
            roles.append(stat[0])
            cantidades.append(stat[1])
        
        return jsonify({
            'success': True,
            'data': {
                'roles': roles,
                'cantidades': cantidades
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener estadísticas de usuarios: {str(e)}'
        }), 500

@admin_bp.route('/api/system-health')
@login_required
@admin_required
def api_system_health():
    """Endpoint de API para verificar el estado del sistema"""
    try:
        # Verificar conexión a la base de datos
        db.session.execute('SELECT 1')
        
        # Contar registros en tablas importantes
        usuarios_activos = User.query.filter_by(activo=True).count()
        productos_activos = Product.get_activos().count()
        tiendas_activas = Store.get_activas().count()
        
        return jsonify({
            'success': True,
            'data': {
                'database': 'online',
                'usuarios_activos': usuarios_activos,
                'productos_activos': productos_activos,
                'tiendas_activas': tiendas_activas,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en el sistema: {str(e)}'
        }), 500

# ===== RUTAS ADICIONALES DE ADMINISTRACIÓN =====

@admin_bp.route('/settings')
@login_required
@admin_required
@active_user_required
def system_settings():
    """Configuración del sistema"""
    try:
        return render_template('admin/settings.html')
    except Exception as e:
        flash(f'Error al cargar configuración: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/backup')
@login_required
@admin_required
@active_user_required
def backup_system():
    """Realizar backup del sistema"""
    try:
        # Aquí iría la lógica de backup
        flash('Sistema de backup ejecutado exitosamente', 'success')
        return redirect(url_for('admin.dashboard'))
    except Exception as e:
        flash(f'Error al realizar backup: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/audit-log')
@login_required
@admin_required
@active_user_required
def audit_log():
    """Registro de auditoría del sistema"""
    try:
        # Aquí iría la lógica para mostrar registros de auditoría
        return render_template('admin/audit_log.html')
    except Exception as e:
        flash(f'Error al cargar registros de auditoría: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))