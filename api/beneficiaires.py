from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Beneficiaire, Compte, Utilisateur

beneficiaires_ns = Namespace('beneficiaires', description='Gestion des bénéficiaires')

beneficiaire_model = beneficiaires_ns.model('Beneficiaire', {
    'id': fields.Integer(readonly=True),
    'compte_source_id': fields.Integer(readonly=True),
    'compte_destination_id': fields.Integer(readonly=True),
    'nom': fields.String(required=True),
    'date_ajout': fields.DateTime(readonly=True)
})

beneficiaire_input_model = beneficiaires_ns.model('BeneficiaireInput', {
    'compte_source_id': fields.Integer(required=True),
    'compte_destination_id': fields.Integer(required=True),
    'nom': fields.String(required=True),
    'email': fields.String(required=True),
    'mot_de_passe': fields.String(required=True)
})

@beneficiaires_ns.route('')
class BeneficiaireList(Resource):
    @beneficiaires_ns.doc('list_beneficiaires')
    @beneficiaires_ns.marshal_list_with(beneficiaire_model)
    def get(self):
        """Liste tous les bénéficiaires"""
        return Beneficiaire.query.all(), 200
    
    @beneficiaires_ns.doc('create_beneficiaire')
    @beneficiaires_ns.expect(beneficiaire_input_model, validate=True)
    @beneficiaires_ns.marshal_with(beneficiaire_model, code=201)
    def post(self):
        """Ajoute un nouveau bénéficiaire"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            beneficiaires_ns.abort(400, "Données JSON invalides")
        
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')
        if not email or not mot_de_passe:
            beneficiaires_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            beneficiaires_ns.abort(401, "Authentification échouée")
        
        compte_source_id = data.get('compte_source_id')
        compte_destination_id = data.get('compte_destination_id')
        nom = data.get('nom')
        
        if not compte_source_id or not compte_destination_id or not nom:
            beneficiaires_ns.abort(400, "Données manquantes")
        
        compte_source = Compte.query.get_or_404(compte_source_id)
        compte_destination = Compte.query.get_or_404(compte_destination_id)
        
        if compte_source.utilisateur_id != utilisateur.id:
            beneficiaires_ns.abort(403, "Vous ne pouvez ajouter un bénéficiaire que pour votre compte")
        
        if compte_source_id == compte_destination_id:
            beneficiaires_ns.abort(400, "Le bénéficiaire ne peut pas être le compte source")
        
        existing = Beneficiaire.query.filter_by(
            compte_source_id=compte_source_id,
            compte_destination_id=compte_destination_id
        ).first()
        
        if existing:
            beneficiaires_ns.abort(409, "Ce bénéficiaire existe déjà")
        
        beneficiaire = Beneficiaire(
            compte_source_id=compte_source_id,
            compte_destination_id=compte_destination_id,
            nom=nom
        )
        
        db.session.add(beneficiaire)
        db.session.commit()
        
        return beneficiaire, 201

@beneficiaires_ns.route('/<int:id>')
class BeneficiaireItem(Resource):
    @beneficiaires_ns.doc('get_beneficiaire')
    @beneficiaires_ns.marshal_with(beneficiaire_model)
    def get(self, id):
        """Récupère un bénéficiaire spécifique"""
        beneficiaire = Beneficiaire.query.get_or_404(id)
        return beneficiaire
    
    @beneficiaires_ns.doc('delete_beneficiaire')
    @beneficiaires_ns.response(204, 'Bénéficiaire supprimé')
    def delete(self, id):
        """Supprime un bénéficiaire"""
        beneficiaire = Beneficiaire.query.get_or_404(id)
        
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        if not email or not mot_de_passe:
            beneficiaires_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            beneficiaires_ns.abort(401, "Authentification échouée")
        
        if beneficiaire.compte_source.utilisateur_id != utilisateur.id:
            beneficiaires_ns.abort(403, "Vous ne pouvez supprimer que vos bénéficiaires")
        
        db.session.delete(beneficiaire)
        db.session.commit()
        
        return '', 204

@beneficiaires_ns.route('/compte/<int:compte_id>')
class BeneficiaireCompte(Resource):
    @beneficiaires_ns.doc('get_beneficiaires_compte')
    @beneficiaires_ns.marshal_list_with(beneficiaire_model)
    def get(self, compte_id):
        """Liste les bénéficiaires d'un compte"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        if not email or not mot_de_passe:
            beneficiaires_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            beneficiaires_ns.abort(401, "Authentification échouée")
        
        compte = Compte.query.get_or_404(compte_id)
        if compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            beneficiaires_ns.abort(403, "Accès non autorisé")
        
        beneficiaires = Beneficiaire.query.filter_by(compte_source_id=compte_id).all()
        return beneficiaires, 200
