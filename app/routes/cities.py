from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from sqlalchemy.exc import IntegrityError
from app.models import City, User
from app.forms import CiudadForm, ConfirmDeleteForm, EmptyForm
from app.utils.decorators import admin_required
from datetime import datetime

cities_bp = Blueprint('cities', __name__)

@cities_bp.route('/')
@login_required
@admin_required
def list_cities():
    form = EmptyForm()
    
    mostrar_inactivas = request.args.get('mostrar_inactivas', 'false').lower() in ['1', 'true', 'yes']

    if mostrar_inactivas:
        ciudades = City.get_todo().all()
    else:
        ciudades = City.get_activos().all()
        
    
    return render_template('cities/list.html', mostrar_inactivas=mostrar_inactivas, ciudades=ciudades, form=form)

@cities_bp.route('/<int:city_id>')
@login_required
@admin_required
def view_city(city_id):
    form = EmptyForm()
    ciudad = City.query.get_or_404(city_id)
    
    return render_template('cities/detail.html', ciudad=ciudad, form=form)

@cities_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_city():
    form = CiudadForm()
    if form.validate_on_submit():
        try:
            # Verificar duplicado
            if City.query.filter_by(nombre=form.nombre.data).first():
                flash('La ciudad ya existe', 'danger')
                return redirect(url_for('cities.create_city'))

            nueva_ciudad = City(nombre=form.nombre.data.strip())
            db.session.add(nueva_ciudad)
            db.session.commit()

            flash('Ciudad creada exitosamente', 'success')
            return redirect(url_for('cities.list_cities'))

        except IntegrityError:
            db.session.rollback()
            flash('Error: Violación de integridad en base de datos, la ciudad ya existe', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la ciudad: {str(e)}', 'danger')

    return render_template('cities/create.html', form=form)

@cities_bp.route('/<int:city_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_city(city_id):
    ciudad = City.query.get_or_404(city_id)
    form = CiudadForm(obj=ciudad)

    if form.validate_on_submit():
        try:
            # Verificar duplicado en otro registro
            if City.query.filter(City.id_ciudad != ciudad.id_ciudad, City.nombre == form.nombre.data).first():
                flash('Ya existe una ciudad con ese nombre', 'danger')
                return redirect(url_for('cities.edit_city', city_id=city_id))

            ciudad.nombre = form.nombre.data.strip()
            db.session.commit()

            flash('Ciudad actualizada exitosamente', 'success')
            return redirect(url_for('cities.list_cities'))

        except IntegrityError:
            db.session.rollback()
            flash('Error: Violación de integridad en base de datos, la ciudad ya existe', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al editar la ciudad: {str(e)}', 'danger')

    return render_template('cities/edit.html', form=form, ciudad=ciudad)

@cities_bp.route('/<int:city_id>/permanent_delete_city', methods=['POST'])
@login_required
@admin_required
def permanent_delete_city(city_id):
    ciudad = City.query.get_or_404(city_id)
    
    #Se debe usar len() y no count(), por no tener una relacion lazy='dynamic'
    #Por falta de relaciones dinamicas. Esta funcion devuelve lista y no query.
    has_relationships = (len(ciudad.tiendas) > 0 or
                         len(ciudad.clientes) > 0 or
                         len(ciudad.proveedores) > 0 or
                         len(ciudad.personal) > 0
                         )
    # Verificar relaciones
    if has_relationships:
        flash('No se puede eliminar la ciudad porque está siendo utilizada', 'danger')
        return redirect(url_for('cities.list_cities'))

    try:
        db.session.delete(ciudad)
        db.session.commit()
        flash('Ciudad eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la ciudad: {str(e)}', 'danger')

    return redirect(url_for('cities.list_cities'))

@cities_bp.route('/<int:city_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_city(city_id):
    ciudad = City.query.get_or_404(city_id)
    
    try:
        ciudad.activo = False
        ciudad.activar()
        flash('Empleado reactivado exitosamente', 'success')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar ciudad: {str(e)}', 'danger')
    
    return redirect(url_for('cities.list_cities'))


@cities_bp.route('/<int:city_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_city(city_id):
    ciudad = City.query.get_or_404(city_id)
    
    #Se debe usar len() y no count(), por no tener una relacion lazy='dynamic'
    #Por falta de relaciones dinamicas. Esta funcion devuelve lista y no query.
    has_relationships = (len(ciudad.tiendas) > 0 or
                         len(ciudad.clientes) > 0 or
                         len(ciudad.proveedores) > 0 or
                         len(ciudad.personal) > 0
                         )
    # Verificar relaciones
    if has_relationships:
        flash('No se puede eliminar la ciudad porque está siendo utilizada', 'danger')
        return redirect(url_for('cities.list_cities'))

    try:
        ciudad.activo = True
        ciudad.desactivar()
        db.session.commit()
        flash('Ciudad eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la ciudad: {str(e)}', 'danger')

    return redirect(url_for('cities.list_cities'))
