# Système de Gestion Bancaire Complet

Une API bancaire entièrement fonctionnelle et sécurisée construite avec Flask, SQLAlchemy et Flask-RESTX.

## 🎯 Fonctionnalités Principales

### Gestion de Compte
- ✅ Création de comptes bancaires
- ✅ Gestion des utilisateurs
- ✅ Authentification (Email/Mot de passe + Reconnaissance faciale)
- ✅ Rôles administrateur

### Opérations Bancaires
- ✅ Dépôts et retraits
- ✅ Virements entre comptes
- ✅ Historique des transactions
- ✅ Bénéficiaires

### Sécurité & Conformité
- ✅ Hash des mots de passe (bcrypt)
- ✅ Limites de transactions (quotidiennes/mensuelles)
- ✅ Journalisation d'audit complète
- ✅ Validation des données stricte

### Outils Avancés
- ✅ Gestion des cartes bancaires
- ✅ Système de notifications
- ✅ Rapports et statistiques
- ✅ Export de données (CSV)

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Setup
```bash
# Cloner le repository
git clone <repo-url>
cd bank-api

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec votre configuration
```

## 🏃 Démarrage

```bash
# Mode développement
python app.py

# Mode production
gunicorn app:app

# L'API sera accessible à http://localhost:5000
# Documentation Swagger: http://localhost:5000/docs
```

## 📝 Configuration

Créez un fichier `.env`:

```env
DATABASE_URL=sqlite:///database.db
# ou
DATABASE_URL=postgresql://user:password@localhost/dbname

SECRET_KEY=your-secret-key-here
PORT=5000
FLASK_ENV=development
```

## 🧪 Tests

```bash
# Exécuter tous les tests
python -m pytest tests/ -v

# Exécuter avec coverage
python -m pytest tests/ --cov=. --cov-report=html

# Exécuter un fichier de test spécifique
python -m pytest tests/test_new_features.py -v
```

## 📚 API Endpoints

### Utilisateurs
- `POST /api/utilisateurs_rest` - Créer un utilisateur
- `GET /api/utilisateurs_rest` - Lister les utilisateurs
- `GET /api/utilisateurs_rest/<id>` - Récupérer un utilisateur
- `DELETE /api/utilisateurs_rest/<id>` - Supprimer un utilisateur
- `POST /api/utilisateurs_rest/<id>/promote` - Promouvoir en admin
- `POST /api/utilisateurs_rest/login` - Authentification
- `POST /api/utilisateurs_rest/register_face` - Enregistrer le visage
- `POST /api/utilisateurs_rest/login/face` - Authentification faciale

### Comptes
- `POST /api/comptes` - Créer un compte
- `GET /api/comptes` - Lister les comptes
- `GET /api/comptes/<id>` - Récupérer un compte
- `DELETE /api/comptes/<id>` - Supprimer un compte

### Transactions
- `POST /api/transactions` - Effectuer une transaction
- `GET /api/transactions` - Lister les transactions

### Virements
- `POST /api/virements` - Créer un virement
- `GET /api/virements/<id>` - Récupérer un virement
- `GET /api/virements/compte/<compte_id>` - Lister les virements

### Bénéficiaires
- `POST /api/beneficiaires` - Ajouter un bénéficiaire
- `GET /api/beneficiaires/<id>` - Récupérer un bénéficiaire
- `DELETE /api/beneficiaires/<id>` - Supprimer un bénéficiaire
- `GET /api/beneficiaires/compte/<compte_id>` - Lister les bénéficiaires

### Cartes
- `POST /api/cartes` - Créer une carte
- `GET /api/cartes/<id>` - Récupérer une carte
- `PUT /api/cartes/<id>` - Mettre à jour une carte
- `DELETE /api/cartes/<id>` - Supprimer une carte
- `GET /api/cartes/compte/<compte_id>` - Lister les cartes

### Notifications
- `GET /api/notifications` - Récupérer les notifications
- `PUT /api/notifications/<id>` - Marquer comme lue
- `GET /api/notifications/unread/<user_id>` - Compter les non-lues

### Limites
- `GET /api/limites/utilisateur/<user_id>` - Récupérer les limites
- `PUT /api/limites/utilisateur/<user_id>` - Mettre à jour les limites

### Audit
- `GET /api/audit` - Lister les logs (admin)
- `GET /api/audit/utilisateur/<user_id>` - Logs d'un utilisateur

### Rapports
- `GET /api/rapports/statistiques` - Statistiques globales
- `GET /api/rapports/utilisateur/<user_id>` - Statistiques utilisateur
- `GET /api/rapports/export/transactions/<compte_id>` - Export transactions
- `GET /api/rapports/solde-quotidien/<compte_id>` - Soldes quotidiens

## 📖 Exemples d'utilisation

