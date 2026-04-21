import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime
from app import create_app
from extensions import db
from models import Utilisateur

@pytest.fixture
def app():
    """Crée une application Flask en mode test avec base SQLite en mémoire."""
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret'
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_utilisateur(app):
    """Crée un utilisateur de test et retourne son ID."""
    with app.app_context():
        user = Utilisateur(
            nom="Test",
            prenom="User",
            email="test@example.com",
            mot_de_passe="pass123",
            telephone="0123456789",
            date_naissance=datetime.strptime("1990-01-01", "%Y-%m-%d").date(),
            adresse="1 rue Test",
            type_compte="courant",
            numero_compte="FR76123456789",
            solde_initial=1000.0,
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        return user.id

@pytest.fixture
def user_instance(app, init_utilisateur):
    """Recharge l'utilisateur dans une session active."""
    with app.app_context():
        return db.session.get(Utilisateur, init_utilisateur)