# API de Gestion Bancaire Complète - Documentation

## Vue d'ensemble

L'API de gestion bancaire offre une suite complète de fonctionnalités pour gérer les comptes bancaires, les transactions, les virements, les notifications et bien d'autres services.

## Nouvelles Fonctionnalités Implémentées

### 1. **Virements Bancaires** (`/api/virements`)

Permet les transferts d'argent entre comptes bancaires.

#### Endpoints:
- `POST /api/virements` - Créer un virement
- `GET /api/virements/<id>` - Récupérer les détails d'un virement
- `GET /api/virements/compte/<compte_id>` - Lister les virements d'un compte
- `GET /api/virements/<reference>` - Récupérer par référence

#### Exemple:
```json
POST /api/virements
{
  "compte_source_id": 1,
  "compte_destination_id": 2,
  "montant": 500.0,
  "motif": "Remboursement",
  "email": "user@example.com",
  "mot_de_passe": "password"
}
```

### 2. **Notifications** (`/api/notifications`)

Système de notification en temps réel pour les événements bancaires.

#### Endpoints:
- `GET /api/notifications` - Récupérer les notifications de l'utilisateur
- `GET /api/notifications/<id>` - Récupérer une notification spécifique
- `PUT /api/notifications/<id>` - Marquer comme lue
- `GET /api/notifications/utilisateur/<user_id>` - Lister (admin)
- `GET /api/notifications/unread/<user_id>` - Compter les non-lues

#### Authentification:
Query parameters: `email`, `password`

### 3. **Bénéficiaires** (`/api/beneficiaires`)

Gérer la liste des bénéficiaires pour les virements rapides.

#### Endpoints:
- `POST /api/beneficiaires` - Ajouter un bénéficiaire
- `GET /api/beneficiaires/<id>` - Récupérer un bénéficiaire
- `DELETE /api/beneficiaires/<id>` - Supprimer un bénéficiaire
- `GET /api/beneficiaires/compte/<compte_id>` - Lister les bénéficiaires d'un compte

#### Exemple:
```json
POST /api/beneficiaires
{
  "compte_source_id": 1,
  "compte_destination_id": 2,
  "nom": "Marie Martin",
  "email": "user@example.com",
  "mot_de_passe": "password"
}
```

### 4. **Cartes Bancaires** (`/api/cartes`)

Gestion complète des cartes bancaires (débit, crédit, virtuelles).

#### Endpoints:
- `POST /api/cartes` - Créer une carte
- `GET /api/cartes/<id>` - Récupérer une carte
- `PUT /api/cartes/<id>` - Mettre à jour le statut
- `DELETE /api/cartes/<id>` - Supprimer une carte
- `GET /api/cartes/compte/<compte_id>` - Lister les cartes d'un compte
- `GET /api/cartes/<numero_carte>` - Récupérer par numéro

#### Types de cartes:
- `debit` - Carte de débit
- `credit` - Carte de crédit
- `virtuelle` - Carte virtuelle

#### Statuts:
- `actif` - Active
- `bloque` - Bloquée
- `expiree` - Expirée

### 5. **Limites de Transactions** (`/api/limites`)

Définir et gérer les limites quotidiennes et mensuelles.

#### Endpoints:
- `GET /api/limites` - Lister toutes les limites (admin)
- `GET /api/limites/utilisateur/<user_id>` - Récupérer les limites
- `PUT /api/limites/utilisateur/<user_id>` - Mettre à jour les limites

#### Défauts:
- Limite quotidienne: 10,000€
- Limite mensuelle: 50,000€

### 6. **Audit & Logs** (`/api/audit`)

Journalisation de toutes les opérations sensibles.

#### Endpoints:
- `GET /api/audit` - Lister tous les logs (admin)
- `GET /api/audit/utilisateur/<user_id>` - Logs d'un utilisateur (admin)

#### Actions tracées:
- Virements
- Transactions
- Modifications de limites
- Tentatives de connexion échouées

### 7. **Rapports & Statistiques** (`/api/rapports`)

Générer des rapports et statistiques bancaires.

#### Endpoints:
- `GET /api/rapports/statistiques` - Stats globales (admin)
- `GET /api/rapports/utilisateur/<user_id>` - Stats d'un utilisateur
- `GET /api/rapports/export/transactions/<compte_id>` - Export CSV
- `GET /api/rapports/export/virements/<compte_id>` - Export CSV
- `GET /api/rapports/solde-quotidien/<compte_id>` - Historique des soldes

## Modèles de Données

### Virement
```python
{
  "id": int,
  "compte_source_id": int,
  "compte_destination_id": int,
  "montant": float,
  "date_virement": datetime,
  "statut": "en_attente|complétée|rejetée",
  "motif": string,
  "reference": string  # Unique
}
```

