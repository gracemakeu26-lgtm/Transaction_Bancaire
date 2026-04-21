from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Utilisateur
from datetime import datetime
import hashlib

def generer_numero_compte():
    import random
    while True:
        numero = f"FR76{random.randint(10000000000, 99999999999)}"
        if not Utilisateur.query.filter_by(numero_compte=numero).first():
            return numero

utilisateurs_ns = Namespace('utilisateurs_rest', description='Gestion des utilisateurs bancaires (REST)')

utilisateur_model = utilisateurs_ns.model('Utilisateur', {
    'id': fields.Integer(readonly=True, description='Identifiant unique'),
    'nom': fields.String(required=True, description='Nom de famille'),
    'prenom': fields.String(required=True, description='Prénom'),
    'email': fields.String(required=True, description='Adresse email valide'),
    'telephone': fields.String(required=True, description='Numéro de téléphone'),
    'date_naissance': fields.Date(required=True, description='Date de naissance (YYYY-MM-DD)'),
    'adresse': fields.String(required=True, description='Adresse postale complète'),
    'type_compte': fields.String(required=True, description='Type de compte', enum=['courant', 'epargne', 'joint']),
    'solde_initial': fields.Float(required=True, description='Solde initial du compte'),
    'numero_compte': fields.String(readonly=True, description='Numéro de compte généré automatiquement'),
    'is_admin': fields.Boolean(description='Utilisateur administrateur'),
    'date_creation': fields.DateTime(readonly=True, description='Date de création du compte'),
    'statut': fields.String(description='Statut du compte', enum=['actif', 'inactif', 'bloque'], default='actif')
})

utilisateur_input_model = utilisateurs_ns.model('UtilisateurInput', {
    'nom': fields.String(required=True, description='Nom de famille'),
    'prenom': fields.String(required=True, description='Prénom'),
    'email': fields.String(required=True, description='Adresse email valide'),
    'mot_de_passe': fields.String(required=True, description='Mot de passe'),
    'telephone': fields.String(required=True, description='Numéro de téléphone'),
    'date_naissance': fields.Date(required=True, description='Date de naissance (YYYY-MM-DD)'),
    'adresse': fields.String(required=True, description='Adresse postale complète'),
    'type_compte': fields.String(required=True, description='Type de compte', enum=['courant', 'epargne', 'joint']),
    'solde_initial': fields.Float(required=True, description='Solde initial du compte'),
    'statut': fields.String(enum=['actif', 'inactif', 'bloque'], default='actif')
})

admin_action_model = utilisateurs_ns.model('AdminAction', {
    'admin_email': fields.String(required=True, description='Email de l’administrateur'),
    'admin_mot_de_passe': fields.String(required=True, description='Mot de passe de l’administrateur')
})

transaction_model = utilisateurs_ns.model('CompteTransaction', {
    'email': fields.String(required=True, description='Email du titulaire du compte ou de l’administrateur'),
    'mot_de_passe': fields.String(required=True, description='Mot de passe du titulaire ou de l’administrateur'),
    'montant': fields.Float(required=True, description='Montant du dépôt ou retrait')
})

face_register_model = utilisateurs_ns.model('FaceRegister', {
    'email': fields.String(required=True, description='Adresse email de l’utilisateur'),
    'image_base64': fields.String(required=True, description='Image du visage encodée en Base64')
})

face_login_model = utilisateurs_ns.model('FaceLogin', {
    'email': fields.String(required=False, description='Adresse email de l’utilisateur (optionnel)'),
    'image_base64': fields.String(required=True, description='Image du visage encodée en Base64')
})

def calculate_face_template(image_base64):
    normalized = image_base64.strip()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def auth_user(email, mot_de_passe):
    if not email or not mot_de_passe:
        utilisateurs_ns.abort(400, "Email et mot de passe requis")
    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
        utilisateurs_ns.abort(401, "Informations invalides")
    return utilisateur

def require_admin(email, mot_de_passe):
    utilisateur = auth_user(email, mot_de_passe)
    if not utilisateur.is_admin:
        utilisateurs_ns.abort(403, "Accès administrateur requis")
    return utilisateur

