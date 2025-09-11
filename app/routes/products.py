from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Supplier
from sqlalchemy import distinct
from sqlalchemy.exc import IntegrityError
from app.forms import ProductForm, StockForm, ConfirmDeleteForm, EmptyForm
from app.utils.decorators import admin_required, seller_required
from datetime import datetime

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
@login_required
def list_products():
    products = Product.query.all()
    # Solo administradores y vendedores pueden ver los productos
    if current_user.rol.nombre not in ['Administrador', 'Vendedor']:
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    categorias = [row[0] for row in db.session.query(distinct(Product.categoria)).all() if row[0]]
    proveedores = Supplier.query.filter_by(activo=True).all()
    
    # Verificar si se deben mostrar productos inactivos (solo para administradores)
    try:    
        mostrar_inactivos = request.args.get('mostrar_inactivos', 'false').lower() in ['1', 'true', 'yes']
        
        if mostrar_inactivos:
            products = Product.query.all()
        else:
            products = Product.query.filter_by(activo=True).all()
            
        # Filtros
        categoria = request.args.get('categoria', '').strip()
        disponibilidad = request.args.get('disponibilidad', '').strip()
        proveedor_id = request.args.get('proveedor', '').strip()
        
        query = Product.query
        
        if not (mostrar_inactivos and current_user.rol.nombre == 'Administrador'):
            query = query.filter(Product.activo == True)
            
        if categoria:
            query = query.filter(Product.categoria.ilike(f"%{categoria}%"))
            
        if disponibilidad == 'disponible':
            query = query.filter(Product.stock > 0)      
        elif disponibilidad == 'agotado':
            query = query.filter(Product.stock == 0)
            
        if proveedor_id:
            query = query.filter(Product.proveedor_id == int(proveedor_id))
        
        products = query.all()
        form = EmptyForm()
        
        return render_template(
            'products/list.html',                  
            products=products, 
            mostrar_inactivos=mostrar_inactivos,
            proveedores=proveedores,
            categorias=categorias,
            form=form
            )
    except Exception as e:
        flash(f'Error al cargar Productos: {str(e)}', 'danger')
        return redirect(url_for('dashboard.dashboard'))

@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    form = ProductForm()
    form.proveedor_id.choices = [(p.id_proveedor, p.nombre) for p in Supplier.query.order_by(Supplier.nombre).all()]
    
    # if not nombre or not precio or not proveedor_id:
    if form.validate_on_submit():
        try:
            nuevo_producto = Product(
                nombre = form.nombre.data.strip(),
                categoria = form.categoria.data,
                descripcion = form.descripcion.data,
                precio = form.precio.data,
                stock = form.stock.data,
                proveedor_id = form.proveedor_id.data,
                activo = form.activo.data
            )
            
            if not form.activo.data:
                nuevo_producto.fecha_eliminacion = datetime.utcnow()
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
        
    return render_template('products/create.html', form=form)

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
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    form.proveedor_id.choices = [(p.id_proveedor, p.nombre) for p in Supplier.query.order_by(Supplier.nombre).all()]
    
    categorias = [row[0] for row in db.session.query(distinct(Product.categoria)).all() if row[0]]
    categoria = request.args.get('categoria', '').strip()
    
    query = Product.query
    
    if categoria:
        query = query.filter(Product.categoria.ilike(f"%{categoria}%"))
    
    if form.validate_on_submit():
        try:
            product.nombre = form.nombre.data.strip()
            product.categoria = form.categoria.data
            product.descripcion = form.descripcion.data
            product.precio = form.precio.data
            product.stock = form.stock.data
            product.proveedor_id = form.proveedor_id.data
            product.activo = form.activo.data
            
            if not form.activo.data:
                product.fecha_eliminacion = datetime.utcnow()
            else:
                product.fecha_eliminacion = None
                
            db.session.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('products.list_products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'error')
        
    return render_template('products/edit.html',form=form, product=product, categorias=categorias, product_id=product.id_producto)

@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        product.activo = False
        product.fecha_eliminacion = datetime.utcnow()
        db.session.commit()
        flash('Producto eliminado exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar producto: {str(e)}', 'danger')
        
    return redirect(url_for('products.list_products'))

@products_bp.route('/<int:product_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        product.activo = True
        product.fecha_eliminacion = None
        db.session.commit()
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
        try:
            accion = form.accion.data
            cantidad = form.cantidad.data

            if accion == 'aumentar':
                product.aumentar_stock(cantidad)
                flash(f'Stock aumentado en {cantidad} unidades', 'success')
            elif accion == 'reducir':
                if product.reducir_stock(cantidad):
                    flash(f'Stock reducido en {cantidad} unidades', 'success')

            db.session.commit()
            return redirect(url_for('product.list_product'))
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('products/stock.html', form=form, product=product)

@products_bp.route('/api/inventory')
@login_required
def api_inventory():
    # API para consultar inventario (útil para AJAX)
    try:
        productos = Product.query.filter_by(activo=True).all()
        return jsonify([{
            'id': p.id_producto,
            'nombre': p.nombre,
            'categoria': p.categoria,
            'stock': p.stock,
            'precio': float(p.precio),
            'activo': p.activo
        } for p in productos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    