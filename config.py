import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Asegurar que el directorio instance existe
instance_dir = os.path.join(basedir, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'claveSegura'
    instance_dir = os.path.join(basedir, 'instance')
    db_path = os.path.join(instance_dir, 'database.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.abspath(db_path)}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    #Limit low Stock
    LOW_STOCK_THRESHOLD = 2
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY') or 'otraClaveSegura'
    WTF_CSRF_TIME_LIMIT = 3600

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}