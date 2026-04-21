def test_deposit_success(client, user_instance):
    user = user_instance
    payload = {
        "email": user.email,
        "mot_de_passe": "pass123",
        "montant": 100.0
    }
    response = client.post(f'/api/utilisateurs/{user.id}/deposit', json=payload)
    assert response.status_code == 200
    assert response.json['solde_initial'] == 1100.0

def test_withdraw_success(client, user_instance):
    user = user_instance
    payload = {
        "email": user.email,
        "mot_de_passe": "pass123",
        "montant": 50.0
    }
    response = client.post(f'/api/utilisateurs/{user.id}/withdraw', json=payload)
    assert response.status_code == 200
    assert response.json['solde_initial'] == 950.0

def test_withdraw_insufficient_funds(client, user_instance):
    user = user_instance
    payload = {
        "email": user.email,
        "mot_de_passe": "pass123",
        "montant": 2000.0
    }
    response = client.post(f'/api/utilisateurs/{user.id}/withdraw', json=payload)
    assert response.status_code == 400
    assert "Solde insuffisant" in response.json['message']