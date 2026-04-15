from flask import Flask
from extensions import db, api
from sqlalchemy import inspect, text
from api.utilisateurs import utilisateurs_ns
from ressources import utilisateurs_ns as utilisateurs_rest_ns
from schemas import ma
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'votre-cle-secrete-tres-longue-a-changer-en-production'
    
    # Initialisation des extensions
    db.init_app(app)
    ma.init_app(app)
    api.init_app(app)
    
    # Enregistrement des namespaces (endpoints)
    api.add_namespace(utilisateurs_ns, path='/api/utilisateurs')
    api.add_namespace(utilisateurs_rest_ns, path='/api/utilisateurs_rest')
    
    # Création des tables
    with app.app_context():
        db.create_all()
        _ensure_face_column_exists()
    
    return app

def _ensure_face_column_exists():
    inspector = inspect(db.engine)
    if 'utilisateurs' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('utilisateurs')]
        if 'empreinte_faciale' not in columns:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE utilisateurs ADD COLUMN empreinte_faciale TEXT'))

app = create_app()

@app.route('/')
def home():
    return {"message": "Bienvenue sur l'API de Gestion des Transactions Bancaires", "docs": "/docs"}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)