@utilisateurs_ns.route('')
class UtilisateurList(Resource):
    @utilisateurs_ns.doc('list_utilisateurs')
    @utilisateurs_ns.marshal_list_with(utilisateur_model)
    def get(self):
        """Récupère la liste de tous les utilisateurs"""
        return Utilisateur.query.all()

    @utilisateurs_ns.doc('create_utilisateur')
    @utilisateurs_ns.expect(utilisateur_input_model, validate=True)
    @utilisateurs_ns.marshal_with(utilisateur_model, code=201)
    def post(self):
        """Crée un nouvel utilisateur (client bancaire)"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            utilisateurs_ns.abort(400, "Le corps de la requête doit être un JSON valide")
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
            is_admin=False,
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

    @utilisateurs_ns.doc('delete_utilisateur')
    @utilisateurs_ns.expect(admin_action_model, validate=True)
    @utilisateurs_ns.response(204, 'Utilisateur supprimé')
    def delete(self, id):
        """Supprime un utilisateur par un administrateur"""
        utilisateur = Utilisateur.query.get_or_404(id)
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            utilisateurs_ns.abort(400, "Le corps de la requête doit être un JSON valide")
        admin_email = data.get('admin_email')
        admin_mot_de_passe = data.get('admin_mot_de_passe')
        requester = require_admin(admin_email, admin_mot_de_passe)
        if utilisateur.is_admin:
            utilisateurs_ns.abort(403, "Impossible de supprimer un autre administrateur")
        db.session.delete(utilisateur)
        db.session.commit()
        return '', 204

@utilisateurs_ns.route('/<int:id>/promote')
class UtilisateurPromote(Resource):
    @utilisateurs_ns.doc('promote_utilisateur')
    @utilisateurs_ns.expect(admin_action_model, validate=True)
    def post(self, id):
        """Promote un utilisateur en administrateur"""
        utilisateur = Utilisateur.query.get_or_404(id)
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            utilisateurs_ns.abort(400, "Le corps de la requête doit être un JSON valide")
        admin_email = data.get('admin_email')
        admin_mot_de_passe = data.get('admin_mot_de_passe')
        require_admin(admin_email, admin_mot_de_passe)
        utilisateur.is_admin = True
        db.session.commit()
        return {'message': 'Utilisateur promu administrateur'}, 200

@utilisateurs_ns.route('/login')
class UtilisateurLogin(Resource):
    @utilisateurs_ns.doc('login_utilisateur')
    @utilisateurs_ns.expect(utilisateurs_ns.model('Login', {
        'email': fields.String(required=True),
        'mot_de_passe': fields.String(required=True)
    }))
    def post(self):
        """Authentification d'un utilisateur"""
        data = request.get_json()
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')
        
        if not email or not mot_de_passe:
            utilisateurs_ns.abort(400, "Email et mot de passe requis")

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if utilisateur and utilisateur.mot_de_passe == mot_de_passe:  # Note: en prod, utiliser hash
            return utilisateur.to_dict(), 200
        utilisateurs_ns.abort(401, "Informations invalides")

@utilisateurs_ns.route('/register_face')
class UtilisateurFaceRegister(Resource):
    @utilisateurs_ns.doc('register_face_utilisateur')
    @utilisateurs_ns.expect(face_register_model, validate=True)
    def post(self):
        """Enregistre une image faciale pour un utilisateur"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            utilisateurs_ns.abort(400, "Le corps de la requête doit être un JSON valide")

        email = data.get('email')
        image_base64 = data.get('image_base64')
        if not email or not image_base64:
            utilisateurs_ns.abort(400, "Email et image faciale requis")

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur:
            utilisateurs_ns.abort(404, "Utilisateur non trouvé")

        empreinte = calculate_face_template(image_base64)
        utilisateur.empreinte_faciale = empreinte
        db.session.commit()
        return {'message': "Visage enregistré avec succès"}, 200

@utilisateurs_ns.route('/login/face')
class UtilisateurFaceLogin(Resource):
    @utilisateurs_ns.doc('login_face_utilisateur')
    @utilisateurs_ns.expect(face_login_model, validate=True)
    def post(self):
        """Authentification d'un utilisateur par reconnaissance faciale"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            utilisateurs_ns.abort(400, "Le corps de la requête doit être un JSON valide")

        image_base64 = data.get('image_base64')
        email = data.get('email')
        if not image_base64:
            utilisateurs_ns.abort(400, "Image faciale requise")

        empreinte = calculate_face_template(image_base64)

        if email:
            utilisateur = Utilisateur.query.filter_by(email=email).first()
            if utilisateur and utilisateur.empreinte_faciale == empreinte:
                return utilisateur.to_dict(), 200
            utilisateurs_ns.abort(401, "Informations invalides")

        utilisateur = Utilisateur.query.filter_by(empreinte_faciale=empreinte).first()
        if utilisateur:
            return utilisateur.to_dict(), 200
        utilisateurs_ns.abort(401, "Visage non reconnu")

