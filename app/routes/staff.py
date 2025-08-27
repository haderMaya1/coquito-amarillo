from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Staff, Store, City, User, Supplier
from app.utils.decorators import admin_required

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/')
@login_required
@admin_required
def list_staff():
    mostrar_inactivos = request.args.get('mostrar_inactivos', False)
    
    if mostrar_inactivos:
        staff = Staff.get_todos().all()
    else:
        staff = Staff.get_activos().all()
    
    return render_template('staff/list.html', staff=staff, mostrar_inactivos=mostrar_inactivos)

@staff_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_staff():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        cargo = request.form.get('cargo')
        salario = request.form.get('salario')
        ciudad_id = request.form.get('ciudad_id')
        tienda_id = request.form.get('tienda_id')
        usuario_id = request.form.get('usuario_id')
        proveedor_id = request.form.get('proveedor_id')
        
        nuevo_empleado = Staff(
            nombre=nombre,
            cargo=cargo,
            salario=salario,
            ciudad_id=ciudad_id,
            tienda_id=tienda_id,
            usuario_id=usuario_id,
            proveedor_id=proveedor_id
        )
        
        db.session.add(nuevo_empleado)
        db.session.commit()
        
        flash('Empleado creado exitosamente', 'success')
        return redirect(url_for('staff.list_staff'))
    
    ciudades = City.query.all()
    tiendas = Store.query.all()
    usuarios = User.query.filter(User.empleado == None).all()
    proveedores = Supplier.get_activos().all()
    
    return render_template('staff/create.html', 
                         ciudades=ciudades, 
                         tiendas=tiendas, 
                         usuarios=usuarios,
                         proveedores=proveedores)

@staff_bp.route('/<int:staff_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    
    if request.method == 'POST':
        empleado.nombre = request.form.get('nombre')
        empleado.cargo = request.form.get('cargo')
        empleado.salario = request.form.get('salario')
        empleado.ciudad_id = request.form.get('ciudad_id')
        empleado.tienda_id = request.form.get('tienda_id')
        empleado.usuario_id = request.form.get('usuario_id')
        empleado.proveedor_id = request.form.get('proveedor_id')
        
        db.session.commit()
        flash('Empleado actualizado exitosamente', 'success')
        return redirect(url_for('staff.list_staff'))
    
    ciudades = City.query.all()
    tiendas = Store.query.all()
    usuarios = User.query.all()
    proveedores = Supplier.get_activos().all()
    
    return render_template('staff/edit.html', 
                         empleado=empleado, 
                         ciudades=ciudades, 
                         tiendas=tiendas, 
                         usuarios=usuarios,
                         proveedores=proveedores)

@staff_bp.route('/<int:staff_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    
    empleado.desactivar()
    flash('Empleado desactivado exitosamente', 'success')
    return redirect(url_for('staff.list_staff'))

@staff_bp.route('/<int:staff_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    
    empleado.activar()
    flash('Empleado reactivado exitosamente', 'success')
    return redirect(url_for('staff.list_staff'))

@staff_bp.route('/<int:staff_id>')
@login_required
@admin_required
def view_staff(staff_id):
    empleado = Staff.query.get_or_404(staff_id)
    return render_template('staff/detail.html', empleado=empleado)