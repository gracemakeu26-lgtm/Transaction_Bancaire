import pytest
from app import create_app, db
from models import Compte

@pytest.fixture
def client():
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Créer un compte actif avec solde 1000
            c1 = Compte(id=1, statut='actif', solde=1000, numero_compte='FRTEST1')
            # Créer un compte inactif
            c2 = Compte(id=2, statut='inactif', solde=500, numero_compte='FRTEST2')
            db.session.add_all([c1, c2])
            db.session.commit()
        yield client

# P1 : Compte inactif
def test_transaction_compte_inactif(client):
    resp = client.post('/api/transactions', json={
        'compte_id': 2, 'type': 'depot', 'montant': 100
    })
    assert resp.status_code == 400
    assert 'compte non actif' in resp.get_json()['erreur']

# P2 : Retrait avec solde insuffisant
def test_retrait_solde_insuffisant(client):
    resp = client.post('/api/transactions', json={
        'compte_id': 1, 'type': 'retrait', 'montant': 2000
    })
    assert resp.status_code == 400
    assert 'solde insuffisant' in resp.get_json()['erreur']

# P3 : Retrait réussi
def test_retrait_reussi(client):
    resp = client.post('/api/transactions', json={
        'compte_id': 1, 'type': 'retrait', 'montant': 300
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['nouveau_solde'] == 700

# P4 : Dépôt réussi
def test_depot_reussi(client):
    resp = client.post('/api/transactions', json={
        'compte_id': 1, 'type': 'depot', 'montant': 500
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['nouveau_solde'] == 1500