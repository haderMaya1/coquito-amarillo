from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from sqlalchemy.exc import IntegrityError
from app.models import City
from app.forms import CiudadForm
from app.utils.decorators import admin_required
from datetime import datetime

cities_bp = Blueprint('cities', __name__)

@cities_bp.route('/')
@login_required
@admin_required
def list_cities():
    ciudades = City.query.order_by(City.nombre).all()
    return render_template('cities/list.html', ciudades=ciudades)

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

@cities_bp.route('/<int:city_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_city(city_id):
    ciudad = City.query.get_or_404(city_id)
    
    has_relationships = (ciudad.tiendas.count() > 0 or
                         ciudad.clientes.count() > 0 or
                         ciudad.proveedores.count() > 0 or
                         ciudad.personal.count() > 0
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
