from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Utilisateur
from datetime import datetime
import re
import random

# Définition du namespace
utilisateurs_ns = Namespace('utilisateurs', description='Gestion des utilisateurs bancaires')

# Modèle Swagger pour la validation et la documentation des entrées/sorties
utilisateur_model = utilisateurs_ns.model('Utilisateur', {
    'id': fields.Integer(readonly=True, description='Identifiant unique'),
    'nom': fields.String(required=True, description='Nom de famille'),
    'prenom': fields.String(required=True, description='Prénom'),
    'email': fields.String(required=True, description='Adresse email valide'),
    'mot_de_passe': fields.String(required=True, description='Mot de passe'),
    'telephone': fields.String(required=True, description='Numéro de téléphone'),
    'date_naissance': fields.Date(required=True, description='Date de naissance (YYYY-MM-DD)'),
    'adresse': fields.String(required=True, description='Adresse postale complète'),
    'type_compte': fields.String(required=True, description='Type de compte', enum=['courant', 'epargne', 'joint']),
    'solde_initial': fields.Float(required=True, description='Solde initial du compte'),
    'numero_compte': fields.String(readonly=True, description='Numéro de compte généré automatiquement'),
    'date_creation': fields.DateTime(readonly=True, description='Date de création du compte'),
    'statut': fields.String(description='Statut du compte', enum=['actif', 'inactif', 'bloque'], default='actif')
})

utilisateur_input_model = utilisateurs_ns.model('UtilisateurInput', {
    'nom': fields.String(required=True),
    'prenom': fields.String(required=True),
    'email': fields.String(required=True),
    'mot_de_passe': fields.String(required=True),
    'telephone': fields.String(required=True),
    'date_naissance': fields.Date(required=True),
    'adresse': fields.String(required=True),
    'type_compte': fields.String(required=True, enum=['courant', 'epargne', 'joint']),
    'solde_initial': fields.Float(required=True),
    'statut': fields.String(enum=['actif', 'inactif', 'bloque'], default='actif')
})

# Fonctions utilitaires
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def generer_numero_compte():
    # Génère un numéro de compte unique en base
    while True:
        numero = f"FR76{random.randint(10000000000, 99999999999)}"
        if not Utilisateur.query.filter_by(numero_compte=numero).first():
            return numero

@utilisateurs_ns.route('')
class UtilisateurList(Resource):
    @utilisateurs_ns.doc('list_utilisateurs')
    @utilisateurs_ns.marshal_list_with(utilisateur_model)
    @utilisateurs_ns.param('statut', 'Filtrer par statut (actif, inactif, bloque)')
    def get(self):
        """Récupère la liste de tous les utilisateurs"""
        statut_filtre = request.args.get('statut')
        query = Utilisateur.query
        if statut_filtre:
            query = query.filter_by(statut=statut_filtre)
        return query.all()

    @utilisateurs_ns.doc('create_utilisateur')
    @utilisateurs_ns.expect(utilisateur_input_model, validate=True)
    @utilisateurs_ns.marshal_with(utilisateur_model, code=201)
    def post(self):
        """Crée un nouvel utilisateur (client bancaire)"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            utilisateurs_ns.abort(400, "Le corps de la requête doit être un JSON valide")
        
        # Validation email
        if not is_valid_email(data.get('email', '')):
            utilisateurs_ns.abort(400, "Format d'email invalide")
        
        # Vérification unicité email
        if Utilisateur.query.filter_by(email=data.get('email')).first():
            utilisateurs_ns.abort(409, "Cet email est déjà utilisé")
        
        try:
            date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
        except ValueError:
            utilisateurs_ns.abort(400, "Format de date invalide. Utiliser YYYY-MM-DD")
        
        nouvel_utilisateur = Utilisateur(
            nom=data['nom'],
            prenom=data['prenom'],
            email=data['email'],
            mot_de_passe=data['mot_de_passe'],
            telephone=data['telephone'],
            date_naissance=date_naissance,
            adresse=data['adresse'],
            type_compte=data['type_compte'],
            numero_compte=generer_numero_compte(),
            solde_initial=data['solde_initial'],
            statut=data.get('statut', 'actif')
        )
        
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        
        return nouvel_utilisateur, 201

@utilisateurs_ns.route('/<int:id>')
@utilisateurs_ns.param('id', 'Identifiant de l\'utilisateur')
@utilisateurs_ns.response(404, 'Utilisateur non trouvé')
class UtilisateurItem(Resource):
    @utilisateurs_ns.doc('get_utilisateur')
    @utilisateurs_ns.marshal_with(utilisateur_model)
    def get(self, id):
        """Récupère un utilisateur par son ID"""
        utilisateur = Utilisateur.query.get_or_404(id)
        return utilisateur

    @utilisateurs_ns.doc('update_utilisateur')
    @utilisateurs_ns.expect(utilisateur_input_model)
    @utilisateurs_ns.marshal_with(utilisateur_model)
    def put(self, id):
        """Met à jour les informations d'un utilisateur"""
        utilisateur = Utilisateur.query.get_or_404(id)
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            utilisateurs_ns.abort(400, "Le corps de la requête doit être un JSON valide")
        
        # Mise à jour des champs modifiables
        if 'nom' in data: utilisateur.nom = data['nom']
        if 'prenom' in data: utilisateur.prenom = data['prenom']
        if 'mot_de_passe' in data: utilisateur.mot_de_passe = data['mot_de_passe']
        if 'telephone' in data: utilisateur.telephone = data['telephone']
        if 'adresse' in data: utilisateur.adresse = data['adresse']
        if 'statut' in data: utilisateur.statut = data['statut']
        # Note : email, date_naissance, type_compte et solde ne sont généralement pas modifiables sans procédure spécifique
        
        db.session.commit()
        return utilisateur

    @utilisateurs_ns.doc('delete_utilisateur')
    @utilisateurs_ns.response(204, 'Utilisateur supprimé')
    def delete(self, id):
        """Supprime un utilisateur (soft delete ou hard delete selon les règles métier)"""
        utilisateur = Utilisateur.query.get_or_404(id)
        # Dans un vrai système bancaire, on ferait un soft delete (statut = 'ferme')
        db.session.delete(utilisateur)
        db.session.commit()
        return '', 204