from extensions import db
from datetime import datetime

class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(128), nullable=False)
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

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError('Le montant du dépôt doit être positif')
        self.solde_initial += amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError('Le montant du retrait doit être positif')
        if amount > self.solde_initial:
            raise ValueError('Solde insuffisant')
        self.solde_initial -= amount