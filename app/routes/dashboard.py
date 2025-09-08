from flask import Blueprint, render_template, jsonify, request, flash
from app.models import Product, Sale, Client, Staff, Store, Supplier, User, SupplierOrder
from app.forms import DateRangeForm, SalesFilterForm, QuickStatsForm
from app.utils.decorators import login_required, roles_required, current_user
from app import db
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/')
@login_required
def dashboard():
    """Panel de control principal con estadísticas adaptadas al rol del usuario"""
    try:
        #Obtener fecha de hoy(sin hora)
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        
        # Estadísticas básicas para todos los roles
        stats = {
            'total_products': Product.get_activos().count(),
            'total_sales_today': Sale.query.filter(
                Sale.fecha >= today_start
            ).count(),
            'total_clients': Client.get_activos().count(),
        }

        # Estadísticas específicas según el rol
        if current_user.rol.nombre == 'Administrador':
            stats.update({
                'total_stores': Store.get_activas().count(),
                'total_staff': Staff.get_activos().count(),
                'total_suppliers': Supplier.get_activos().count(),
                'recent_sales': Sale.query.order_by(Sale.fecha.desc()).limit(10).all(),
                'low_stock_products': Product.query.filter(
                    Product.stock <= Product.stock
                ).limit(5).all()
            })
        
        elif current_user.rol.nombre == 'Vendedor':
            # Obtener la tienda del vendedor (si está asociado a una)
            user_store = None
            if current_user.empleado and current_user.empleado.tienda:
                user_store = current_user.empleado.tienda
                stats.update({
                    'store_sales_today': Sale.query.filter(
                        Sale.tienda_id == user_store.id_tienda,
                        Sale.fecha >= datetime.utcnow().date()
                    ).count(),
                    'store_recent_sales': Sale.query.filter(
                        Sale.tienda_id == user_store.id_tienda
                    ).order_by(Sale.fecha.desc()).limit(10).all(),
                })
        
        elif current_user.rol.nombre == 'Proveedor':
            # Obtener el proveedor del usuario
            user_supplier = None
            if current_user.empleado and current_user.empleado.proveedor:
                user_supplier = current_user.empleado.proveedor
                stats.update({
                    'supplier_orders': user_supplier.ordenes_proveedor,
                    'recent_orders': user_supplier.ordenes_proveedor.order_by(
                        db.desc('fecha_creacion')
                    ).limit(5).all() if user_supplier else []
                })

        return render_template('admin/dashboard.html', stats=stats, current_user=current_user)
    
    except Exception as e:
        # En caso de error, mostrar un dashboard básico
        return render_template('admin/dashboard.html', 
                             stats={'error': str(e)}, 
                             current_user=current_user)

@dashboard_bp.route('/sales-data', methods=['GET', 'POST'])
@login_required
def sales_data():
    """Endpoint de API para datos de ventas (para gráficos)"""
    form = SalesFilterForm()
    
    # Establecer valores predeterminados
    default_days = 30
    start_date = datetime.utcnow() - timedelta(days=default_days)
    end_date = datetime.utcnow()
    
    if form.validate_on_submit():
        try:
            # Usar los datos del formulario
            if form.days.data:
                days = form.days.data
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
            elif form.start_date.data and form.end_date.data:
                start_date = form.start_date.data
                end_date = form.end_date.data
                # Asegurar que end_date incluya todo el día
                end_date = end_date.replace(hour=23, minute=59, second=59)
        
        except Exception as e:
            flash(f'Error en los parámetros de fecha: {str(e)}', 'error')
            # Usar valores predeterminados en caso de error
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=default_days)
    
    elif request.method == 'GET':
        # Para solicitudes GET, usar parámetros de query string
        days = request.args.get('days', default_days, type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                # Si hay error en el formato, usar días predeterminados
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
        else:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
    
    try:
        # Consulta base
        query = Sale.query.filter(
            Sale.fecha >= start_date,
            Sale.fecha <= end_date
        )
        
        # Filtrar por tienda si el usuario es vendedor
        if current_user.rol.nombre == 'Vendedor' and current_user.empleado and current_user.empleado.tienda:
            query = query.filter(Sale.tienda_id == current_user.empleado.tienda.id_tienda)
        
        # Filtrar por proveedor si el usuario es proveedor
        elif current_user.rol.nombre == 'Proveedor' and current_user.empleado and current_user.empleado.proveedor:
            # Para proveedores, mostramos datos diferentes (no ventas)
            return jsonify({
                'success': True,
                'data': {
                    'labels': [],
                    'datasets': []
                },
                'message': 'Los proveedores no tienen datos de ventas'
            })
        
        # Agrupar por día y calcular totales
        sales_data = query.with_entities(
            db.func.date(Sale.fecha_venta).label('date'),
            db.func.count(Sale.id_venta).label('sales_count'),
            db.func.sum(Sale.total).label('sales_total')
        ).group_by(
            db.func.date(Sale.fecha_venta)
        ).order_by(
            db.func.date(Sale.fecha_venta)
        ).all()
        
        # Formatear datos para el gráfico
        dates = []
        sales_count = []
        sales_total = []
        
        for data in sales_data:
            dates.append(data.date.strftime('%Y-%m-%d'))
            sales_count.append(data.sales_count)
            sales_total.append(float(data.sales_total) if data.sales_total else 0)
        
        return jsonify({
            'success': True,
            'data': {
                'labels': dates,
                'datasets': [
                    {
                        'label': 'Ventas por día',
                        'data': sales_count,
                        'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                        'borderColor': 'rgba(54, 162, 235, 1)',
                        'borderWidth': 1
                    },
                    {
                        'label': 'Ingresos por día',
                        'data': sales_total,
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                        'borderColor': 'rgba(75, 192, 192, 1)',
                        'borderWidth': 1,
                        'type': 'line',
                        'yAxisID': 'y1'
                    }
                ]
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener datos de ventas: {str(e)}'
        }), 500

@dashboard_bp.route('/quick-stats', methods=['GET', 'POST'])
@login_required
def quick_stats():
    """Endpoint de API para estadísticas rápidas"""
    form = QuickStatsForm()
    
    if form.validate_on_submit():
        try:
            stats = {}
            
            # Estadísticas para administradores
            if current_user.rol.nombre == 'Administrador':
                stats = {
                    'total_users': User.query.filter_by(activo=True).count(),
                    'total_stores': Store.get_activas().count(),
                    'total_products': Product.get_activos().count(),
                    'today_sales': Sale.query.filter(
                        Sale.fecha >= datetime.utcnow().date()
                    ).count(),
                    'today_revenue': db.session.query(
                        db.func.sum(Sale.total)
                    ).filter(
                        Sale.fecha >= datetime.utcnow().date()
                    ).scalar() or 0
                }
            
            # Estadísticas para vendedores
            elif current_user.rol.nombre == 'Vendedor' and current_user.empleado and current_user.empleado.tienda:
                stats = {
                    'store_sales_today': Sale.query.filter(
                        Sale.tienda_id == current_user.empleado.tienda.id_tienda,
                        Sale.fecha >= datetime.utcnow().date()
                    ).count(),
                    'store_revenue_today': db.session.query(
                        db.func.sum(Sale.total)
                    ).filter(
                        Sale.tienda_id == current_user.empleado.tienda.id_tienda,
                        Sale.fecha >= datetime.utcnow().date()
                    ).scalar() or 0,
                    'store_clients': Client.query.filter(
                        Client.tienda_id == current_user.empleado.tienda.id_tienda
                    ).count()
                }
            
            # Estadísticas para proveedores
            elif current_user.rol.nombre == 'Proveedor' and current_user.empleado and current_user.empleado.proveedor:
                stats = {
                    'total_orders': current_user.empleado.proveedor.ordenes_proveedor.count(),
                    'pending_orders': current_user.empleado.proveedor.ordenes_proveedor.filter_by(
                        estado='pendiente'
                    ).count(),
                    'completed_orders': current_user.empleado.proveedor.ordenes_proveedor.filter_by(
                        estado='completada'
                    ).count()
                }
            
            return jsonify({
                'success': True,
                'data': stats
            })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error al obtener estadísticas: {str(e)}'
            }), 500
    
    # Para solicitudes GET, devolver datos básicos
    try:
        stats = {}
        
        # Estadísticas básicas para todos los roles
        if current_user.rol.nombre == 'Administrador':
            stats = {
                'total_users': User.query.filter_by(activo=True).count(),
                'total_stores': Store.get_activas().count(),
                'total_products': Product.get_activos().count(),
            }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener estadísticas: {str(e)}'
        }), 500

