from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from sqlalchemy.exc import IntegrityError
from app.models import Client, City, ClientOrder, ClientOrderProduct, Product
from app.forms import ClienteForm, ClientOrderForm, ClientOrderProductForm, ConfirmDeleteForm
from app.utils.decorators import admin_required, seller_required
from app.utils.security import sanitize_form_data

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
@login_required
def list_clients():
    # Solo administradores y vendedores pueden ver los clientes
    if current_user.rol.nombre not in ['Administrador', 'Vendedor']:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
    
    if mostrar_inactivos and current_user.rol.nombre == 'Administrador':
        clients = Client.get_todos().all()
    else:
        clients = Client.get_activos().all()
    
    return render_template('clients/list.html', clients=clients, mostrar_inactivos=mostrar_inactivos)

@clients_bp.route('/create', methods=['GET', 'POST'])
@login_required
@seller_required
def create_client():
    form = ClienteForm()
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.order_by(City.nombre).all()]
    
    if form.validate_on_submit():
        try:
            if Client.query.filter_by(telefono=form.telefono.data).first():
                flash('El teléfono ya está registrado', 'danger')
                return redirect(url_for('clients.create_client'))

            sanitize_data = sanitize_form_data(form.data)
            
            nuevo_cliente = Client(
                nombre = sanitize_data['nombre'],
                direccion = sanitize_data['direccion'],
                telefono = sanitize_data['telefono'],
                ciudad_id = sanitize_data['ciudad_id'],
                activo = sanitize_data['activo']
            )
            
            db.session.add(nuevo_cliente)
            db.session.commit()
            
            flash('Cliente creado exitosamente', 'success')
            return redirect(url_for('clients.list_clients'))

        except IntegrityError:
            db.session.rollback()
            flash('Error: Violación de integirdad en base de datos', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'error')
            
    return render_template('clients/create.html', form=form)

@clients_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClienteForm(object=client)
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.order_by(City.nombre).all()]
    
    if form.validate_on_submit():
        try:
            sanitize_data = sanitize_form_data(form.data)
            
            client.nombre = sanitize_data['nombre']
            client.direccion = sanitize_data['direccion']
            client.telefono = sanitize_data['telefono']
            client.ciudad_id = sanitize_data['ciudad_id']
            client.activo = sanitize_data['activo']
            
            if Client.query.filter(Client.nombre == form.nombre.data, Client.id_cliente != client.id_cliente).first():
                flash('El nombre ya está registrado en otro cliente', 'danger')
                return redirect(url_for('clients.edit_client', client_id=client.id_cliente))
            
            if not form.activo.data:
                client.fecha_eliminacion = form.fecha_eliminacion.data
            else:
                client.fecha_eliminacion = None
                                
            db.session.commit()
            flash('Cliente actualizado exitosamente', 'success')
            return redirect(url_for('clients.list_clients'))
        
        except Exception as e:
                db.session.rollback()
                flash(f'Error al crear Cliente: {str(e)}', 'error')
                        
    return render_template('clients/edit.html', form=form, client=client) 

@clients_bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
@seller_required
def delete_client(client_id):
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        client = Client.query.get_or_404(client_id)

        try:
            client.desactivar()
            flash('Cliente desactivado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al desactivar Cliente: {str(e)}', 'danger')
            
    return redirect(url_for('clients.list_clients'))

@clients_bp.route('/<int:client_id>/activate', methods=['POST'])
@login_required
@seller_required
def activate_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    try:
        client.activar()
        flash('Cliente reactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar el Cliente: {str(e)}', 'danger')
        
    return redirect(url_for('clients.list_clients'))

@clients_bp.route('/<int:client_id>')
@login_required
@seller_required
def view_client(client_id):
    client = Client.query.get_or_404(client_id)
    # Aquí luego agregaremos el historial de compras
    return render_template('clients/detail.html', client=client)

clients_bp = Blueprint('clients', __name__)

# Listar órdenes de un cliente
@clients_bp.route('/<int:client_id>/orders')
@login_required
def list_client_orders(client_id):
    cliente = Client.query.get_or_404(client_id)
    return render_template('clients/orders.html', cliente=cliente, ordenes=cliente.ordenes)


# Crear una orden para un cliente
@clients_bp.route('/<int:client_id>/orders/create', methods=['GET', 'POST'])
@login_required
def create_client_order(client_id):
    cliente = Client.query.get_or_404(client_id)
    form = ClientOrderForm()

    if form.validate_on_submit():
        data = sanitize_form_data(form.data)

        nueva_orden = ClientOrder(
            cliente_id=cliente.id_cliente,
            estado=data.get('estado', 'pendiente')
        )
        db.session.add(nueva_orden)
        db.session.commit()
        flash('Orden creada correctamente', 'success')
        return redirect(url_for('clients.list_client_orders', client_id=cliente.id_cliente))

    return render_template('clients/create_order.html', cliente=cliente, form=form)


# Ver detalle de una orden
@clients_bp.route('/orders/<int:order_id>')
@login_required
def view_client_order(order_id):
    orden = ClientOrder.query.get_or_404(order_id)
    return render_template('clients/order_detail.html', orden=orden)


# Agregar productos a una orden existente
@clients_bp.route('/orders/<int:order_id>/add_product', methods=['GET', 'POST'])
@login_required
def add_product_to_order(order_id):
    orden = ClientOrder.query.get_or_404(order_id)
    form = ClientOrderProductForm()

    if form.validate_on_submit():
        data = sanitize_form_data(form.data)

        producto = Product.query.get(data.get('id_producto'))
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('clients.view_client_order', order_id=orden.id_orden_cliente))

        cantidad = data.get('cantidad', 1)
        if producto.stock < cantidad:
            flash('Stock insuficiente', 'danger')
            return redirect(url_for('clients.view_client_order', order_id=orden.id_orden_cliente))

        orden_producto = ClientOrderProduct(
            id_orden_cliente=orden.id_orden_cliente,
            id_producto=producto.id_producto,
            cantidad=cantidad
        )
        db.session.add(orden_producto)
        db.session.commit()

        flash('Producto agregado a la orden', 'success')
        return redirect(url_for('clients.view_client_order', order_id=orden.id_orden_cliente))

    return render_template('clients/add_product.html', form=form, orden=orden)