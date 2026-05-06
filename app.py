from flask import Flask, request, jsonify
from extensions import db, api
from sqlalchemy import inspect, text
from api.utilisateurs import utilisateurs_ns
from ressources import utilisateurs_ns as utilisateurs_rest_ns, comptes_ns
from schemas import ma
from models import Utilisateur
from dotenv import load_dotenv
from api.comptes import comptes_ns
from api.transactions import transactions_ns
from datetime import datetime
import os


load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)
    # Appliquer la configuration de test si fournie (priorité)
    if test_config:
        app.config.update(test_config)

    database_url = app.config.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')

    if database_url and not app.config.get('SQLALCHEMY_DATABASE_URI'):
        # 🔧 Nécessaire pour Neon : remplace "postgres://" par "postgresql://"
        print("Configuration de la base de données à partir de DATABASE_URL")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        # # Fallback en local (SQLite)
        # print("Aucune DATABASE_URL trouvée, utilisation de SQLite en local")
        # basedir = os.path.abspath(os.path.dirname(__file__))
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Configuration par défaut si non fournie
    basedir = os.path.abspath(os.path.dirname(__file__))
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url if database_url else 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    app.config.setdefault('SECRET_KEY', 'votre-cle-secrete-tres-longue-a-changer-en-production')
    
    # Initialisation des extensions
    db.init_app(app)
    ma.init_app(app)
    api.init_app(app)
    
    # Enregistrement des namespaces (endpoints)
    api.add_namespace(utilisateurs_ns, path='/api/utilisateurs')
    api.add_namespace(utilisateurs_rest_ns, path='/api/utilisateurs_rest')
    api.add_namespace(comptes_ns, path='/api/comptes')
    api.add_namespace(transactions_ns, path='/api/transactions')
    
    # Routes racine liées à l'instance app (assure disponibilité pour toutes les instances)
    @app.route('/')
    def home():
        return {"message": "Bienvenue sur l'API de Gestion des Transactions Bancaires", "docs": "/docs"}, 200
    
    # Création des tables (ne pas forcer en mode TESTING pour laisser les tests gérer
    # la création/suppression de la base en mémoire)
    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()
            _ensure_face_column_exists()
    
    return app

def _ensure_face_column_exists():
    inspector = inspect(db.engine)
    if 'utilisateurs' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('utilisateurs')}
        missing_columns = []
        if 'empreinte_faciale' not in columns:
            missing_columns.append("ALTER TABLE utilisateurs ADD COLUMN empreinte_faciale TEXT")
        if 'is_admin' not in columns:
            missing_columns.append("ALTER TABLE utilisateurs ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
        for sql in missing_columns:
            with db.engine.begin() as conn:
                conn.execute(text(sql))

app = create_app()

# Routes pour la gestion des comptes bancaires
@app.route('/comptes', methods=['POST'])
def creer_compte():
    """Crée un nouveau compte bancaire"""
    data = request.get_json()
    if not data:
        return jsonify({'erreur': 'Données JSON requises'}), 400
    
    required_fields = ['nom', 'prenom', 'email', 'mot_de_passe', 'telephone', 'date_naissance', 'adresse', 'type_compte', 'solde_initial']
    for field in required_fields:
        if field not in data:
            return jsonify({'erreur': f'Champ manquant : {field}'}), 400
    
    if Utilisateur.query.filter_by(email=data['email']).first():
        return jsonify({'erreur': 'Cet email est déjà utilisé'}), 409
    
    try:
        date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erreur': 'Format de date invalide. Utiliser YYYY-MM-DD'}), 400
    
    nouvel_utilisateur = Utilisateur(
        nom=data['nom'],
        prenom=data['prenom'],
        email=data['email'],
        mot_de_passe=data['mot_de_passe'],
        telephone=data['telephone'],
        date_naissance=date_naissance,
        adresse=data['adresse'],
        type_compte=data['type_compte'],
        numero_compte=generer_numero_compte(),
        solde_initial=data['solde_initial'],
        is_admin=False,
        statut=data.get('statut', 'actif')
    )
    
    db.session.add(nouvel_utilisateur)
    db.session.commit()
    
    return jsonify(nouvel_utilisateur.to_dict()), 201

@app.route('/comptes/<int:id>', methods=['PUT'])
def modifier_compte(id):
    """Modifie un compte bancaire existant"""
    utilisateur = Utilisateur.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({'erreur': 'Données JSON requises'}), 400
    
    # Mise à jour des champs modifiables
    if 'nom' in data: utilisateur.nom = data['nom']
    if 'prenom' in data: utilisateur.prenom = data['prenom']
    if 'mot_de_passe' in data: utilisateur.mot_de_passe = data['mot_de_passe']
    if 'telephone' in data: utilisateur.telephone = data['telephone']
    if 'adresse' in data: utilisateur.adresse = data['adresse']
    if 'statut' in data: utilisateur.statut = data['statut']
    # Note : email, date_naissance, type_compte et solde ne sont généralement pas modifiables sans procédure spécifique
    
    db.session.commit()
    return jsonify(utilisateur.to_dict()), 200

@app.route('/comptes/<int:id>', methods=['DELETE'])
def supprimer_compte(id):
    """Supprime un compte bancaire (admin seulement)"""
    utilisateur = Utilisateur.query.get_or_404(id)
    data = request.get_json()
    if not data or 'admin_email' not in data or 'admin_mot_de_passe' not in data:
        return jsonify({'erreur': 'Authentification admin requise'}), 400
    
    admin = Utilisateur.query.filter_by(email=data['admin_email']).first()
    if not admin or admin.mot_de_passe != data['admin_mot_de_passe'] or not admin.is_admin:
        return jsonify({'erreur': 'Accès administrateur requis'}), 403
    
    if utilisateur.is_admin:
        return jsonify({'erreur': 'Impossible de supprimer un autre administrateur'}), 403
    
    db.session.delete(utilisateur)
    db.session.commit()
    return '', 204

def generer_numero_compte():
    import random
    while True:
        numero = f"FR76{random.randint(10000000000, 99999999999)}"
        if not Utilisateur.query.filter_by(numero_compte=numero).first():
            return numero


if __name__ == '__main__':
    port = int(os.environ.get('PORT'))
    print(f"Démarrage de l'application sur le port {port}...")
    app.run(debug=True, host='0.0.0.0', port=port)