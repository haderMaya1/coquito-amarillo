from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Staff, Store, City, User, Supplier
from app.forms import StaffForm
from app.utils.security import sanitize_form_data
from app.utils.decorators import admin_required

staff_bp = Blueprint('staff', __name__)

# ===== RUTAS PARA STAFF (EMPLEADOS) =====

@staff_bp.route('/')
@login_required
@admin_required
def list_staff():
    mostrar_inactivos = request.args.get('mostrar_inactivos', False)
    
    if mostrar_inactivos:
        staff = Staff.get_todos().all()
    else:
        staff = Staff.get_activos().all()
    
    return render_template('staff/list.html', staff=staff, mostrar_inactivos=mostrar_inactivos)

@staff_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_staff():
    form = StaffForm()
    
    # Cargar opciones para los campos de selección
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.all()]
    form.tienda_id.choices = [(-1, '-- Seleccione una tienda --')] + [(t.id_tienda, t.nombre) for t in Store.get_activas().all()]
    form.usuario_id.choices = [(-1, '-- Seleccione un usuario --')] + [(u.id_usuario, u.username) for u in User.query.filter(User.empleado == None).all()]
    form.proveedor_id.choices = [(-1, '-- Seleccione un proveedor --')] + [(p.id_proveedor, p.nombre) for p in Supplier.get_activos().all()]

    if form.validate_on_submit():
        try:
            # Sanitizar los datos del formulario
            sanitized_data = sanitize_form_data(form.data)
            
            # Convertir valores -1 a None para campos opcionales
            tienda_id = sanitized_data['tienda_id'] if sanitized_data['tienda_id'] != -1 else None
            usuario_id = sanitized_data['usuario_id'] if sanitized_data['usuario_id'] != -1 else None
            proveedor_id = sanitized_data['proveedor_id'] if sanitized_data['proveedor_id'] != -1 else None
            
            # Validar que no se asocie a tienda y proveedor simultáneamente
            if tienda_id and proveedor_id:
                flash('Un empleado no puede estar asociado a una tienda y a un proveedor simultáneamente', 'error')
                return render_template('staff/create.html', form=form)
            
            nuevo_empleado = Staff(
                nombre=sanitized_data['nombre'],
                cargo=sanitized_data['cargo'],
                salario=sanitized_data['salario'],
                ciudad_id=sanitized_data['ciudad_id'],
                tienda_id=tienda_id,
                usuario_id=usuario_id,
                proveedor_id=proveedor_id
            )
            
            db.session.add(nuevo_empleado)
            db.session.commit()
            
            flash('Empleado creado exitosamente', 'success')
            return redirect(url_for('staff.list_staff'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear empleado: {str(e)}', 'error')
    
    return render_template('staff/create.html', form=form)

@staff_bp.route('/<int:staff_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    form = StaffForm(obj=empleado)
    
    # Cargar opciones para los campos de selección
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.all()]
    form.tienda_id.choices = [(-1, '-- Ninguna --')] + [(t.id_tienda, t.nombre) for t in Store.get_activas().all()]
    form.usuario_id.choices = [(-1, '-- Ninguno --')] + [(u.id_usuario, u.username) for u in User.query.all()]
    form.proveedor_id.choices = [(-1, '-- Ninguno --')] + [(p.id_proveedor, p.nombre) for p in Supplier.get_activas().all()]
    
    # Ajustar valores actuales para los selects
    form.tienda_id.data = empleado.tienda_id if empleado.tienda_id else -1
    form.usuario_id.data = empleado.usuario_id if empleado.usuario_id else -1
    form.proveedor_id.data = empleado.proveedor_id if empleado.proveedor_id else -1

    if form.validate_on_submit():
        try:
            # Sanitizar los datos del formulario
            sanitized_data = sanitize_form_data(form.data)
            
            # Convertir valores -1 a None para campos opcionales
            tienda_id = sanitized_data['tienda_id'] if sanitized_data['tienda_id'] != -1 else None
            usuario_id = sanitized_data['usuario_id'] if sanitized_data['usuario_id'] != -1 else None
            proveedor_id = sanitized_data['proveedor_id'] if sanitized_data['proveedor_id'] != -1 else None
            
            # Validar que no se asocie a tienda y proveedor simultáneamente
            if tienda_id and proveedor_id:
                flash('Un empleado no puede estar asociado a una tienda y a un proveedor simultáneamente', 'error')
                return render_template('staff/edit.html', form=form, empleado=empleado)
            
            empleado.nombre = sanitized_data['nombre']
            empleado.cargo = sanitized_data['cargo']
            empleado.salario = sanitized_data['salario']
            empleado.ciudad_id = sanitized_data['ciudad_id']
            empleado.tienda_id = tienda_id
            empleado.usuario_id = usuario_id
            empleado.proveedor_id = proveedor_id
            
            db.session.commit()
            flash('Empleado actualizado exitosamente', 'success')
            return redirect(url_for('staff.list_staff'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar empleado: {str(e)}', 'error')
    
    return render_template('staff/edit.html', form=form, empleado=empleado)

@staff_bp.route('/<int:staff_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    
    try:
        empleado.desactivar()
        flash('Empleado desactivado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al desactivar empleado: {str(e)}', 'error')
    
    return redirect(url_for('staff.list_staff'))

@staff_bp.route('/<int:staff_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    
    try:
        empleado.activar()
        flash('Empleado reactivado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al reactivar empleado: {str(e)}', 'error')
    
    return redirect(url_for('staff.list_staff'))

@staff_bp.route('/<int:staff_id>')
@login_required
@admin_required
def view_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    return render_template('staff/detail.html', empleado=empleado)