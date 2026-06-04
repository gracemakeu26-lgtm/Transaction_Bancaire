from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Virement, Compte, Utilisateur, Notification, AuditLog
from datetime import datetime
import random
import string

virements_ns = Namespace('virements', description='Gestion des virements bancaires')

virement_model = virements_ns.model('Virement', {
    'id': fields.Integer(readonly=True),
    'compte_source_id': fields.Integer(required=True),
    'compte_destination_id': fields.Integer(required=True),
    'montant': fields.Float(required=True, min=0.01),
    'date_virement': fields.DateTime(readonly=True),
    'statut': fields.String(readonly=True, enum=['en_attente', 'complétée', 'rejetée']),
    'motif': fields.String(),
    'reference': fields.String(readonly=True)
})

virement_input_model = virements_ns.model('VirementInput', {
    'compte_source_id': fields.Integer(required=True),
    'compte_destination_id': fields.Integer(required=True),
    'montant': fields.Float(required=True, min=0.01),
    'motif': fields.String(),
    'email': fields.String(required=True),
    'mot_de_passe': fields.String(required=True)
})

def generer_reference():
    """Génère une référence unique de virement"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def log_audit(utilisateur_id, type_action, description, statut='succès', adresse_ip=None):
    """Enregistre une action dans l'audit log"""
    log = AuditLog(
        utilisateur_id=utilisateur_id,
        type_action=type_action,
        description=description,
        statut_action=statut,
        adresse_ip=adresse_ip or request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

def creer_notification(utilisateur_id, type_notif, message, montant=None):
    """Crée une notification pour l'utilisateur"""
    notif = Notification(
        utilisateur_id=utilisateur_id,
        type_notification=type_notif,
        message=message,
        montant=montant
    )
    db.session.add(notif)
    db.session.commit()

@virements_ns.route('')
class VirementList(Resource):
    @virements_ns.doc('list_virements')
    @virements_ns.marshal_list_with(virement_model)
    def get(self):
        """Liste tous les virements"""
        return Virement.query.all(), 200

    @virements_ns.doc('create_virement')
    @virements_ns.expect(virement_input_model, validate=True)
    @virements_ns.marshal_with(virement_model, code=201)
    def post(self):
        """Crée un nouveau virement bancaire"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            virements_ns.abort(400, "Données JSON invalides")
        
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')
        if not email or not mot_de_passe:
            virements_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            log_audit(None, 'virement_non_autorisé', f'Tentative de virement avec identifiants invalides', 'échec')
            virements_ns.abort(401, "Authentification échouée")
        
        compte_source_id = data.get('compte_source_id')
        compte_destination_id = data.get('compte_destination_id')
        montant = data.get('montant')
        
        if not compte_source_id or not compte_destination_id or not montant:
            virements_ns.abort(400, "Données manquantes")
        
        if montant <= 0:
            virements_ns.abort(400, "Montant doit être positif")
        
        compte_source = Compte.query.get_or_404(compte_source_id)
        compte_destination = Compte.query.get_or_404(compte_destination_id)
        
        if compte_source.utilisateur_id != utilisateur.id:
            log_audit(utilisateur.id, 'virement_non_autorisé', f'Tentative de virement sur un compte non possédé', 'échec')
            virements_ns.abort(403, "Vous ne pouvez virer que depuis votre compte")
        
        if compte_source.statut != 'actif':
            virements_ns.abort(400, "Le compte source n'est pas actif")
        
        if compte_destination.statut != 'actif':
            virements_ns.abort(400, "Le compte destination n'est pas actif")
        
        if compte_source.solde < montant:
            log_audit(utilisateur.id, 'virement_rejeté', f'Solde insuffisant pour le virement de {montant}€', 'échec')
            virements_ns.abort(400, "Solde insuffisant")
        
        reference = generer_reference()
        
        compte_source.solde -= montant
        compte_destination.solde += montant
        
        virement = Virement(
            compte_source_id=compte_source_id,
            compte_destination_id=compte_destination_id,
            montant=montant,
            motif=data.get('motif'),
            reference=reference,
            statut='complétée'
        )
        
        db.session.add(virement)
        
        utilisateur_dest = compte_destination.utilisateur
        if utilisateur_dest:
            creer_notification(utilisateur_dest.id, 'virement_reçu', 
                             f"Virement de {montant}€ reçu (Ref: {reference})", montant)
        
        creer_notification(utilisateur.id, 'virement_envoyé',
                         f"Virement de {montant}€ envoyé (Ref: {reference})", montant)
        
        log_audit(utilisateur.id, 'virement_créé', f'Virement de {montant}€ vers le compte {compte_destination.numero_compte}')
        
        db.session.commit()
        
        return virement, 201

@virements_ns.route('/<int:id>')
@virements_ns.response(404, 'Virement non trouvé')
class VirementItem(Resource):
    @virements_ns.doc('get_virement')
    @virements_ns.marshal_with(virement_model)
    def get(self, id):
        """Récupère les détails d'un virement"""
        virement = Virement.query.get_or_404(id)
        return virement

@virements_ns.route('/compte/<int:compte_id>')
class VirementCompte(Resource):
    @virements_ns.doc('get_virements_compte')
    @virements_ns.marshal_list_with(virement_model)
    def get(self, compte_id):
        """Liste tous les virements d'un compte (envoyés et reçus)"""
        virements_envoyes = Virement.query.filter_by(compte_source_id=compte_id).all()
        virements_recus = Virement.query.filter_by(compte_destination_id=compte_id).all()
        return virements_envoyes + virements_recus, 200

@virements_ns.route('/<string:reference>')
class VirementReference(Resource):
    @virements_ns.doc('get_virement_reference')
    @virements_ns.marshal_with(virement_model)
    def get(self, reference):
        """Récupère un virement par sa référence"""
        virement = Virement.query.filter_by(reference=reference).first_or_404()
        return virement
