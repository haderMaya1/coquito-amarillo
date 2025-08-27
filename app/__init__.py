from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from flask_wtf import CSRFProtect

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()

# Añadir esto después de la configuración del login_manager
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    from app.routes.products import products_bp
    from app.routes.clients import clients_bp
    from app.routes.sales import sales_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.staff import staff_bp
    from app.routes.cities import cities_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(cities_bp, url_prefix='/cities')
    
    # En create_app, después de inicializar la base de datos
    with app.app_context():
        db.create_all()
        
        # Solo crear datos iniciales si no existen roles
        from app.models import Role
        if not Role.query.first():
            from app.seeds import init_db
            init_db()
            
    # ... después de crear la app
    app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'  # Debe ser una clave segura
    app.config['WTF_CSRF_SECRET_KEY'] = 'otra-clave-secreta-csrf'  # Para protección CSRF

    csrf = CSRFProtect(app)
        
    return app