@dashboard_bp.route('/recent-activity', methods=['GET', 'POST'])
@login_required
def recent_activity():
    """Endpoint de API para actividad reciente"""
    form = DateRangeForm()
    
    # Valores predeterminados: últimos 7 días
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    
    if form.validate_on_submit():
        try:
            if form.start_date.data and form.end_date.data:
                start_date = form.start_date.data
                end_date = form.end_date.data
                # Asegurar que end_date incluya todo el día
                end_date = end_date.replace(hour=23, minute=59, second=59)
        except Exception as e:
            flash(f'Error en los parámetros de fecha: {str(e)}', 'error')
    
    try:
        activities = []
        
        # Actividad reciente para administradores
        if current_user.rol.nombre == 'Administrador':
            # Últimas ventas
            recent_sales = Sale.query.filter(
                Sale.fecha >= start_date,
                Sale.fecha <= end_date
            ).order_by(
                Sale.fecha.desc()
            ).limit(10).all()
            
            for sale in recent_sales:
                activities.append({
                    'type': 'sale',
                    'description': f'Venta #{sale.id_venta} por ${sale.total}',
                    'timestamp': sale.fecha,
                    'icon': 'shopping-cart'
                })
        
        # Actividad reciente para vendedores
        elif current_user.rol.nombre == 'Vendedor' and current_user.empleado and current_user.empleado.tienda:
            # Ventas recientes de la tienda
            recent_sales = Sale.query.filter(
                Sale.tienda_id == current_user.empleado.tienda.id_tienda,
                Sale.fecha >= start_date,
                Sale.fecha <= end_date
            ).order_by(
                Sale.fecha.desc()
            ).limit(10).all()
            
            for sale in recent_sales:
                activities.append({
                    'type': 'sale',
                    'description': f'Venta #{sale.id_venta} por ${sale.total}',
                    'timestamp': sale.fecha,
                    'icon': 'shopping-cart'
                })
        
        # Actividad reciente para proveedores
        elif current_user.rol.nombre == 'Proveedor' and current_user.empleado and current_user.empleado.proveedor:
            # Órdenes recientes
            recent_orders = current_user.empleado.proveedor.ordenes_proveedor.filter(
                SupplierOrder.fecha_creacion >= start_date,
                SupplierOrder.fecha_creacion <= end_date
            ).order_by(
                db.desc('fecha_creacion')
            ).limit(10).all()
            
            for order in recent_orders:
                activities.append({
                    'type': 'order',
                    'description': f'Orden #{order.id_orden_proveedor} - {order.estado}',
                    'timestamp': order.fecha_creacion,
                    'icon': 'truck'
                })
        
        # Ordenar actividades por timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': activities[:5]  # Solo las 5 más recientes
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener actividad reciente: {str(e)}'
        }), 500