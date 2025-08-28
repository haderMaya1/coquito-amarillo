from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Supplier, Invoice, Sale
from sqlalchemy.exc import IntegrityError
from app.forms import ProductForm, ConfirmDeleteForm, StockForm, InvoiceForm, SaleForm
from app.utils.security import sanitize_form_data
from app.utils.decorators import admin_required, seller_required

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
@login_required
def list_products():
    # Solo administradores y vendedores pueden ver los productos
    if current_user.rol.nombre not in ['Administrador', 'Vendedor']:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    # Verificar si se deben mostrar productos inactivos (solo para administradores)
    mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
    # Filtros
    categoria = request.args.get('categoria', '')
    disponibilidad = request.args.get('disponibilidad', '')
    
    query = Product.query
    
    if not (mostrar_inactivos and current_user.rol.nombre == 'Administrador'):
        query = query.filter(Product.activo == True)
    if categoria:
        query = query.filter(Product.categoria.ilike(f"%{categoria}"))
    if disponibilidad == 'disponible':
        query = query.filter(Product.stock > 0)
    elif disponibilidad == 'agotado':
        query = query.filter(Product.stock == 0)
    
    products = query.all()
    
    return render_template(
        'products/list.html',                  
        products=products, 
        mostrar_inactivos=mostrar_inactivos
        )

@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    form = ProductForm()
    form.proveedor_id.choices = [(p.id_proveedor, p.nombre) for p in Supplier.query.all()]
    
    # if not nombre or not precio or not proveedor_id:
    if form.validate_on_submit():
        try:
            sanitize_data = sanitize_form_data(form.data)
            
            nuevo_producto = Product(
                nombre = sanitize_data['nombre'],
                descripcion = sanitize_data['descripcion'],
                precio = sanitize_data['precio'],
                stock =  sanitize_data['stock'],
                proveedor_id = sanitize_data['proveedor_id'],
                activo = sanitize_data['activo']
            )
            
            if not form.activo.data:
                nuevo_producto.fecha_eliminacion = form.fecha_eliminacion.data
            else:
                nuevo_producto.fecha_eliminacion = None
        
            db.session.add(nuevo_producto)
            db.session.commit()
            
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('products.list_products'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Violación de integridad en base de datos', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear Producto: {str(e)}', 'error')
        
        return render_template('admin/create.html', form=form)

@products_bp.route('/<int:product_id>')
@login_required
def view_product(product_id):
    # Solo administradores y vendedores pueden ver los detalles
    if current_user.rol.nombre not in ['Administrador', 'Vendedor']:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    product = Product.query.get_or_404(product_id)
    return render_template('products/detail.html', product=product)

@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    form = ProductForm()
    
    form.proveedor_id.choices = [(p.id_proveedor, p.nombre) for p in Supplier.query.all()]
    actualizar_producto = Product.query.get_or_404(product_id)
    
    if form.validate_on_submit():
        try:
            sanitize_data = sanitize_form_data(form.data)
            
            actualizar_producto.nombre = sanitize_data['nombre']
            actualizar_producto.descripcion = sanitize_data['descripcion']
            actualizar_producto.precio = sanitize_data['precio']
            actualizar_producto.stock = sanitize_data['stock']
            actualizar_producto.proveedor_id = sanitize_data['proveedor_id']
            
            if not form.activo.data:
                actualizar_producto.fecha_eliminacion = form.fecha_eliminacion.data
            else:
                actualizar_producto.fecha_eliminacion = None
                
            db.session.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('products.list_products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
        
    return render_template('products/edit.html', producto=actualizar_producto, form=form)

@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    #Soft delete
    product.desactivar()
    
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('products.list_products'))

@products_bp.route('/<int:product_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    try:
        # Reactivar producto
        product.activar()
        flash('Producto reactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar el producto: {str(e)}', 'danger')
    return redirect(url_for('products.list_products'))

@products_bp.route('/<int:product_id>/stock', methods=['GET', 'POST'])
@login_required
@admin_required
def update_stock(product_id):
    product = Product.query.get_or_404(product_id)
    form = StockForm()

    if form.validate_on_submit():
        accion = form.accion.data
        cantidad = form.cantidad.data

        if accion == 'aumentar':
            product.aumentar_stock(cantidad)
            flash(f'Stock aumentado en {cantidad} unidades', 'success')
        elif accion == 'reducir':
            if product.reducir_stock(cantidad):
                flash(f'Stock reducido en {cantidad} unidades', 'success')
            else:
                flash('No hay suficiente stock para reducir', 'danger')

        return redirect(url_for('products.list_products'))

    return render_template('products/stock.html', form=form, product=product)

@products_bp.route('/api/inventory')
@login_required
def api_inventory():
    # API para consultar inventario (útil para AJAX)
    productos = Product.query.all()
    return jsonify([{
        'id': p.id_producto,
        'nombre': p.nombre,
        'stock': p.stock,
        'precio': float(p.precio),
        'activo': p.activo
    } for p in productos])