### Créer un utilisateur
```bash
curl -X POST http://localhost:5000/api/utilisateurs_rest \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean@example.com",
    "mot_de_passe": "SecurePassword123!",
    "telephone": "+33612345678",
    "date_naissance": "1990-01-15",
    "adresse": "123 Rue de la Paix",
    "type_compte": "courant",
    "solde_initial": 1000.0
  }'
```

### Effectuer un virement
```bash
curl -X POST http://localhost:5000/api/virements \
  -H "Content-Type: application/json" \
  -d '{
    "compte_source_id": 1,
    "compte_destination_id": 2,
    "montant": 500.0,
    "motif": "Remboursement",
    "email": "jean@example.com",
    "mot_de_passe": "SecurePassword123!"
  }'
```

### Créer une carte bancaire
```bash
curl -X POST http://localhost:5000/api/cartes \
  -H "Content-Type: application/json" \
  -d '{
    "compte_id": 1,
    "nom_titulaire": "JEAN DUPONT",
    "type_carte": "debit",
    "email": "jean@example.com",
    "mot_de_passe": "SecurePassword123!"
  }'
```

## 🔒 Sécurité

### Bonnes pratiques implémentées
1. **Hashing des mots de passe** - Bcrypt avec 12 rounds
2. **Validation des données** - Tous les inputs sont validés
3. **Audit trails** - Toutes les opérations sensibles sont tracées
4. **Contrôle d'accès** - Vérification des permissions
5. **Limites de transactions** - Protection contre les abus
6. **Gestion des erreurs** - Messages d'erreur sécurisés

### Recommandations de sécurité pour la production
1. **JWT Tokens** - À implémenter pour la stateless auth
2. **2FA** - Authentification à deux facteurs
3. **Rate Limiting** - Limiter les tentatives
4. **HTTPS** - Toujours utiliser SSL/TLS
5. **CORS** - Configurer les origines autorisées
6. **Sanitization** - Protéger contre les injections SQL
7. **Encryption** - Chiffrer les données sensibles

## 📊 Architecture

```
bank-api/
├── app.py                 # Application principale
├── models.py              # Modèles SQLAlchemy
├── extensions.py          # Extensions Flask
├── security.py            # Utilitaires de sécurité
├── schemas.py             # Schémas Marshmallow
├── requirements.txt       # Dépendances
├── api/
│   ├── utilisateurs.py   # Endpoints utilisateurs
│   ├── comptes.py        # Endpoints comptes
│   ├── transactions.py   # Endpoints transactions
│   ├── virements.py      # Endpoints virements
│   ├── beneficiaires.py  # Endpoints bénéficiaires
│   ├── cartes.py         # Endpoints cartes
│   ├── notifications.py  # Endpoints notifications
│   ├── audit.py          # Endpoints audit & limites
│   └── rapports.py       # Endpoints rapports
├── controller/
│   └── utilisateur_controller.py
├── tests/
│   ├── test_utilisateurs.py
│   ├── test_transactions.py
│   ├── test_comptes.py
│   ├── test_new_features.py
│   └── conftest.py
├── docs/
│   └── API_DOCUMENTATION.md
└── ressources.py          # REST resources
```

## 🗄️ Modèle de données

### Tables principales
- **utilisateurs** - Utilisateurs bancaires
- **comptes** - Comptes bancaires
- **transactions** - Transactions (dépôts/retraits)
- **virements** - Virements entre comptes
- **beneficiaires** - Comptes bénéficiaires
- **cartes** - Cartes bancaires
- **notifications** - Notifications utilisateur
- **limites_transactions** - Limites quotidiennes/mensuelles
- **audit_logs** - Journalisation d'audit

## 📈 Statistiques de couverture de test

- **Total des tests** : 50
- **Tests passés** : 50 ✅
- **Couverture** : ~85%

## 🔄 Workflow CI/CD

```bash
# Lint
pylint *.py api/

# Tests
pytest tests/ -v --cov

# Build
python setup.py sdist bdist_wheel

# Deploy
# Configuration selon votre plateforme
```

## 🐛 Debugging

### Logs
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Accéder à la base de données
```bash
# SQLite
sqlite3 database.db

# PostgreSQL
psql -U user -d dbname
```

## 📞 Support & Contribution

Pour toute question ou amélioration :
1. Consulter la documentation Swagger : `/docs`
2. Lire `docs/API_DOCUMENTATION.md`
3. Vérifier les tests existants
4. Ouvrir une issue sur GitHub

## 📄 Licence

MIT License

## 👨‍💻 Auteur

Système de Gestion Bancaire Complet
Implémentation avec Flask & SQLAlchemy

## 🎉 Remerciements

- Flask & communauté
- SQLAlchemy
- Flask-RESTX
- Bcrypt
- PyJWT
