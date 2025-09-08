from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Role, Sale, Staff, Store
from app.utils.decorators import admin_required, active_user_required, roles_required
from sqlalchemy.exc import IntegrityError
from app.forms import UserForm, RolForm, ConfirmDeleteForm, EmptyForm
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
    usuarios = User.query.all()
    form = EmptyForm()
    """Gestión de usuarios"""
    try:
        mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
        
        if mostrar_inactivos:
            usuarios = User.query.all()
        else:
            usuarios = User.query.filter_by(activo=True).all()
        
        return render_template('admin/users.html', usuarios=usuarios, mostrar_inactivos=mostrar_inactivos, form=form)
    except Exception as e:
        flash(f'Error al cargar usuarios: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserForm()

    # Cargar roles y asignar choices antes de validar
    roles = Role.query.all()
    form.rol_id.choices = [(role.id_rol, role.nombre) for role in roles]

    # Si el formulario fue enviado pero no valida, lo registramos (útil)
    if request.method == 'POST' and not form.validate_on_submit():
        current_app.logger.debug('Formulario no validó. Errores: %s', form.errors)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        # Verificar duplicado
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('admin.create_user'))

        # Construir usuario (sin commit aún)
        nuevo_usuario = User(
            nombre=form.nombre.data.strip(),
            email=email,
            rol_id=form.rol_id.data,
            activo=bool(form.activo.data)
        )

        # Fecha de registro automática
        nuevo_usuario.fecha_registro = datetime.utcnow()

        # Validar/Asignar contraseña (capturar errores de validación personalizada)
        try:
            nuevo_usuario.password = form.password.data
        except ValueError as ve:
            current_app.logger.warning('Validación de contraseña falló: %s', ve)
            flash(f'Error en contraseña: {ve}', 'danger')
            return render_template('admin/create_user.html', form=form, roles=roles)

        # Fecha de eliminación (solo si inactivo y se suministró)
        if not form.activo.data and getattr(form, 'fecha_eliminacion', None) and form.fecha_eliminacion.data:
            nuevo_usuario.fecha_eliminacion = form.fecha_eliminacion.data
        else:
            nuevo_usuario.fecha_eliminacion = None

        # Logear lo que vamos a insertar (sin exponer contraseñas)
        try:
            pwd_hash_len = len(nuevo_usuario._password_hash) if getattr(nuevo_usuario, '_password_hash', None) else 0
        except Exception:
            pwd_hash_len = 0

        current_app.logger.debug('Intentando crear usuario: %s', {
            'nombre': nuevo_usuario.nombre,
            'email': nuevo_usuario.email,
            'rol_id': nuevo_usuario.rol_id,
            'activo': nuevo_usuario.activo,
            'fecha_registro': nuevo_usuario.fecha_registro,
            'fecha_eliminacion': nuevo_usuario.fecha_eliminacion,
            'pwd_hash_len': pwd_hash_len
        })

        db.session.add(nuevo_usuario)

        # Usamos flush() para forzar la validación de constraints antes del commit
        try:
            db.session.flush()   # si hay violación de integridad, ocurrirá aquí
            db.session.commit()
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('admin.manage_users'))
        except IntegrityError as ie:
            db.session.rollback()
            # ie.orig puede contener el mensaje DB (MySQL / SQLite distinto)
            current_app.logger.error('IntegrityError creando usuario: %s', ie, exc_info=True)
            flash('Error de integridad en la base de datos (p. ej. email duplicado o FK inválida). Revisa logs.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Error inesperado creando usuario', exc_info=True)
            flash('Error inesperado al crear usuario. Revisa logs del servidor.', 'danger')

    # Al final renderizamos (si GET o si validate_on_submit falló)
    return render_template('admin/create_user.html', form=form, roles=roles)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    usuario = User.query.get_or_404(user_id)
    form = UserForm()
    
    #Cargar roles
    roles = Role.query.all()
    form.rol_id.choices = [(role.id_rol, role.nombre) for role in roles]
    
    if form.validate_on_submit():
        try:  
            existing_user = User.query.filter(
                User.email == form.email.data,
                User.id_usuario != usuario.id_usuario
            ).first()
            
            if existing_user:
                flash('El email ya  está registrado en otro usuario', 'danger')
                return render_template('admin/edit_user.html', usuario=usuario, roles=roles, form=form)
            
            usuario.nombre = form.nombre.data.strip()
            usuario.email = form.email.data.strip().lower()
            usuario.rol_id = form.rol_id.data
            usuario.activo = form.activo.data
            
            if User.query.filter(User.email == form.email.data, User.id_usuario != usuario.id_usuario).first():
                flash('El nombre ya está registrado en otro cliente', 'danger')
                return redirect(url_for('admin.edit_user', user_id=usuario.id_usuario))
            
            if form.password.data:
                usuario.password = form.password.data
                    
            if not form.activo.data:
                usuario.fecha_eliminacion = datetime.utcnow()
            else:
                usuario.fecha_eliminacion = None
                
            db.session.commit()
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('admin.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'error')
        
    return render_template('admin/edit_user.html', usuario=usuario, roles=roles, form=form)  
    
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
            user.activo = False
            user.fecha_eliminacion = datetime.utcnow()
            db.session.commit()
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
        user.activo = True
        user.fecha_eliminacion = None
        db.session.commit()
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
            if Role.query.filter_by(nombre=nombre).first():
                flash('El rol ya existe', 'danger')
                return redirect(url_for('admin.create_role'))
            
            nuevo_rol = Role(
                nombre = form.nombre.data.strip(),
                descripcion = form.descripcion.data,
                activo = form.activo.data
            )
            
            if not form.activo.data:
                nuevo_rol.fecha_eliminacion = datetime.utcnow()
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
        
    return render_template('admin/create_role.html', form=form)

@admin_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RolForm()
    
    if form.validate_on_submit():
        try:
            existing_role = Role.query.filter(
                Role.nombre == form.nombre.data,
                Role.id_rol != role.id_rol   
            ).first()
            
            if existing_role:
                flash('El nombre ya está registrado en otro Rol', 'danger')
                return render_template('admin/edit_role.html', role=role, form=form)
            
            role.nombre = form.nombre.data.strip()
            role.descripcion = form.descripcion.data
            role.activo = form.activo.data
            
            if not form.activo.data:
                role.fecha_eliminacion = datetime.utcnow()
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
            if role.usuarios.count() > 0:
                flash('No se puede eliminar el rol porque hay usuarios asignados a él', 'danger')
                return redirect(url_for('admin.manage_roles'))
        
            role.activo = False
            role.fecha_eliminacion = datetime.utcnow()
            db.session.commit()
            flash('Rol desactivado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al desactivar rol: {str(e)}', 'danger')
            
    return redirect(url_for('admin.manage_roles'), role=role, form=form)

@admin_bp.route('/roles/<int:role_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_role(role_id):
    role = Role.query.get_or_404(role_id)
    
    if role.activo:
        flash('El rol ya está activo', 'info')
        return redirect(url_for('admin.manage_roles'))
    
    try:
        role.activo = True
        role.fecha_eliminacion = None
        db.session.commit()
        flash('Rol reactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar el rol: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_roles'), role=role)

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
        ventas_recientes = Sale.query.filter(Sale.fecha >= fecha_inicio).count()
        
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
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
@active_user_required
def toggle_user_status(user_id):
    """Activar/desactivar usuario"""
    try:
        usuario = User.query.get_or_404(user_id)
        
        if usuario.id_usuario == current_user.id_usuario:
            usuario.activo = False
            flash('No puedes cambiar el estado de tu propia cuenta', 'dannger')
            return redirect(url_for('admin.manage_users'))
        
        usuario.activo = not usuario.activo
        
        if usuario.activo:
            usuario.fecha_eliminacion = None
            flash('Usuario activado exitosamente', 'success')
        else:
            usuario.fecha_eliminacion = datetime.utcnow()
            flash('Usuario desactivado exitosamente', 'success')
            
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
            Sale.fecha >= fecha_inicio,
            Sale.fecha <= fecha_fin
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
            db.func.date(Sale.fecha).label('fecha'),
            db.func.count(Sale.id_venta).label('ventas'),
            db.func.sum(Sale.total).label('ingresos')
        ).filter(
            Sale.fecha >= fecha_inicio,
            Sale.fecha <= fecha_fin
        ).group_by(
            db.func.date(Sale.fecha)
        ).order_by(
            db.func.date(Sale.fecha)
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