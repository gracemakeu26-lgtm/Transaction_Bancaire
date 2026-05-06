# CFG et chemins pour 5 fonctionnalités choisies

Fonctionnalités choisies:
1. Créer un utilisateur — `POST /api/utilisateurs`
2. Récupérer un utilisateur — `GET /api/utilisateurs/<id>`
3. Dépôt sur utilisateur — `POST /api/utilisateurs/<id>/deposit`
4. Retrait sur utilisateur — `POST /api/utilisateurs/<id>/withdraw`
5. Transaction globale — `POST /api/transactions`

---

**1) Créer un utilisateur (POST /api/utilisateurs)**

CFG (textuel):
- Start -> Read JSON body
  - if not JSON -> return 400 (invalid JSON)
  - validate email format -> if invalid -> return 400
  - if email exists -> return 409
  - parse date_naissance -> if invalid -> return 400
  - create Utilisateur -> commit -> return 201

Chemins (liste):
A. (invalid JSON) -> 400
B. (invalid email) -> 400
C. (email exists) -> 409
D. (invalid date format) -> 400
E. (success) -> 201


**2) Récupérer un utilisateur (GET /api/utilisateurs/<id>)**

CFG:
- Start -> Query by id
  - if not found -> 404
  - else -> 200 + utilisateur

Chemins:
A. (utilisateur existe) -> 200
B. (utilisateur manquant) -> 404


**3) Dépôt (POST /api/utilisateurs/<id>/deposit)**

CFG:
- Start -> get utilisateur by id (404 if not)
  - read body -> if invalid JSON -> 400
  - validate montant: if None or <=0 -> 400
  - auth_user(email, mot_de_passe):
    - if missing creds -> 400
    - if invalid creds -> 401
  - if auteur.id != utilisateur.id and not auteur.is_admin -> 403
  - utilisateur.deposit(montant): may raise ValueError -> catch -> 400
  - commit -> return 200

Chemins:
A. invalid JSON -> 400
B. montant invalid (None or <=0) -> 400
C. auth missing -> 400
D. auth invalid -> 401
E. auth valid but not allowed -> 403
F. deposit success -> 200


**4) Retrait (POST /api/utilisateurs/<id>/withdraw)**

CFG similar to deposit, plus solde insuffisant branch inside `withdraw` raising ValueError:

Chemins:
A. invalid JSON -> 400
B. montant invalid -> 400
C. auth invalid/missing -> 400/401
D. not allowed (not owner, not admin) -> 403
E. solde insuffisant -> 400
F. withdraw success -> 200


**5) Transaction globale (POST /api/transactions)**

CFG:
- Start -> read JSON -> if invalid -> 400
- require `compte_id` -> if missing -> 400
- lookup compte -> if not found -> 404
- if compte.statut != 'actif' -> 400
- montant validation -> 400 if invalid
- type validation ("retrait" or "depot") -> 400
- if retrait and solde < montant -> 400
- apply change, create Transaction, commit -> 201

Chemins:
A. invalid JSON -> 400
B. missing compte_id -> 400
C. compte not found -> 404
D. compte not actif -> 400
E. montant invalid -> 400
F. type invalid -> 400
G. retrait solde insuffisant -> 400
H. retrait success -> 201
I. depot success -> 201

---

Couverture observée (extrait de `coverage report --branch`):

```
Name                         Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------------
api/comptes.py                  38     15      2      0    58%   19, 28-38, 48-4
9, 55-60                                                                        api/transactions.py             44      8     18      6    77%   27, 31, 35, 42,
 45-46, 48, 52                                                                  api/utilisateurs.py            164     40     38     16    69%   10, 13, 17-20, 
77->75, 87-91, 100, 104, 108, 112-113, 143-144, 154, 175, 180, 182, 197, 202, 205, 208-209, 222, 227, 230, 244-253                                              app.py                         115     56     38      7    47%   29, 42, 68->exi
t, 72, 74, 76-77, 83, 89-124, 129-144, 149-163, 166-170, 174-176                extensions.py                    4      0      0      0   100%
models.py                       49      2      6      2    93%   42, 47
...
TOTAL                          727    244    148     31    60%
```

---

Prochaines étapes réalisées dans le dépôt:
- Ajout des tests couvrant chaque chemin listé ci-dessous (fichier `tests/test_cfg_paths.py`).
- Vous pouvez exécuter `coverage run --branch -m pytest && coverage report -m` pour régénérer le tableau.

Résultat de la couverture après ajout des tests (extrait):

```
Name                         Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------------
api/comptes.py                  38     15      2      0    58%   19, 28-38, 48-4
9, 55-60                                                                        api/transactions.py             44      4     18      2    90%   27, 42, 45-46
api/utilisateurs.py            164     32     38     12    75%   10, 17-20, 77->
75, 87-91, 100, 154, 175, 180, 182, 197, 202, 208-209, 222, 227, 230, 244-253   app.py                         115     56     38      7    47%   29, 42, 68->exi
t, 72, 74, 76-77, 83, 89-124, 129-144, 149-163, 166-170, 174-176                extensions.py                    4      0      0      0   100%
models.py                       49      2      6      2    93%   42, 47
...
TOTAL                          836    232    148     23    67%
```

Fichiers ajoutés / modifiés pour ces travaux:
- `api/transactions.py` : validations plus strictes et réponses formatées
- `app.py` : respect de `test_config` et évitement de `db.create_all()` en mode `TESTING`
- `models.py` : champs `Compte` rendus `nullable` pour compatibilité fixtures
- `tests/test_cfg_paths.py` : tests détaillés pour tous les chemins CFG
- `tests/test_transaction.py` : ajustement pour utiliser `test_config`
- `docs/cfg_and_paths.md` : ce document

Commandes utiles pour reproduire localement:

```bash
python -m pip install -r requirements.txt
coverage run --branch -m pytest
coverage report -m
coverage html   # ouvre un rapport HTML dans htmlcov/
```


