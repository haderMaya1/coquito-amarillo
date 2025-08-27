from migrations.init_migration import app

if __name__ == '__main__':
    with app.app_context():
        print("Iniciando migración de la base de datos...")
        # La migración se ejecuta automáticamente al importar init_migration