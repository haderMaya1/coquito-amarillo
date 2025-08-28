from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Sale, Invoice, SaleProduct, Client, Staff, Store, Product
from app.forms import SaleForm, SaleProductForm, InvoiceForm
from app.utils.decorators import seller_required
from app.utils.security import sanitize_form_data
from datetime import datetime

sales_bp = Blueprint('sales', __name__)

# --------- Listar ventas ---------
@sales_bp.route('/')
@login_required
@seller_required
def list_sales():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    cliente_id = request.args.get('cliente_id')
    vendedor_id = request.args.get('vendedor_id')

    query = Sale.query

    if fecha_inicio:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            query = query.filter(Sale.fecha >= fecha_inicio)
        except ValueError:
            flash('Formato de fecha inicial incorrecto', 'danger')

    if fecha_fin:
        try:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            query = query.filter(Sale.fecha <= fecha_fin)
        except ValueError:
            flash('Formato de fecha final incorrecto', 'danger')

    if cliente_id:
        query = query.filter(Sale.cliente_id == cliente_id)

    if vendedor_id:
        query = query.filter(Sale.empleado_id == vendedor_id)

    ventas = query.order_by(Sale.fecha.desc()).all()
    clientes = Client.get_activos().all()
    vendedores = Staff.query.all()

    return render_template('sales/list.html', ventas=ventas, clientes=clientes, vendedores=vendedores)


# --------- Crear venta ---------
@sales_bp.route('/create', methods=['GET', 'POST'])
@login_required
@seller_required
def create_sale():
    form = SaleForm()

    if form.validate_on_submit():
        data = sanitize_form_data(form.data)

        cliente_id = data.get('cliente_id')
        productos = data.get('productos')  # esperado como lista de dicts desde el formulario

        if not cliente_id or not productos:
            flash('Debes seleccionar un cliente y al menos un producto', 'danger')
            return redirect(url_for('sales.create_sale'))

        empleado = Staff.query.filter_by(usuario_id=current_user.id_usuario).first()
        if not empleado:
            flash('No se encontró el vendedor asociado', 'danger')
            return redirect(url_for('sales.create_sale'))

        nueva_venta = Sale(
            cliente_id=cliente_id,
            empleado_id=empleado.id_empleado,
            tienda_id=empleado.tienda_id,
            total=0
        )
        db.session.add(nueva_venta)
        db.session.flush()  # genera id_venta

        total_venta = 0
        for item in productos:
            producto_id = item.get('producto_id')
            cantidad = int(item.get('cantidad', 1))

            producto = Product.query.get(producto_id)
            if not producto:
                db.session.rollback()
                flash(f'Producto {producto_id} no encontrado', 'danger')
                return redirect(url_for('sales.create_sale'))

            if producto.stock < cantidad:
                db.session.rollback()
                flash(f'Stock insuficiente para {producto.nombre}', 'danger')
                return redirect(url_for('sales.create_sale'))

            subtotal = producto.precio * cantidad
            total_venta += subtotal

            venta_producto = SaleProduct(
                id_venta=nueva_venta.id_venta,
                id_producto=producto_id,
                cantidad=cantidad,
                subtotal=subtotal
            )
            db.session.add(venta_producto)

            producto.stock -= cantidad

        nueva_venta.total = total_venta

        factura = Invoice(
            venta_id=nueva_venta.id_venta,
            total=total_venta
        )
        db.session.add(factura)

        db.session.commit()

        flash('Venta y factura creadas exitosamente', 'success')
        return redirect(url_for('sales.view_sale', sale_id=nueva_venta.id_venta))

    clientes = Client.get_activos().all()
    productos = Product.get_activos().filter(Product.stock > 0).all()
    return render_template('sales/create.html', form=form, clientes=clientes, productos=productos)

@sales_bp.route('/<int:sale_id>/add_product', methods=['GET', 'POST'])
@login_required
@seller_required
def add_product_to_sale(sale_id):
    venta = Sale.query.get_or_404(sale_id)
    form = SaleProductForm()

    if form.validate_on_submit():
        data = sanitize_form_data(form.data)

        producto = Product.query.get(data['id_producto'])
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('sales.view_sale', sale_id=sale_id))

        if producto.stock < data['cantidad']:
            flash(f'Stock insuficiente para {producto.nombre}', 'danger')
            return redirect(url_for('sales.view_sale', sale_id=sale_id))

        subtotal = producto.precio * data['cantidad']

        venta_producto = SaleProduct(
            id_venta=venta.id_venta,
            id_producto=producto.id_producto,
            cantidad=data['cantidad'],
            subtotal=subtotal
        )
        db.session.add(venta_producto)

        # Actualizamos stock y totales
        producto.stock -= data['cantidad']
        venta.total += subtotal
        venta.factura.total = venta.total  # sincronizamos la factura

        db.session.commit()
        flash('Producto agregado correctamente a la venta', 'success')
        return redirect(url_for('sales.view_sale', sale_id=sale_id))

    return render_template('sales/add_product.html', form=form, venta=venta)

# --------- Ver venta ---------
@sales_bp.route('/<int:sale_id>')
@login_required
@seller_required
def view_sale(sale_id):
    venta = Sale.query.get_or_404(sale_id)
    return render_template('sales/detail.html', venta=venta)


# --------- Crear factura manualmente ---------
@sales_bp.route('/<int:sale_id>/invoice/create', methods=['GET', 'POST'])
@login_required
@seller_required
def create_invoice(sale_id):
    venta = Sale.query.get_or_404(sale_id)
    form = InvoiceForm()

    if form.validate_on_submit():
        data = sanitize_form_data(form.data)

        if venta.factura:
            flash('Ya existe una factura para esta venta', 'warning')
            return redirect(url_for('sales.view_invoice', sale_id=venta.id_venta))

        nueva_factura = Invoice(
            venta_id=venta.id_venta,
            total=data.get('total', venta.total)
        )
        db.session.add(nueva_factura)
        db.session.commit()

        flash('Factura creada correctamente', 'success')
        return redirect(url_for('sales.view_invoice', sale_id=venta.id_venta))

    return render_template('sales/create_invoice.html', form=form, venta=venta)


# --------- Ver factura ---------
@sales_bp.route('/<int:sale_id>/invoice')
@login_required
@seller_required
def view_invoice(sale_id):
    venta = Sale.query.get_or_404(sale_id)
    return render_template('sales/invoice.html', venta=venta, factura=venta.factura)

#Another config for sales:
# ... aquí van las rutas de ventas previas ...
# 🔹 API detalle de producto
@sales_bp.route('/api/product/<int:product_id>')
@login_required
def api_product_detail(product_id):
    producto = Product.query.get_or_404(product_id)
    return jsonify({
        'id': producto.id_producto,
        'nombre': producto.nombre,
        'precio': float(producto.precio),
        'stock': producto.stock
    })