# Namespace pour la gestion des comptes
comptes_ns = Namespace('comptes', description='Gestion des comptes bancaires')

compte_model = comptes_ns.model('Compte', {
    'id': fields.Integer(readonly=True, description='Identifiant unique'),
    'nom': fields.String(required=True, description='Nom de famille'),
    'prenom': fields.String(required=True, description='Prénom'),
    'email': fields.String(required=True, description='Adresse email valide'),
    'telephone': fields.String(required=True, description='Numéro de téléphone'),
    'date_naissance': fields.Date(required=True, description='Date de naissance (YYYY-MM-DD)'),
    'adresse': fields.String(required=True, description='Adresse postale complète'),
    'type_compte': fields.String(required=True, description='Type de compte', enum=['courant', 'epargne', 'joint']),
    'solde_initial': fields.Float(required=True, description='Solde initial du compte'),
    'numero_compte': fields.String(readonly=True, description='Numéro de compte généré automatiquement'),
    'is_admin': fields.Boolean(description='Utilisateur administrateur'),
    'date_creation': fields.DateTime(readonly=True, description='Date de création du compte'),
    'statut': fields.String(description='Statut du compte', enum=['actif', 'inactif', 'bloque'], default='actif')
})

compte_input_model = comptes_ns.model('CompteInput', {
    'nom': fields.String(required=True, description='Nom de famille'),
    'prenom': fields.String(required=True, description='Prénom'),
    'email': fields.String(required=True, description='Adresse email valide'),
    'mot_de_passe': fields.String(required=True, description='Mot de passe'),
    'telephone': fields.String(required=True, description='Numéro de téléphone'),
    'date_naissance': fields.Date(required=True, description='Date de naissance (YYYY-MM-DD)'),
    'adresse': fields.String(required=True, description='Adresse postale complète'),
    'type_compte': fields.String(required=True, description='Type de compte', enum=['courant', 'epargne', 'joint']),
    'solde_initial': fields.Float(required=True, description='Solde initial du compte'),
    'statut': fields.String(enum=['actif', 'inactif', 'bloque'], default='actif')
})

@comptes_ns.route('')
class CompteList(Resource):
    @comptes_ns.doc('list_comptes')
    @comptes_ns.marshal_list_with(compte_model)
    def get(self):
        """Récupère la liste de tous les comptes"""
        return Utilisateur.query.all()

    @comptes_ns.doc('create_compte')
    @comptes_ns.expect(compte_input_model, validate=True)
    @comptes_ns.marshal_with(compte_model, code=201)
    def post(self):
        """Crée un nouveau compte bancaire"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            comptes_ns.abort(400, "Le corps de la requête doit être un JSON valide")
        if Utilisateur.query.filter_by(email=data.get('email')).first():
            comptes_ns.abort(409, "Cet email est déjà utilisé")
        try:
            date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
        except ValueError:
            comptes_ns.abort(400, "Format de date invalide. Utiliser YYYY-MM-DD")
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
            is_admin=False,
            statut=data.get('statut', 'actif')
        )
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        return nouvel_utilisateur, 201

@comptes_ns.route('/<int:id>')
@comptes_ns.param('id', 'Identifiant du compte')
@comptes_ns.response(404, 'Compte non trouvé')
class CompteItem(Resource):
    @comptes_ns.doc('get_compte')
    @comptes_ns.marshal_with(compte_model)
    def get(self, id):
        """Récupère un compte par son ID"""
        utilisateur = Utilisateur.query.get_or_404(id)
        return utilisateur

    @comptes_ns.doc('delete_compte')
    @comptes_ns.expect(admin_action_model, validate=True)
    @comptes_ns.response(204, 'Compte supprimé')
    def delete(self, id):
        """Supprime un compte par un administrateur"""
        utilisateur = Utilisateur.query.get_or_404(id)
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            comptes_ns.abort(400, "Le corps de la requête doit être un JSON valide")
        admin_email = data.get('admin_email')
        admin_mot_de_passe = data.get('admin_mot_de_passe')
        requester = require_admin(admin_email, admin_mot_de_passe)
        if utilisateur.is_admin:
            comptes_ns.abort(403, "Impossible de supprimer un autre administrateur")
        db.session.delete(utilisateur)
        db.session.commit()
        return '', 204
