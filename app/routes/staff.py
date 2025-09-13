from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Staff, Store, City, User, Supplier
from app.forms import StaffForm, ConfirmDeleteForm, EmptyForm
from app.utils.decorators import admin_required
from sqlalchemy.exc import SQLAlchemyError

staff_bp = Blueprint('staff', __name__)

# ===== RUTAS PARA STAFF (EMPLEADOS) =====

@staff_bp.route('/')
@login_required
@admin_required
def list_staff():
    # Crear instancias de todos los formularios necesarios
    form = EmptyForm()
    delete_form = ConfirmDeleteForm()
    activate_form = ConfirmDeleteForm()
    
    mostrar_inactivos = request.args.get('mostrar_inactivos', False)
    
    if mostrar_inactivos:
        staff = Staff.get_todos().all()
    else:
        staff = Staff.get_activos().all()
    
    return render_template(
        'staff/list.html', 
        staff=staff, 
        mostrar_inactivos=mostrar_inactivos, 
        activate_form=activate_form, 
        delete_form=delete_form, 
        form=form
    )
    
@staff_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_staff():
    form = StaffForm()
    
    # Cargar opciones para los campos de selección
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.all()]
    form.tienda_id.choices = [(-1, '-- Seleccione una tienda --')] + [(t.id_tienda, t.nombre) for t in Store.get_activas().all()]
    form.usuario_id.choices = [(-1, '-- Seleccione un usuario --')] + [(u.id_usuario, u.nombre) for u in User.get_activos().all()]
    form.proveedor_id.choices = [(-1, '-- Seleccione un proveedor --')] + [(p.id_proveedor, p.nombre) for p in Supplier.get_activos().all()]

    if form.validate_on_submit():
        try:
            # Obtener valores directamente del formulario
            tienda_id = form.tienda_id.data if form.tienda_id.data != -1 else None
            usuario_id = form.usuario_id.data if form.usuario_id.data != -1 else None
            proveedor_id = form.proveedor_id.data if form.proveedor_id.data != -1 else None
            
            # Validar que no se asocie a tienda y proveedor simultáneamente
            if tienda_id and proveedor_id:
                flash('Un empleado no puede estar asociado a una tienda y a un proveedor simultáneamente', 'error')
                return render_template('staff/create.html', form=form)
            
            nuevo_empleado = Staff(
                nombre=form.nombre.data,
                cargo=form.cargo.data,
                salario=form.salario.data,
                ciudad_id=form.ciudad_id.data,
                tienda_id=tienda_id,
                usuario_id=usuario_id,
                proveedor_id=proveedor_id
            )
            
            db.session.add(nuevo_empleado)
            db.session.commit()
            
            flash('Empleado creado exitosamente', 'success')
            return redirect(url_for('staff.list_staff'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error de base de datos al crear empleado: {str(e)}', 'error')
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
    form.usuario_id.choices = [(-1, '-- Ninguno --')] + [(u.id_usuario, u.nombre) for u in User.get_activos().all()]
    form.proveedor_id.choices = [(-1, '-- Ninguno --')] + [(p.id_proveedor, p.nombre) for p in Supplier.get_activas().all()]
    
    if request.method == 'GET':
        # Ajustar valores actuales para los selects
        form.tienda_id.data = empleado.tienda_id if empleado.tienda_id else -1
        form.usuario_id.data = empleado.usuario_id if empleado.usuario_id else -1
        form.proveedor_id.data = empleado.proveedor_id if empleado.proveedor_id else -1

    if form.validate_on_submit():
        try:
            # Obtener valores directamente del formulario
            tienda_id = form.tienda_id.data if form.tienda_id.data != -1 else None
            usuario_id = form.usuario_id.data if form.usuario_id.data != -1 else None
            proveedor_id = form.proveedor_id.data if form.proveedor_id.data != -1 else None
            
            # Validar que no se asocie a tienda y proveedor simultáneamente
            if tienda_id and proveedor_id:
                flash('Un empleado no puede estar asociado a una tienda y a un proveedor simultáneamente', 'error')
                return render_template('staff/edit.html', form=form, empleado=empleado)
            
            empleado.nombre = form.nombre.data
            empleado.cargo = form.cargo.data
            empleado.salario = form.salario.data
            empleado.ciudad_id = form.ciudad_id.data
            empleado.tienda_id = tienda_id
            empleado.usuario_id = usuario_id
            empleado.proveedor_id = proveedor_id
            
            db.session.commit()
            flash('Empleado actualizado exitosamente', 'success')
            return redirect(url_for('staff.list_staff'))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Error de base de datos al editar empleado: {str(e)}', 'error')
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
        empleado.activo = False
        empleado.desactivar()
        flash('Empleado desactivado exitosamente', 'success')
        db.session.commit()
    except Exception as e:
        flash(f'Error al desactivar empleado: {str(e)}', 'error')
    
    return redirect(url_for('staff.list_staff'))

@staff_bp.route('/<int:staff_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    
    try:
        empleado.activo = True
        empleado.activar()
        flash('Empleado reactivado exitosamente', 'success')
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error de base de datos al activate empleado: {str(e)}', 'error')    
    except Exception as e:
        flash(f'Error al reactivar empleado: {str(e)}', 'error')
    
    return redirect(url_for('staff.list_staff'))

##################################### DANGER #####################################
@staff_bp.route('/<int:staff_id>/permanent-delete', methods=['POST'])
@login_required
@admin_required
def permanent_delete_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    try:
        db.session.delete(empleado)  # Eliminación física
        db.session.commit()
        flash('Empleado eliminado permanentemente', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error de base de datos al eliminar empleado: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar empleado: {str(e)}', 'error')
    
    return redirect(url_for('staff.list_staff'))
#################################################################################

@staff_bp.route('/<int:staff_id>')
@login_required
@admin_required
def view_staff(staff_id):
    form = EmptyForm()
    empleado = Staff.query.get_or_404(staff_id)
    return render_template('staff/detail.html', empleado=empleado, form=form)