### Notification
```python
{
  "id": int,
  "utilisateur_id": int,
  "type_notification": string,
  "message": string,
  "date_creation": datetime,
  "is_read": boolean,
  "montant": float
}
```

### Carte
```python
{
  "id": int,
  "compte_id": int,
  "numero_carte": string,
  "nom_titulaire": string,
  "date_expiration": "MM/YY",
  "type_carte": "debit|credit|virtuelle",
  "statut": "actif|bloque|expiree",
  "date_emission": datetime
}
```

### LimiteTransaction
```python
{
  "id": int,
  "utilisateur_id": int,
  "limite_quotidienne": float,
  "limite_mensuelle": float,
  "montant_quotidien": float,
  "montant_mensuel": float,
  "date_reset_quotidien": datetime,
  "date_reset_mensuel": datetime
}
```

### AuditLog
```python
{
  "id": int,
  "utilisateur_id": int,
  "type_action": string,
  "description": string,
  "date_action": datetime,
  "adresse_ip": string,
  "statut_action": "succès|échec"
}
```

## Authentification

Deux méthodes principales:

### 1. Email/Mot de passe
```python
{
  "email": "user@example.com",
  "mot_de_passe": "password123"
}
```

### 2. JWT (À implémenter)
```
Authorization: Bearer <token>
```

## Codes d'Erreur

- `400` - Requête invalide
- `401` - Non authentifié
- `403` - Non autorisé (accès admin requis)
- `404` - Ressource non trouvée
- `409` - Conflit (email existant, etc.)

## Sécurité

### Fonctionnalités de sécurité:
- ✅ Hash des mots de passe (bcrypt)
- ✅ JWT support prêt
- ✅ Audit trails complets
- ✅ Limites de transactions
- ✅ Contrôles d'accès granulaires
- ✅ Validation des données
- ✅ Authentification pour toutes les opérations sensibles

### Prochaines améliorations recommandées:
1. Implémenter JWT tokens stateless
2. Ajouter 2FA (authentification à deux facteurs)
3. Rate limiting sur les endpoints sensibles
4. Chiffrement des numéros de carte
5. SSL/TLS obligatoire
6. Détection des fraudes en temps réel

## Exemples de Workflow

### Scénario 1: Effectuer un virement

```bash
# 1. Créer un bénéficiaire (optionnel)
curl -X POST http://localhost:5000/api/beneficiaires \
  -H "Content-Type: application/json" \
  -d '{
    "compte_source_id": 1,
    "compte_destination_id": 2,
    "nom": "Marie",
    "email": "jean@example.com",
    "mot_de_passe": "password123"
  }'

# 2. Effectuer le virement
curl -X POST http://localhost:5000/api/virements \
  -H "Content-Type: application/json" \
  -d '{
    "compte_source_id": 1,
    "compte_destination_id": 2,
    "montant": 500.0,
    "motif": "Remboursement",
    "email": "jean@example.com",
    "mot_de_passe": "password123"
  }'

# 3. Consulter les notifications
curl "http://localhost:5000/api/notifications?email=marie@example.com&password=password456"
```

### Scénario 2: Créer et gérer une carte

```bash
# 1. Créer une carte
curl -X POST http://localhost:5000/api/cartes \
  -H "Content-Type: application/json" \
  -d '{
    "compte_id": 1,
    "nom_titulaire": "JEAN DUPONT",
    "type_carte": "debit",
    "email": "jean@example.com",
    "mot_de_passe": "password123"
  }'

# 2. Bloquer la carte
curl -X PUT "http://localhost:5000/api/cartes/1?email=jean@example.com&password=password123" \
  -H "Content-Type: application/json" \
  -d '{
    "statut": "bloque"
  }'
```

## Tests

Tous les tests sont localisés dans `tests/test_new_features.py`.

```bash
# Exécuter tous les tests
python -m pytest tests/ -v

# Exécuter uniquement les nouveaux tests
python -m pytest tests/test_new_features.py -v

# Coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Changelog

### Version 1.1.0 (Nouvelle)
- ✅ Virements bancaires
- ✅ Notifications
- ✅ Bénéficiaires
- ✅ Gestion des cartes
- ✅ Limites de transactions
- ✅ Audit logs
- ✅ Rapports et statistiques
- ✅ Support bcrypt pour mots de passe

### Version 1.0.0 (Existant)
- Gestion des utilisateurs
- Gestion des comptes
- Transactions (dépôts/retraits)
- Authentification faciale

## Support

Pour toute question, veuillez consulter la documentation complète à `/docs` (Swagger UI).
