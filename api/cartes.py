from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Carte, Compte, Utilisateur
import random
import string

cartes_ns = Namespace('cartes', description='Gestion des cartes bancaires')

carte_model = cartes_ns.model('Carte', {
    'id': fields.Integer(readonly=True),
    'compte_id': fields.Integer(readonly=True),
    'numero_carte': fields.String(readonly=True),
    'nom_titulaire': fields.String(),
    'date_expiration': fields.String(),
    'type_carte': fields.String(enum=['debit', 'credit', 'virtuelle']),
    'statut': fields.String(enum=['actif', 'bloque', 'expiree']),
    'date_emission': fields.DateTime(readonly=True)
})

carte_input_model = cartes_ns.model('CarteInput', {
    'compte_id': fields.Integer(required=True),
    'nom_titulaire': fields.String(required=True),
    'type_carte': fields.String(required=True, enum=['debit', 'credit', 'virtuelle']),
    'email': fields.String(required=True),
    'mot_de_passe': fields.String(required=True)
})

def generer_numero_carte():
    """Génère un numéro de carte unique (format simplifié)"""
    while True:
        numero = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        if not Carte.query.filter_by(numero_carte=numero).first():
            return numero

def generer_date_expiration():
    """Génère une date d'expiration (MM/YY)"""
    month = random.randint(1, 12)
    year = random.randint(25, 30)
    return f"{month:02d}/{year:02d}"

@cartes_ns.route('')
class CarteList(Resource):
    @cartes_ns.doc('list_cartes')
    @cartes_ns.marshal_list_with(carte_model)
    def get(self):
        """Liste toutes les cartes"""
        return Carte.query.all(), 200
    
    @cartes_ns.doc('create_carte')
    @cartes_ns.expect(carte_input_model, validate=True)
    @cartes_ns.marshal_with(carte_model, code=201)
    def post(self):
        """Crée une nouvelle carte bancaire"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            cartes_ns.abort(400, "Données JSON invalides")
        
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')
        if not email or not mot_de_passe:
            cartes_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            cartes_ns.abort(401, "Authentification échouée")
        
        compte_id = data.get('compte_id')
        nom_titulaire = data.get('nom_titulaire')
        type_carte = data.get('type_carte')
        
        if not compte_id or not nom_titulaire or not type_carte:
            cartes_ns.abort(400, "Données manquantes")
        
        compte = Compte.query.get_or_404(compte_id)
        
        if compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            cartes_ns.abort(403, "Vous ne pouvez créer une carte que pour votre compte")
        
        if compte.statut != 'actif':
            cartes_ns.abort(400, "Le compte n'est pas actif")
        
        carte = Carte(
            compte_id=compte_id,
            numero_carte=generer_numero_carte(),
            nom_titulaire=nom_titulaire,
            date_expiration=generer_date_expiration(),
            type_carte=type_carte,
            statut='actif'
        )
        
        db.session.add(carte)
        db.session.commit()
        
        return carte, 201

@cartes_ns.route('/<int:id>')
class CarteItem(Resource):
    @cartes_ns.doc('get_carte')
    @cartes_ns.marshal_with(carte_model)
    def get(self, id):
        """Récupère une carte spécifique"""
        carte = Carte.query.get_or_404(id)
        return carte
    
    @cartes_ns.doc('update_carte_status')
    @cartes_ns.response(200, 'Statut de la carte mis à jour')
    def put(self, id):
        """Met à jour le statut d'une carte (bloquer/débloquer)"""
        carte = Carte.query.get_or_404(id)
        
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        if not email or not mot_de_passe:
            cartes_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            cartes_ns.abort(401, "Authentification échouée")
        
        if carte.compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            cartes_ns.abort(403, "Accès non autorisé")
        
        data = request.get_json(silent=True)
        if data and 'statut' in data:
            nouveau_statut = data['statut']
            if nouveau_statut in ['actif', 'bloque', 'expiree']:
                carte.statut = nouveau_statut
                db.session.commit()
                return {'message': f'Statut de la carte mis à jour: {nouveau_statut}'}, 200
            else:
                cartes_ns.abort(400, "Statut invalide")
        else:
            cartes_ns.abort(400, "Nouveau statut requis")
    
    @cartes_ns.doc('delete_carte')
    @cartes_ns.response(204, 'Carte supprimée')
    def delete(self, id):
        """Supprime une carte"""
        carte = Carte.query.get_or_404(id)
        
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        if not email or not mot_de_passe:
            cartes_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            cartes_ns.abort(401, "Authentification échouée")
        
        if carte.compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            cartes_ns.abort(403, "Accès non autorisé")
        
        db.session.delete(carte)
        db.session.commit()
        
        return '', 204

@cartes_ns.route('/compte/<int:compte_id>')
class CarteCompte(Resource):
    @cartes_ns.doc('get_cartes_compte')
    @cartes_ns.marshal_list_with(carte_model)
    def get(self, compte_id):
        """Liste les cartes d'un compte"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        if not email or not mot_de_passe:
            cartes_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            cartes_ns.abort(401, "Authentification échouée")
        
        compte = Compte.query.get_or_404(compte_id)
        if compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            cartes_ns.abort(403, "Accès non autorisé")
        
        cartes = Carte.query.filter_by(compte_id=compte_id).all()
        return cartes, 200

@cartes_ns.route('/<string:numero_carte>')
class CarteNumero(Resource):
    @cartes_ns.doc('get_carte_numero')
    @cartes_ns.marshal_with(carte_model)
    def get(self, numero_carte):
        """Récupère une carte par numéro"""
        carte = Carte.query.filter_by(numero_carte=numero_carte).first_or_404()
        return carte
