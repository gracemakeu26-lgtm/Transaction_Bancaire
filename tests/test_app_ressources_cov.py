import os
import pytest
from app import create_app
from extensions import db
from models import Utilisateur
from ressources import calculate_face_template


def test_create_app_with_database_url_env(monkeypatch):
    # Ensure DATABASE_URL replacement code path runs but avoid creating real DB by setting TESTING=True
    monkeypatch.setenv('DATABASE_URL', 'postgres://user:pass@localhost/dbname')
    app = create_app(test_config={'TESTING': True})
    # create_app should replace postgres:// with postgresql://
    assert app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql://')


def test_home_route(client):
    resp = client.get('/')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'Bienvenue' in data['message']
    assert '/docs' in data['docs']


def test_calculate_face_template_variants():
    s1 = '  abc123 '\
        .strip()
    h1 = calculate_face_template('abc123')
    h2 = calculate_face_template('  abc123  ')
    assert h1 == h2
    assert isinstance(h1, str) and len(h1) == 64


def test_create_user_and_admin_promote(client):
    # create a user and an admin via the API then promote
    payload_user = {
        'nom': 'P', 'prenom': 'U', 'email': 'promote@example.com', 'mot_de_passe': 'pwd',
        'telephone': '0', 'date_naissance': '1990-01-01', 'adresse': 'addr', 'type_compte': 'courant', 'solde_initial': 0
    }
    r = client.post('/api/utilisateurs_rest', json=payload_user)
    assert r.status_code == 201

    # create admin user directly in DB (easier) and ensure credentials
    with client.application.app_context():
        from datetime import datetime
        admin = Utilisateur(nom='A', prenom='Admin', email='admin@example.com', mot_de_passe='adminpw',
                             telephone='0', date_naissance=datetime.strptime('1990-01-01', '%Y-%m-%d').date(), adresse='a', type_compte='courant',
                             numero_compte='FRADMIN', solde_initial=0, is_admin=True)
        db.session.add(admin)
        db.session.commit()
    # promote created user using admin creds
    # find created user id
    with client.application.app_context():
        user = db.session.query(Utilisateur).filter_by(email='promote@example.com').first()
        uid = user.id
    resp = client.post(f'/api/utilisateurs_rest/{uid}/promote', json={'admin_email': 'admin@example.com', 'admin_mot_de_passe': 'adminpw'})
    assert resp.status_code == 200
    assert resp.get_json().get('message')
