from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Store, City
from app.forms import StoreForm
from app.utils.decorators import admin_required
from datetime import datetime

store_bp = Blueprint('store', __name__)

# ===== RUTAS PARA STORE (TIENDAS) =====

@store_bp.route('/')
@login_required
@admin_required
def list_stores():
    mostrar_inactivas = request.args.get('mostrar_inactivas', False, type=bool)
    
    if mostrar_inactivas:
        stores = Store.get_todas().all()
    else:
        stores = Store.get_activas().all()
    
    return render_template('stores/list.html', stores=stores, mostrar_inactivas=mostrar_inactivas)

@store_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_store():
    form = StoreForm()
    
    # Cargar opciones para el campo de ciudad
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.all()]

    if form.validate_on_submit():
        try:
            nueva_tienda = Store(
                nombre=form.nombre.data.strip(),
                direccion=form.direccion.data,
                ciudad_id=form.ciudad_id.data
            )
            
            db.session.add(nueva_tienda)
            db.session.commit()
            
            flash('Tienda creada exitosamente', 'success')
            return redirect(url_for('store.list_stores'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear tienda: {str(e)}', 'error')
    
    return render_template('stores/create.html', form=form)

@store_bp.route('/<int:store_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_store(store_id):
    tienda = Store.query.get_or_404(store_id)
    form = StoreForm(obj=tienda)
    
    # Cargar opciones para el campo de ciudad
    form.ciudad_id.choices = [(c.id_ciudad, c.nombre) for c in City.query.all()]

    if form.validate_on_submit():
        try:
            tienda.nombre = form.nombre.data
            tienda.direccion = form.direccion.data
            tienda.ciudad_id = form.ciudad_id.data
            
            db.session.commit()
            flash('Tienda actualizada exitosamente', 'success')
            return redirect(url_for('store.list_stores'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar tienda: {str(e)}', 'error')
    
    return render_template('stores/edit.html', form=form, tienda=tienda)

@store_bp.route('/<int:store_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_store(store_id):
    tienda = Store.query.get_or_404(store_id)
    
    try:
        tienda.activo = False
        tienda.fecha_eliminacion = datetime.utcnow()
        db.session.commit()
        flash('Tienda desactivada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar tienda: {str(e)}', 'error')
    
    return redirect(url_for('store.list_stores'))

@store_bp.route('/<int:store_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_store(store_id):
    tienda = Store.query.get_or_404(store_id)
    
    try:
        tienda.activo = True
        tienda.fecha_eliminacion = None
        db.session.commit()
        flash('Tienda reactivada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al reactivar tienda: {str(e)}', 'error')
    
    return redirect(url_for('store.list_stores'))

@store_bp.route('/<int:store_id>')
@login_required
@admin_required
def view_store(store_id):
    tienda = Store.query.get_or_404(store_id)
    
    # Obtener el personal activo de esta tienda
    personal_activo = [empleado for empleado in tienda.personal if empleado.activo]
    
    return render_template('stores/detail.html', tienda=tienda, personal_activo=personal_activo)