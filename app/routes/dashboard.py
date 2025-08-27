from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Product, Sale, Client
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def dashboard():
    total_products = Product.query.count()
    total_sales = Sale.query.count()
    total_clients = Client.query.count()
    
    return render_template('admin/dashboard.html', 
                         total_products=total_products,
                         total_sales=total_sales,
                         total_clients=total_clients)