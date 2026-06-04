import pytest
import json
from app import create_app
from extensions import db
from models import (
    Utilisateur, Compte, Transaction, Virement, Beneficiaire, 
    Notification, Carte, LimiteTransaction, AuditLog
)
from datetime import datetime

@pytest.fixture
def app():
    """Crée une application test"""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    }
    app = create_app(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Client de test"""
    return app.test_client()

@pytest.fixture
def setup_users_app(app):
    """Configure les utilisateurs de test dans le contexte de l'app"""
    with app.app_context():
        user1 = Utilisateur(
            nom='Dupont',
            prenom='Jean',
            email='jean@example.com',
            mot_de_passe='password123',
            telephone='+33612345678',
            date_naissance=datetime(1990, 1, 1).date(),
            adresse='123 Rue de la Paix',
            type_compte='courant',
            numero_compte='FR7612345678901234567890'
        )
        
        user2 = Utilisateur(
            nom='Martin',
            prenom='Marie',
            email='marie@example.com',
            mot_de_passe='password456',
            telephone='+33687654321',
            date_naissance=datetime(1995, 5, 15).date(),
            adresse='456 Rue de l\'Amour',
            type_compte='epargne',
            numero_compte='FR7698765432109876543210'
        )
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        compte1 = Compte(
            numero_compte='FR76001',
            type_compte='courant',
            solde=5000.0,
            utilisateur_id=user1.id,
            statut='actif'
        )
        
        compte2 = Compte(
            numero_compte='FR76002',
            type_compte='epargne',
            solde=10000.0,
            utilisateur_id=user2.id,
            statut='actif'
        )
        
        db.session.add(compte1)
        db.session.add(compte2)
        db.session.commit()
        
        yield {
            'user1_id': user1.id,
            'user2_id': user2.id,
            'compte1_id': compte1.id,
            'compte2_id': compte2.id
        }

# Tests pour les virements
def test_create_virement_success(client, app, setup_users_app):
    """Test la création d'un virement réussi"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'montant': 500.0,
        'motif': 'Remboursement',
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/virements', json=data)
    assert response.status_code == 201
    assert response.json['montant'] == 500.0
    assert response.json['statut'] == 'complétée'

def test_create_virement_insufficient_balance(client, app, setup_users_app):
    """Test un virement avec solde insuffisant"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'montant': 10000.0,
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/virements', json=data)
    assert response.status_code == 400

def test_create_virement_invalid_auth(client, app, setup_users_app):
    """Test un virement avec authentification invalide"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'montant': 500.0,
        'email': 'jean@example.com',
        'mot_de_passe': 'wrongpassword'
    }
    response = client.post('/api/virements', json=data)
    assert response.status_code == 401

def test_get_virement(client, app, setup_users_app):
    """Test la récupération d'un virement"""
    with app.app_context():
        virement = Virement(
            compte_source_id=setup_users_app['compte1_id'],
            compte_destination_id=setup_users_app['compte2_id'],
            montant=500.0,
            reference='TEST123456',
            statut='complétée'
        )
        db.session.add(virement)
        db.session.commit()
        virement_id = virement.id
        
    response = client.get(f'/api/virements/{virement_id}')
    assert response.status_code == 200
    assert response.json['montant'] == 500.0

# Tests pour les notifications
def test_get_user_notifications(client, app, setup_users_app):
    """Test la récupération des notifications d'un utilisateur"""
    with app.app_context():
        notif = Notification(
            utilisateur_id=setup_users_app['user1_id'],
            type_notification='virement_envoyé',
            message='Test notification',
            montant=100.0
        )
        db.session.add(notif)
        db.session.commit()
    
    response = client.get(
        '/api/notifications',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert len(response.json) > 0

def test_mark_notification_as_read(client, app, setup_users_app):
    """Test le marquage d'une notification comme lue"""
    with app.app_context():
        notif = Notification(
            utilisateur_id=setup_users_app['user1_id'],
            type_notification='virement_reçu',
            message='Test notification',
            montant=100.0,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
        notif_id = notif.id
    
    response = client.put(f'/api/notifications/{notif_id}')
    assert response.status_code == 200

# Tests pour les bénéficiaires
def test_add_beneficiaire(client, app, setup_users_app):
    """Test l'ajout d'un bénéficiaire"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'nom': 'Marie Martin',
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/beneficiaires', json=data)
    assert response.status_code == 201
    assert response.json['nom'] == 'Marie Martin'

def test_list_beneficiaires_compte(client, app, setup_users_app):
    """Test la liste des bénéficiaires d'un compte"""
    with app.app_context():
        beneficiaire = Beneficiaire(
            compte_source_id=setup_users_app['compte1_id'],
            compte_destination_id=setup_users_app['compte2_id'],
            nom='Test Beneficiaire'
        )
        db.session.add(beneficiaire)
        db.session.commit()
    
    response = client.get(
        f'/api/beneficiaires/compte/{setup_users_app["compte1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert len(response.json) > 0

# Tests pour les cartes
def test_create_carte(client, app, setup_users_app):
    """Test la création d'une carte bancaire"""
    data = {
        'compte_id': setup_users_app['compte1_id'],
        'nom_titulaire': 'JEAN DUPONT',
        'type_carte': 'debit',
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/cartes', json=data)
    assert response.status_code == 201
    assert response.json['type_carte'] == 'debit'
    assert 'numero_carte' in response.json

def test_list_cartes_compte(client, app, setup_users_app):
    """Test la liste des cartes d'un compte"""
    with app.app_context():
        carte = Carte(
            compte_id=setup_users_app['compte1_id'],
            numero_carte='4532123456789012',
            nom_titulaire='JEAN DUPONT',
            date_expiration='12/25',
            type_carte='debit',
            statut='actif'
        )
        db.session.add(carte)
        db.session.commit()
    
    response = client.get(
        f'/api/cartes/compte/{setup_users_app["compte1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert len(response.json) > 0

def test_update_carte_status(client, app, setup_users_app):
    """Test la mise à jour du statut d'une carte"""
    with app.app_context():
        carte = Carte(
            compte_id=setup_users_app['compte1_id'],
            numero_carte='4532123456789012',
            nom_titulaire='JEAN DUPONT',
            date_expiration='12/25',
            type_carte='debit',
            statut='actif'
        )
        db.session.add(carte)
        db.session.commit()
        carte_id = carte.id
    
    response = client.put(
        f'/api/cartes/{carte_id}',
        json={'statut': 'bloque'},
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200

# Tests pour les limites de transactions
def test_get_limite_utilisateur(client, app, setup_users_app):
    """Test la récupération des limites d'un utilisateur"""
    with app.app_context():
        limite = LimiteTransaction(
            utilisateur_id=setup_users_app['user1_id'],
            limite_quotidienne=10000.0,
            limite_mensuelle=50000.0
        )
        db.session.add(limite)
        db.session.commit()
    
    response = client.get(
        f'/api/limites/utilisateur/{setup_users_app["user1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert response.json['limite_quotidienne'] == 10000.0

def test_update_limite_utilisateur(client, app, setup_users_app):
    """Test la mise à jour des limites d'un utilisateur"""
    data = {
        'limite_quotidienne': 15000.0,
        'limite_mensuelle': 75000.0,
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.put(
        f'/api/limites/utilisateur/{setup_users_app["user1_id"]}',
        json=data
    )
    assert response.status_code == 200
    assert response.json['limite_quotidienne'] == 15000.0

# Tests pour l'audit
def test_get_audit_logs_admin(client, app, setup_users_app):
    """Test l'accès aux logs d'audit (admin seulement)"""
    with app.app_context():
        admin = Utilisateur(
            nom='Admin',
            prenom='Test',
            email='admin@example.com',
            mot_de_passe='adminpass',
            telephone='+33612341234',
            date_naissance=datetime(1980, 1, 1).date(),
            adresse='Admin Address',
            type_compte='courant',
            numero_compte='FR76ADMIN123',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    
    response = client.get(
        '/api/audit',
        query_string={
            'email': 'admin@example.com',
            'password': 'adminpass'
        }
    )
    assert response.status_code == 200

def test_get_audit_logs_non_admin_rejected(client, app, setup_users_app):
    """Test que les non-admins ne peuvent pas voir les logs"""
    response = client.get(
        '/api/audit',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 403

# Tests pour les rapports
def test_get_statistiques_utilisateur(client, app, setup_users_app):
    """Test les statistiques d'un utilisateur"""
    response = client.get(
        f'/api/rapports/utilisateur/{setup_users_app["user1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert 'solde_total' in response.json
    assert response.json['solde_total'] == 5000.0

def test_get_solde_quotidien(client, app, setup_users_app):
    """Test l'historique des soldes quotidiens"""
    response = client.get(
        f'/api/rapports/solde-quotidien/{setup_users_app["compte1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123',
            'jours': 30
        }
    )
    assert response.status_code == 200
    assert 'solde_actuel' in response.json


# Tests pour les virements
def test_create_virement_success(client, app, setup_users_app):
    """Test la création d'un virement réussi"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'montant': 500.0,
        'motif': 'Remboursement',
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/virements', json=data)
    assert response.status_code == 201
    assert response.json['montant'] == 500.0
    assert response.json['statut'] == 'complétée'

def test_create_virement_insufficient_balance(client, app, setup_users_app):
    """Test un virement avec solde insuffisant"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'montant': 10000.0,
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/virements', json=data)
    assert response.status_code == 400

def test_create_virement_invalid_auth(client, app, setup_users_app):
    """Test un virement avec authentification invalide"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'montant': 500.0,
        'email': 'jean@example.com',
        'mot_de_passe': 'wrongpassword'
    }
    response = client.post('/api/virements', json=data)
    assert response.status_code == 401

def test_get_virement(client, app, setup_users_app):
    """Test la récupération d'un virement"""
    with app.app_context():
        virement = Virement(
            compte_source_id=setup_users_app['compte1_id'],
            compte_destination_id=setup_users_app['compte2_id'],
            montant=500.0,
            reference='TEST123456',
            statut='complétée'
        )
        db.session.add(virement)
        db.session.commit()
        virement_id = virement.id
        
    response = client.get(f'/api/virements/{virement_id}')
    assert response.status_code == 200
    assert response.json['montant'] == 500.0

# Tests pour les notifications
def test_get_user_notifications(client, app, setup_users_app):
    """Test la récupération des notifications d'un utilisateur"""
    with app.app_context():
        notif = Notification(
            utilisateur_id=setup_users_app['user1_id'],
            type_notification='virement_envoyé',
            message='Test notification',
            montant=100.0
        )
        db.session.add(notif)
        db.session.commit()
    
    response = client.get(
        '/api/notifications',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert len(response.json) > 0

def test_mark_notification_as_read(client, app, setup_users_app):
    """Test le marquage d'une notification comme lue"""
    with app.app_context():
        notif = Notification(
            utilisateur_id=setup_users_app['user1_id'],
            type_notification='virement_reçu',
            message='Test notification',
            montant=100.0,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
        notif_id = notif.id
    
    response = client.put(f'/api/notifications/{notif_id}')
    assert response.status_code == 200

# Tests pour les bénéficiaires
def test_add_beneficiaire(client, app, setup_users_app):
    """Test l'ajout d'un bénéficiaire"""
    data = {
        'compte_source_id': setup_users_app['compte1_id'],
        'compte_destination_id': setup_users_app['compte2_id'],
        'nom': 'Marie Martin',
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/beneficiaires', json=data)
    assert response.status_code == 201
    assert response.json['nom'] == 'Marie Martin'

def test_list_beneficiaires_compte(client, app, setup_users_app):
    """Test la liste des bénéficiaires d'un compte"""
    with app.app_context():
        beneficiaire = Beneficiaire(
            compte_source_id=setup_users_app['compte1_id'],
            compte_destination_id=setup_users_app['compte2_id'],
            nom='Test Beneficiaire'
        )
        db.session.add(beneficiaire)
        db.session.commit()
    
    response = client.get(
        f'/api/beneficiaires/compte/{setup_users_app["compte1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert len(response.json) > 0

# Tests pour les cartes
def test_create_carte(client, app, setup_users_app):
    """Test la création d'une carte bancaire"""
    data = {
        'compte_id': setup_users_app['compte1_id'],
        'nom_titulaire': 'JEAN DUPONT',
        'type_carte': 'debit',
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.post('/api/cartes', json=data)
    assert response.status_code == 201
    assert response.json['type_carte'] == 'debit'
    assert 'numero_carte' in response.json

def test_list_cartes_compte(client, app, setup_users_app):
    """Test la liste des cartes d'un compte"""
    with app.app_context():
        carte = Carte(
            compte_id=setup_users_app['compte1_id'],
            numero_carte='4532123456789012',
            nom_titulaire='JEAN DUPONT',
            date_expiration='12/25',
            type_carte='debit',
            statut='actif'
        )
        db.session.add(carte)
        db.session.commit()
    
    response = client.get(
        f'/api/cartes/compte/{setup_users_app["compte1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert len(response.json) > 0

def test_update_carte_status(client, app, setup_users_app):
    """Test la mise à jour du statut d'une carte"""
    with app.app_context():
        carte = Carte(
            compte_id=setup_users_app['compte1_id'],
            numero_carte='4532123456789012',
            nom_titulaire='JEAN DUPONT',
            date_expiration='12/25',
            type_carte='debit',
            statut='actif'
        )
        db.session.add(carte)
        db.session.commit()
        carte_id = carte.id
    
    response = client.put(
        f'/api/cartes/{carte_id}',
        json={'statut': 'bloque'},
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200

# Tests pour les limites de transactions
def test_get_limite_utilisateur(client, app, setup_users_app):
    """Test la récupération des limites d'un utilisateur"""
    with app.app_context():
        limite = LimiteTransaction(
            utilisateur_id=setup_users_app['user1_id'],
            limite_quotidienne=10000.0,
            limite_mensuelle=50000.0
        )
        db.session.add(limite)
        db.session.commit()
    
    response = client.get(
        f'/api/limites/utilisateur/{setup_users_app["user1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert response.json['limite_quotidienne'] == 10000.0

def test_update_limite_utilisateur(client, app, setup_users_app):
    """Test la mise à jour des limites d'un utilisateur"""
    data = {
        'limite_quotidienne': 15000.0,
        'limite_mensuelle': 75000.0,
        'email': 'jean@example.com',
        'mot_de_passe': 'password123'
    }
    response = client.put(
        f'/api/limites/utilisateur/{setup_users_app["user1_id"]}',
        json=data
    )
    assert response.status_code == 200
    assert response.json['limite_quotidienne'] == 15000.0

# Tests pour l'audit
def test_get_audit_logs_admin(client, app, setup_users_app):
    """Test l'accès aux logs d'audit (admin seulement)"""
    with app.app_context():
        admin = Utilisateur(
            nom='Admin',
            prenom='Test',
            email='admin@example.com',
            mot_de_passe='adminpass',
            telephone='+33612341234',
            date_naissance=datetime(1980, 1, 1).date(),
            adresse='Admin Address',
            type_compte='courant',
            numero_compte='FR76ADMIN123',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    
    response = client.get(
        '/api/audit',
        query_string={
            'email': 'admin@example.com',
            'password': 'adminpass'
        }
    )
    assert response.status_code == 200

def test_get_audit_logs_non_admin_rejected(client, app, setup_users_app):
    """Test que les non-admins ne peuvent pas voir les logs"""
    response = client.get(
        '/api/audit',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 403

# Tests pour les rapports
def test_get_statistiques_utilisateur(client, app, setup_users_app):
    """Test les statistiques d'un utilisateur"""
    response = client.get(
        f'/api/rapports/utilisateur/{setup_users_app["user1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123'
        }
    )
    assert response.status_code == 200
    assert 'solde_total' in response.json
    assert response.json['solde_total'] == 5000.0

def test_get_solde_quotidien(client, app, setup_users_app):
    """Test l'historique des soldes quotidiens"""
    response = client.get(
        f'/api/rapports/solde-quotidien/{setup_users_app["compte1_id"]}',
        query_string={
            'email': 'jean@example.com',
            'password': 'password123',
            'jours': 30
        }
    )
    assert response.status_code == 200
    assert 'solde_actuel' in response.json
