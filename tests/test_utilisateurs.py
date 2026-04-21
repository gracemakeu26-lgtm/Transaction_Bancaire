from datetime import datetime

def test_create_utilisateur(client):
    payload = {
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean@example.com",
        "mot_de_passe": "secret123",
        "telephone": "0612345678",
        "date_naissance": "1985-05-10",
        "adresse": "10 rue de Paris",
        "type_compte": "courant",
        "solde_initial": 500.0
    }
    response = client.post('/api/utilisateurs', json=payload)
    assert response.status_code == 201

def test_update_utilisateur(client, user_instance):
    user = user_instance
    payload = {"nom": "NouveauNom"}
    response = client.put(f'/api/utilisateurs/{user.id}', json=payload)
    assert response.status_code == 200
    assert response.json['nom'] == "NouveauNom"

def test_delete_utilisateur(client, user_instance):
    from models import Utilisateur
    from extensions import db
    from app import create_app
    from datetime import datetime

    user = user_instance

    # Création d'un admin (dans la même session)
    with client.application.app_context():
        admin = Utilisateur(
            nom="Admin", prenom="Super", email="admin@bank.com",
            mot_de_passe="adminpass", telephone="000",
            date_naissance=datetime.now().date(),
            adresse="Siège", type_compte="courant",
            numero_compte="ADMIN001", solde_initial=0,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id

    payload = {"admin_email": "admin@bank.com", "admin_mot_de_passe": "adminpass"}
    response = client.delete(f'/api/utilisateurs/{user.id}', json=payload)
    assert response.status_code == 204