-- Fichier de migration pour le système bancaire complet
-- Nouvelles tables ajoutées pour les fonctionnalités v1.1.0

-- Table: virements
-- Permet les transferts d'argent entre comptes
CREATE TABLE virements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compte_source_id INTEGER NOT NULL,
    compte_destination_id INTEGER NOT NULL,
    montant FLOAT NOT NULL,
    date_virement DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR(20) DEFAULT 'en_attente',
    motif VARCHAR(255),
    reference VARCHAR(50) UNIQUE NOT NULL,
    FOREIGN KEY (compte_source_id) REFERENCES comptes(id),
    FOREIGN KEY (compte_destination_id) REFERENCES comptes(id)
);

-- Table: beneficiaires
-- Stocke les comptes de bénéficiaires fréquents
CREATE TABLE beneficiaires (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compte_source_id INTEGER NOT NULL,
    compte_destination_id INTEGER NOT NULL,
    nom VARCHAR(100) NOT NULL,
    date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (compte_source_id) REFERENCES comptes(id),
    FOREIGN KEY (compte_destination_id) REFERENCES comptes(id),
    UNIQUE(compte_source_id, compte_destination_id)
);

-- Table: notifications
-- Système de notifications pour les événements bancaires
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utilisateur_id INTEGER NOT NULL,
    type_notification VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    montant FLOAT,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
);

-- Table: cartes
-- Gestion des cartes bancaires
CREATE TABLE cartes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compte_id INTEGER NOT NULL,
    numero_carte VARCHAR(19) UNIQUE NOT NULL,
    nom_titulaire VARCHAR(100) NOT NULL,
    date_expiration VARCHAR(5) NOT NULL,
    type_carte VARCHAR(20) NOT NULL,
    statut VARCHAR(20) DEFAULT 'actif',
    date_emission DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (compte_id) REFERENCES comptes(id)
);

-- Table: limites_transactions
-- Limites quotidiennes et mensuelles de transactions
CREATE TABLE limites_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utilisateur_id INTEGER NOT NULL UNIQUE,
    limite_quotidienne FLOAT DEFAULT 10000.0,
    limite_mensuelle FLOAT DEFAULT 50000.0,
    montant_quotidien FLOAT DEFAULT 0.0,
    montant_mensuel FLOAT DEFAULT 0.0,
    date_reset_quotidien DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_reset_mensuel DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
);

-- Table: audit_logs
-- Journalisation de toutes les opérations sensibles
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utilisateur_id INTEGER,
    type_action VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    date_action DATETIME DEFAULT CURRENT_TIMESTAMP,
    adresse_ip VARCHAR(45),
    statut_action VARCHAR(20) DEFAULT 'succès',
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
);

-- Modifications aux tables existantes

-- Ajouter des colonnes à la table utilisateurs
ALTER TABLE utilisateurs ADD COLUMN derniere_connexion DATETIME;

-- Ajouter des colonnes à la table transactions
ALTER TABLE transactions ADD COLUMN description VARCHAR(255);
ALTER TABLE transactions ADD COLUMN statut VARCHAR(20) DEFAULT 'complétée';

-- Index pour performance
CREATE INDEX idx_virements_source ON virements(compte_source_id);
CREATE INDEX idx_virements_destination ON virements(compte_destination_id);
CREATE INDEX idx_virements_date ON virements(date_virement);
CREATE INDEX idx_notifications_utilisateur ON notifications(utilisateur_id);
CREATE INDEX idx_notifications_date ON notifications(date_creation);
CREATE INDEX idx_cartes_compte ON cartes(compte_id);
CREATE INDEX idx_audit_utilisateur ON audit_logs(utilisateur_id);
CREATE INDEX idx_audit_date ON audit_logs(date_action);
CREATE INDEX idx_limites_utilisateur ON limites_transactions(utilisateur_id);

-- Vues utiles
-- Vue: Statistiques par compte
CREATE VIEW v_statistiques_compte AS
SELECT 
    c.id,
    c.numero_compte,
    c.solde,
    COUNT(t.id) as nombre_transactions,
    SUM(CASE WHEN t.type_transaction = 'depot' THEN t.montant ELSE 0 END) as total_depots,
    SUM(CASE WHEN t.type_transaction = 'retrait' THEN t.montant ELSE 0 END) as total_retraits
FROM comptes c
LEFT JOIN transactions t ON c.id = t.compte_id
GROUP BY c.id;

-- Vue: Transactions récentes
CREATE VIEW v_transactions_recentes AS
SELECT 
    t.id,
    c.numero_compte,
    t.type_transaction,
    t.montant,
    t.date_transaction,
    t.description,
    u.nom,
    u.prenom
FROM transactions t
JOIN comptes c ON t.compte_id = c.id
JOIN utilisateurs u ON c.utilisateur_id = u.id
ORDER BY t.date_transaction DESC
LIMIT 100;

-- Vue: Bénéficiaires avec détails
CREATE VIEW v_beneficiaires_details AS
SELECT 
    b.id,
    b.nom,
    cs.numero_compte as compte_source,
    cd.numero_compte as compte_destination,
    b.date_ajout,
    COUNT(v.id) as nombre_virements
FROM beneficiaires b
JOIN comptes cs ON b.compte_source_id = cs.id
JOIN comptes cd ON b.compte_destination_id = cd.id
LEFT JOIN virements v ON b.compte_source_id = v.compte_source_id 
    AND b.compte_destination_id = v.compte_destination_id
GROUP BY b.id;

-- Procédures stockées (si la base le supporte)
-- Exemple: Réinitialiser les limites quotidiennes

-- Données de seed (optionnel)
-- Insérer un utilisateur admin de test
-- INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, telephone, date_naissance, adresse, type_compte, numero_compte, solde_initial, is_admin, statut)
-- VALUES ('Admin', 'Test', 'admin@test.com', 'hashed_password', '+33000000000', '1980-01-01', 'Admin Address', 'courant', 'FR76ADMIN000', 0, 1, 'actif');
