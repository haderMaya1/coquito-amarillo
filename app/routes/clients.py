from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from sqlalchemy.exc import IntegrityError
from app.models import Client, City, ClientOrder, ClientOrderProduct, Product
from app.forms import ClienteForm, ClientOrderForm, ClientOrderProductForm, ConfirmDeleteForm, EmptyForm
from app.utils.decorators import admin_required, seller_required

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
@login_required
def list_clients():
    clients = Client.query.all()
    form = EmptyForm()
    try:
        # Solo administradores y vendedores pueden ver los clientes
        if current_user.rol.nombre not in ['Administrador', 'Vendedor']:
            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        
        mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
        
        if mostrar_inactivos and current_user.rol.nombre == 'Administrador' or current_user.rol.nombre == 'Vendedor':
            clients = Client.get_todos().all()
        else:
            clients = Client.get_activos().all()
        
        return render_template('clients/list.html', clients=clients, mostrar_inactivos=mostrar_inactivos, form=form)
    except Exception as e:
        flash(f'Error al cargar clientes: {str(e)}', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
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
            
            nuevo_cliente = Client(
                nombre = form.nombre.data,
                direccion = form.direccion.data,
                telefono = form.telefono.data,
                ciudad_id = form.ciudad_id.data,
                activo = form.activo.data
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
            client.nombre = form.nombre.data
            client.direccion = form.direccion.data
            client.telefono = form.telefono.data
            client.ciudad_id = form.ciudad_id.data
            client.activo = form.activo.data
            
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
            client.activo = False
            client.desactivar()
            db.session.commit()
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
    
    if client.activo:
        flash('El usuario ya está activo', 'info')
        return redirect(url_for('clients.list_clients'))
    
    try:
        client.activo = True
        client.activar()
        db.session.commit()
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
    form = EmptyForm()
    # Aquí luego agregaremos el historial de compras
    return render_template('clients/detail.html', client=client, form=form)

################################################################
#                                                              #
############################ORDENES#############################
#                                                              #    
################################################################

# Listar órdenes de un cliente
@clients_bp.route('/<int:client_id>/orders')
@login_required
def list_client_orders(client_id):
    form = EmptyForm()
    cliente = Client.query.get_or_404(client_id)

    if current_user.rol.nombre not in ['Administrador', 'Vendedor']:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    # Base query: todas las órdenes del cliente
    query = ClientOrder.query.filter_by(cliente_id=client_id)

    # --- Filtros desde request.args ---
    estado = request.args.get('estado', type=str)
    mostrar_completadas = request.args.get('mostrar_completadas', '1') == '1'
    mostrar_canceladas = request.args.get('mostrar_canceladas', '1') == '1'
    orden_id = request.args.get('orden_id', type=str)

    # Filtro por estado específico
    if estado and estado in ['pendiente', 'completada', 'cancelada']:
        query = query.filter(ClientOrder.estado == estado)

    # Filtro por ID de orden
    if orden_id:
        query = query.filter(ClientOrder.id_orden_cliente.like(f"%{orden_id}%"))

    # Ocultar completadas si el usuario lo pide
    if not mostrar_completadas:
        query = query.filter(ClientOrder.estado != 'completada')

    # Ocultar canceladas si el usuario lo pide
    if not mostrar_canceladas:
        query = query.filter(ClientOrder.estado != 'cancelada')

    # Ejecutar query final
    ordenes = query.order_by(ClientOrder.id_orden_cliente.desc()).all()

    return render_template(
        'clients/order/orders.html',
        cliente=cliente,
        ordenes=ordenes,
        form=form,
        # Pasamos los filtros a la vista para mantener estado
        filtros={
            'estado': estado,
            'mostrar_completadas': mostrar_completadas,
            'mostrar_canceladas': mostrar_canceladas,
            'orden_id': orden_id
        }
    )
    
# Crear una orden para un cliente
@clients_bp.route('/<int:client_id>/orders/create', methods=['GET', 'POST'])
@login_required
def create_client_order(client_id):
    cliente = Client.query.get_or_404(client_id)
    form = ClientOrderForm()

    if form.validate_on_submit():

        nueva_orden = ClientOrder(
            cliente_id=cliente.id_cliente,
            estado=ClientOrder.query.get('estado', 'pendiente')
        )
        db.session.add(nueva_orden)
        db.session.commit()
        flash('Orden creada correctamente', 'success')
        return redirect(url_for('clients.list_client_orders', client_id=cliente.id_cliente))

    return render_template('clients/order/create_order.html', cliente=cliente, form=form)


# Ver detalle de una orden
@clients_bp.route('/orders/<int:order_id>')
@login_required
def view_client_order(order_id):
    orden = ClientOrder.query.get_or_404(order_id)
    form = EmptyForm()
    return render_template('clients/order/order_detail.html', orden=orden, form=form)


# Agregar productos a una orden existente
@clients_bp.route('/orders/<int:order_id>/add_product', methods=['GET', 'POST'])
@login_required
def add_product_to_order(order_id):
    orden = ClientOrder.query.get_or_404(order_id)
    form = ClientOrderProductForm()

    if form.validate_on_submit():

        producto = Product.query.get(('id_producto'))
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('clients.view_client_order', order_id=orden.id_orden_cliente))

        cantidad = ClientOrder.query.get('cantidad', 1)
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

    return render_template('clients/order/add_product.html', form=form, orden=orden)