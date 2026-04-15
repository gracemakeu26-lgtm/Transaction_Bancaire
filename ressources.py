from flask_restx import Namespace, Resource, fields
from flask import request
from models import Utilisateur
import hashlib

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
    'date_creation': fields.DateTime(readonly=True, description='Date de création du compte'),
    'statut': fields.String(description='Statut du compte', enum=['actif', 'inactif', 'bloque'], default='actif')
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

@utilisateurs_ns.route('')
class UtilisateurList(Resource):
    @utilisateurs_ns.doc('list_utilisateurs')
    @utilisateurs_ns.marshal_list_with(utilisateur_model)
    def get(self):
        """Récupère la liste de tous les utilisateurs"""
        return Utilisateur.query.all()

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
