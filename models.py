from extensions import db
from datetime import datetime
from enum import Enum

class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    date_naissance = db.Column(db.Date, nullable=False)
    adresse = db.Column(db.Text, nullable=False)
    type_compte = db.Column(db.String(20), nullable=False)
    numero_compte = db.Column(db.String(24), unique=True, nullable=False)
    solde_initial = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    empreinte_faciale = db.Column(db.Text, nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='actif')
    derniere_connexion = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'email': self.email,
            'telephone': self.telephone,
            'date_naissance': self.date_naissance.isoformat(),
            'adresse': self.adresse,
            'type_compte': self.type_compte,
            'numero_compte': self.numero_compte,
            'solde_initial': self.solde_initial,
            'is_admin': self.is_admin,
            'date_creation': self.date_creation.isoformat(),
            'statut': self.statut
        }

    def deposit(self, montant):
        if montant <= 0:
            raise ValueError("Le montant doit être positif")
        self.solde_initial += montant

    def withdraw(self, montant):
        if montant <= 0:
            raise ValueError("Le montant doit être positif")
        if self.solde_initial < montant:
            raise ValueError("Solde insuffisant")
        self.solde_initial -= montant

class Compte(db.Model):
    __tablename__ = 'comptes'
    id = db.Column(db.Integer, primary_key=True)
    numero_compte = db.Column(db.String(24), unique=True, nullable=True)
    type_compte = db.Column(db.String(20), nullable=True)
    solde = db.Column(db.Float, default=0.0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='actif')
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=True)
    utilisateur = db.relationship('Utilisateur', backref=db.backref('comptes', lazy=True))

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    type_transaction = db.Column(db.String(20), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    date_transaction = db.Column(db.DateTime, default=datetime.utcnow)
    compte_id = db.Column(db.Integer, db.ForeignKey('comptes.id'), nullable=False)
    compte = db.relationship('Compte', backref=db.backref('transactions', lazy=True))
    description = db.Column(db.String(255), nullable=True)
    statut = db.Column(db.String(20), default='complétée')

class Virement(db.Model):
    __tablename__ = 'virements'
    id = db.Column(db.Integer, primary_key=True)
    compte_source_id = db.Column(db.Integer, db.ForeignKey('comptes.id'), nullable=False)
    compte_destination_id = db.Column(db.Integer, db.ForeignKey('comptes.id'), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    date_virement = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='en_attente')
    motif = db.Column(db.String(255), nullable=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    
    compte_source = db.relationship('Compte', foreign_keys=[compte_source_id])
    compte_destination = db.relationship('Compte', foreign_keys=[compte_destination_id])

class Beneficiaire(db.Model):
    __tablename__ = 'beneficiaires'
    id = db.Column(db.Integer, primary_key=True)
    compte_source_id = db.Column(db.Integer, db.ForeignKey('comptes.id'), nullable=False)
    compte_destination_id = db.Column(db.Integer, db.ForeignKey('comptes.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)
    
    compte_source = db.relationship('Compte', foreign_keys=[compte_source_id])
    compte_destination = db.relationship('Compte', foreign_keys=[compte_destination_id])

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    type_notification = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    montant = db.Column(db.Float, nullable=True)
    
    utilisateur = db.relationship('Utilisateur', backref=db.backref('notifications', lazy=True))

class LimiteTransaction(db.Model):
    __tablename__ = 'limites_transactions'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    limite_quotidienne = db.Column(db.Float, default=10000.0)
    limite_mensuelle = db.Column(db.Float, default=50000.0)
    montant_quotidien = db.Column(db.Float, default=0.0)
    montant_mensuel = db.Column(db.Float, default=0.0)
    date_reset_quotidien = db.Column(db.DateTime, default=datetime.utcnow)
    date_reset_mensuel = db.Column(db.DateTime, default=datetime.utcnow)
    
    utilisateur = db.relationship('Utilisateur', backref=db.backref('limites', lazy=True))

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=True)
    type_action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_action = db.Column(db.DateTime, default=datetime.utcnow)
    adresse_ip = db.Column(db.String(45), nullable=True)
    statut_action = db.Column(db.String(20), default='succès')
    
    utilisateur = db.relationship('Utilisateur', backref=db.backref('audit_logs', lazy=True))

class Carte(db.Model):
    __tablename__ = 'cartes'
    id = db.Column(db.Integer, primary_key=True)
    compte_id = db.Column(db.Integer, db.ForeignKey('comptes.id'), nullable=False)
    numero_carte = db.Column(db.String(19), unique=True, nullable=False)
    nom_titulaire = db.Column(db.String(100), nullable=False)
    date_expiration = db.Column(db.String(5), nullable=False)
    type_carte = db.Column(db.String(20), nullable=False)
    statut = db.Column(db.String(20), default='actif')
    date_emission = db.Column(db.DateTime, default=datetime.utcnow)
    
    compte = db.relationship('Compte', backref=db.backref('cartes', lazy=True))