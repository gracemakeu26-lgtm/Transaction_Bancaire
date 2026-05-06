import pytest
from app import create_app
from extensions import db
from models import Utilisateur, Compte
from datetime import datetime

# These tests reuse the `app` & `client` fixtures from conftest.py when needed.

# 1) Create utilisateur paths

def test_create_utilisateur_invalid_json(client):
    resp = client.post('/api/utilisateurs', json={})
    assert resp.status_code == 400


def test_create_utilisateur_invalid_email(client):
    payload = {
        'nom': 'X', 'prenom': 'Y', 'email': 'bad-email', 'mot_de_passe': 'p',
        'telephone': '000', 'date_naissance': '1990-01-01', 'adresse': 'addr',
        'type_compte': 'courant', 'solde_initial': 0
    }
    resp = client.post('/api/utilisateurs', json=payload)
    assert resp.status_code == 400


def test_create_utilisateur_email_exists(client, init_utilisateur):
    # init_utilisateur creates test@example.com
    payload = {
        'nom': 'Test2', 'prenom': 'User2', 'email': 'test@example.com', 'mot_de_passe': 'p',
        'telephone': '000', 'date_naissance': '1990-01-01', 'adresse': 'addr',
        'type_compte': 'courant', 'solde_initial': 0
    }
    resp = client.post('/api/utilisateurs', json=payload)
    assert resp.status_code == 409


def test_create_utilisateur_invalid_date(client):
    payload = {
        'nom': 'X', 'prenom': 'Y', 'email': 'unique@example.com', 'mot_de_passe': 'p',
        'telephone': '000', 'date_naissance': '01-01-1990', 'adresse': 'addr',
        'type_compte': 'courant', 'solde_initial': 0
    }
    resp = client.post('/api/utilisateurs', json=payload)
    assert resp.status_code == 400


def test_create_utilisateur_success(client):
    payload = {
        'nom': 'New', 'prenom': 'User', 'email': 'newuser@example.com', 'mot_de_passe': 'p',
        'telephone': '000', 'date_naissance': '1995-05-05', 'adresse': 'addr',
        'type_compte': 'courant', 'solde_initial': 0
    }
    resp = client.post('/api/utilisateurs', json=payload)
    assert resp.status_code == 201


# 2) Get utilisateur

def test_get_utilisateur_not_found(client):
    resp = client.get('/api/utilisateurs/9999')
    assert resp.status_code == 404


def test_get_utilisateur_success(client, init_utilisateur):
    # init_utilisateur returns id via fixture
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    resp = client.get(f'/api/utilisateurs/{u.id}')
    assert resp.status_code == 200
    assert resp.get_json()['email'] == 'test@example.com'


# 3) Deposit (paths)

def test_deposit_invalid_json(client, init_utilisateur):
    # missing body
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    resp = client.post(f'/api/utilisateurs/{u.id}/deposit', json={})
    assert resp.status_code == 400


def test_deposit_invalid_montant(client, init_utilisateur):
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    payload = {'email': u.email, 'mot_de_passe': 'pass123', 'montant': -10}
    resp = client.post(f'/api/utilisateurs/{u.id}/deposit', json=payload)
    assert resp.status_code == 400


def test_deposit_auth_invalid(client, init_utilisateur):
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    payload = {'email': u.email, 'mot_de_passe': 'wrong', 'montant': 10}
    resp = client.post(f'/api/utilisateurs/{u.id}/deposit', json=payload)
    assert resp.status_code in (400, 401)


def test_deposit_not_allowed(client, init_utilisateur):
    # create another user and try to deposit on someone else's account
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
        u_id = u.id
        other = Utilisateur(nom='O', prenom='O', email='other@example.com', mot_de_passe='op',
                            telephone='0', date_naissance=datetime.strptime('1990-01-01','%Y-%m-%d').date(),
                            adresse='a', type_compte='courant', numero_compte='FRX', solde_initial=0)
        db.session.add(other)
        db.session.commit()
        other_email = other.email
    payload = {'email': other_email, 'mot_de_passe': 'op', 'montant': 10}
    resp = client.post(f'/api/utilisateurs/{u_id}/deposit', json=payload)
    assert resp.status_code == 403


def test_deposit_success(client, init_utilisateur):
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    payload = {'email': u.email, 'mot_de_passe': 'pass123', 'montant': 100}
    resp = client.post(f'/api/utilisateurs/{u.id}/deposit', json=payload)
    assert resp.status_code == 200


# 4) Withdraw (paths)

def test_withdraw_invalid_montant(client, init_utilisateur):
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    payload = {'email': u.email, 'mot_de_passe': 'pass123', 'montant': -5}
    resp = client.post(f'/api/utilisateurs/{u.id}/withdraw', json=payload)
    assert resp.status_code == 400


def test_withdraw_insufficient(client, init_utilisateur):
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    payload = {'email': u.email, 'mot_de_passe': 'pass123', 'montant': 999999}
    resp = client.post(f'/api/utilisateurs/{u.id}/withdraw', json=payload)
    assert resp.status_code == 400


def test_withdraw_success(client, init_utilisateur):
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
    payload = {'email': u.email, 'mot_de_passe': 'pass123', 'montant': 50}
    resp = client.post(f'/api/utilisateurs/{u.id}/withdraw', json=payload)
    assert resp.status_code == 200


# 5) Transactions global

def test_transactions_missing_compte_id(client):
    resp = client.post('/api/transactions', json={'type': 'depot', 'montant': 10})
    assert resp.status_code == 400


def test_transactions_compte_not_found(client):
    resp = client.post('/api/transactions', json={'compte_id': 9999, 'type': 'depot', 'montant': 10})
    assert resp.status_code in (400, 404)


def test_transactions_invalid_type(client, init_utilisateur):
    # create a compte first
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
        c = Compte(numero_compte='FRX', type_compte='courant', solde=100, utilisateur_id=u.id)
        db.session.add(c)
        db.session.commit()
        cid = c.id
    resp = client.post('/api/transactions', json={'compte_id': cid, 'type': 'invalid', 'montant': 10})
    assert resp.status_code == 400


def test_transactions_invalid_montant(client, init_utilisateur):
    with client.application.app_context():
        u = db.session.query(Utilisateur).filter_by(email='test@example.com').first()
        c = Compte(numero_compte='FRY', type_compte='courant', solde=100, utilisateur_id=u.id)
        db.session.add(c)
        db.session.commit()
        cid = c.id
    resp = client.post('/api/transactions', json={'compte_id': cid, 'type': 'depot', 'montant': -5})
    assert resp.status_code == 400
