from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import City, Supplier, SupplierOrder, Product, SupplierOrderProduct
from app.forms import SupplierForm, SupplierOrderForm
from app.utils.decorators import admin_required
from app.utils.security import sanitize_form_data, sanitize_input


suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

# ===== RUTAS PARA SUPPLIERS (PROVEEDORES) =====

@suppliers_bp.route('/')
@login_required
def list_suppliers():
    # Proveedores solo pueden ver su información, administradores ven todos
    if current_user.rol.nombre == 'Proveedor' and current_user.empleado and current_user.empleado.proveedor:
        suppliers = [current_user.empleado.proveedor]
    else:
        mostrar_inactivos = request.args.get('mostrar_inactivos', False)
        if mostrar_inactivos and current_user.rol.nombre == 'Administrador':
            suppliers = Supplier.get_todos().all()
        else:
            suppliers = Supplier.get_activos().all()
    
    return render_template('suppliers/list.html', suppliers=suppliers)

@suppliers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_supplier():
    form = SupplierForm()
    
    # Cargar opciones para el campo de ciudad
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.all()]

    if form.validate_on_submit():
        try:
            # Sanitizar los datos del formulario
            sanitized_data = sanitize_form_data(form.data)
            
            nuevo_proveedor = Supplier(
                nombre=sanitized_data['nombre'],
                contacto=sanitized_data['contacto'],
                ciudad_id=sanitized_data['ciudad_id']
            )
            
            db.session.add(nuevo_proveedor)
            db.session.commit()
            
            flash('Proveedor creado exitosamente', 'success')
            return redirect(url_for('suppliers.list_suppliers'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear proveedor: {str(e)}', 'error')
    
    return render_template('suppliers/create.html', form=form)

@suppliers_bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(supplier_id):
    proveedor = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=proveedor)
    
    # Cargar opciones para el campo de ciudad
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.all()]

    if form.validate_on_submit():
        try:
            # Sanitizar los datos del formulario
            sanitized_data = sanitize_form_data(form.data)
            
            proveedor.nombre = sanitized_data['nombre']
            proveedor.contacto = sanitized_data['contacto']
            proveedor.ciudad_id = sanitized_data['ciudad_id']
            
            db.session.commit()
            flash('Proveedor actualizado exitosamente', 'success')
            return redirect(url_for('suppliers.list_suppliers'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar proveedor: {str(e)}', 'error')
    
    return render_template('suppliers/edit.html', form=form, proveedor=proveedor)

@suppliers_bp.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_supplier(supplier_id):
    proveedor = Supplier.query.get_or_404(supplier_id)
    
    try:
        proveedor.desactivar()
        flash('Proveedor desactivado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al desactivar proveedor: {str(e)}', 'error')
    
    return redirect(url_for('suppliers.list_suppliers'))

@suppliers_bp.route('/<int:supplier_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_supplier(supplier_id):
    proveedor = Supplier.query.get_or_404(supplier_id)
    
    try:
        proveedor.activar()
        flash('Proveedor reactivado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al reactivar proveedor: {str(e)}', 'error')
    
    return redirect(url_for('suppliers.list_suppliers'))

@suppliers_bp.route('/<int:supplier_id>')
@login_required
def view_supplier(supplier_id):
    proveedor = Supplier.query.get_or_404(supplier_id)
    
    # Verificar permisos
    if (current_user.rol.nombre == 'Proveedor' and 
        current_user.empleado and 
        current_user.empleado.proveedor_id != supplier_id):
        flash('No tienes permisos para ver este proveedor', 'danger')
        return redirect(url_for('suppliers.list_suppliers'))
    
    return render_template('suppliers/detail.html', proveedor=proveedor)

# Gestión de Órdenes de Proveedor
@suppliers_bp.route('/orders')
@login_required
def list_orders():
    if current_user.rol.nombre == 'Proveedor' and current_user.empleado:
        orders = SupplierOrder.query.filter_by(proveedor_id=current_user.empleado.proveedor_id).all()
    else:
        orders = SupplierOrder.query.all()
    
    return render_template('suppliers/orders/list.html', orders=orders)

@suppliers_bp.route('/orders/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_order():
    form = SupplierOrderForm()
    
    # Cargar opciones para el campo de proveedor
    form.proveedor_id.choices = [(p.id_proveedor, p.nombre) for p in Supplier.get_activos().all()]

    if form.validate_on_submit():
        try:
            # Sanitizar los datos del formulario
            sanitized_data = sanitize_form_data(form.data)
            proveedor_id = sanitized_data['proveedor_id']
            
            # Procesar productos (si se enviaron)
            productos = request.form.getlist('productos[]')
            cantidades = request.form.getlist('cantidades[]')
            
            if not productos or not cantidades:
                flash('Debe agregar al menos un producto a la orden', 'error')
                return render_template('suppliers/orders/create.html', form=form, productos=Product.get_activos().all())
            
            # Crear la orden
            nueva_orden = SupplierOrder(proveedor_id=proveedor_id)
            db.session.add(nueva_orden)
            db.session.flush()  # Para obtener el ID de la orden
            
            for i in range(len(productos)):
                producto_id = sanitize_input(productos[i])
                cantidad = sanitize_input(cantidades[i])
                
                # Validar cantidad
                try:
                    cantidad = int(cantidad)
                    if cantidad <= 0:
                        flash('La cantidad debe ser mayor a 0', 'error')
                        db.session.rollback()
                        return render_template('suppliers/orders/create.html', form=form, productos=Product.get_activos().all())
                except ValueError:
                    flash('Cantidad inválida', 'error')
                    db.session.rollback()
                    return render_template('suppliers/orders/create.html', form=form, productos=Product.get_activos().all())
                
                # Verificar que el producto existe
                producto = Product.query.get(producto_id)
                if not producto:
                    flash(f'El producto con ID {producto_id} no existe', 'error')
                    db.session.rollback()
                    return render_template('suppliers/orders/create.html', form=form, productos=Product.get_activos().all())
                
                # Agregar producto a la orden
                orden_producto = SupplierOrderProduct(
                    id_orden_proveedor=nueva_orden.id_orden_proveedor,
                    id_producto=producto_id,
                    cantidad=cantidad
                )
                db.session.add(orden_producto)
            
            db.session.commit()
            flash('Orden de proveedor creada exitosamente', 'success')
            return redirect(url_for('suppliers.list_orders'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear orden: {str(e)}', 'error')
    
    return render_template('suppliers/orders/create.html', form=form, productos=Product.get_activos().all())

@suppliers_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    orden = SupplierOrder.query.get_or_404(order_id)
    
    # Verificar permisos
    if (current_user.rol.nombre == 'Proveedor' and 
        current_user.empleado and 
        current_user.empleado.proveedor_id != orden.proveedor_id):
        flash('No tienes permisos para modificar esta orden', 'danger')
        return redirect(url_for('suppliers.list_orders'))
    
    nuevo_estado = request.form.get('estado')
    nuevo_estado = sanitize_input(nuevo_estado) if nuevo_estado else None
    
    if nuevo_estado == 'recibida':
        try:
            orden.recibir_orden()
            flash('Orden marcada como recibida e inventario actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al recibir orden: {str(e)}', 'error')
    elif nuevo_estado == 'cancelada':
        try:
            orden.cancelar_orden()
            flash('Orden cancelada', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al cancelar orden: {str(e)}', 'error')
    else:
        flash('Estado no válido', 'danger')
    
    return redirect(url_for('suppliers.list_orders'))

@suppliers_bp.route('/orders/<int:order_id>')
@login_required
def view_order(order_id):
    orden = SupplierOrder.query.get_or_404(order_id)
    
    # Verificar permisos
    if (current_user.rol.nombre == 'Proveedor' and 
        current_user.empleado and 
        current_user.empleado.proveedor_id != orden.proveedor_id):
        flash('No tienes permisos para ver esta orden', 'danger')
        return redirect(url_for('suppliers.list_orders'))
    
    return render_template('suppliers/orders/detail.html', orden=orden)