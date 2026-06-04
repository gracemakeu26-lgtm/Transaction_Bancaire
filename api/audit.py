from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, AuditLog, Utilisateur, LimiteTransaction
from datetime import datetime, timedelta

audit_ns = Namespace('audit', description='Journalisation des opérations sensibles')
limites_ns = Namespace('limites', description='Gestion des limites de transactions')

audit_log_model = audit_ns.model('AuditLog', {
    'id': fields.Integer(readonly=True),
    'utilisateur_id': fields.Integer(),
    'type_action': fields.String(),
    'description': fields.String(),
    'date_action': fields.DateTime(readonly=True),
    'adresse_ip': fields.String(),
    'statut_action': fields.String(enum=['succès', 'échec'])
})

limite_model = limites_ns.model('LimiteTransaction', {
    'id': fields.Integer(readonly=True),
    'utilisateur_id': fields.Integer(readonly=True),
    'limite_quotidienne': fields.Float(),
    'limite_mensuelle': fields.Float(),
    'montant_quotidien': fields.Float(readonly=True),
    'montant_mensuel': fields.Float(readonly=True),
    'date_reset_quotidien': fields.DateTime(readonly=True),
    'date_reset_mensuel': fields.DateTime(readonly=True)
})

limite_input_model = limites_ns.model('LimiteInput', {
    'limite_quotidienne': fields.Float(),
    'limite_mensuelle': fields.Float(),
    'email': fields.String(required=True),
    'mot_de_passe': fields.String(required=True)
})

@audit_ns.route('')
class AuditLogList(Resource):
    @audit_ns.doc('list_audit_logs')
    @audit_ns.marshal_list_with(audit_log_model)
    def get(self):
        """Liste tous les logs d'audit (admin seulement)"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            audit_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe or not utilisateur.is_admin:
            audit_ns.abort(403, "Accès administrateur requis")
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        logs = AuditLog.query.order_by(AuditLog.date_action.desc()).paginate(
            page=page, per_page=per_page
        )
        
        return logs.items, 200

@audit_ns.route('/utilisateur/<int:user_id>')
class AuditLogUtilisateur(Resource):
    @audit_ns.doc('get_user_audit_logs')
    @audit_ns.marshal_list_with(audit_log_model)
    def get(self, user_id):
        """Liste les logs d'audit d'un utilisateur (admin seulement)"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            audit_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe or not utilisateur.is_admin:
            audit_ns.abort(403, "Accès administrateur requis")
        
        logs = AuditLog.query.filter_by(utilisateur_id=user_id).order_by(
            AuditLog.date_action.desc()
        ).all()
        
        return logs, 200

@limites_ns.route('')
class LimiteTransactionList(Resource):
    @limites_ns.doc('list_limites')
    @limites_ns.marshal_list_with(limite_model)
    def get(self):
        """Liste toutes les limites de transactions (admin seulement)"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            limites_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe or not utilisateur.is_admin:
            limites_ns.abort(403, "Accès administrateur requis")
        
        limites = LimiteTransaction.query.all()
        return limites, 200

@limites_ns.route('/utilisateur/<int:user_id>')
class LimiteTransactionUtilisateur(Resource):
    @limites_ns.doc('get_user_limite')
    @limites_ns.marshal_with(limite_model)
    def get(self, user_id):
        """Récupère les limites de transactions d'un utilisateur"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            limites_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            limites_ns.abort(401, "Authentification échouée")
        
        if utilisateur.id != user_id and not utilisateur.is_admin:
            limites_ns.abort(403, "Accès non autorisé")
        
        limite = LimiteTransaction.query.filter_by(utilisateur_id=user_id).first()
        if not limite:
            limite = LimiteTransaction(utilisateur_id=user_id)
            db.session.add(limite)
            db.session.commit()
        
        return limite, 200
    
    @limites_ns.doc('update_user_limite')
    @limites_ns.expect(limite_input_model, validate=True)
    @limites_ns.marshal_with(limite_model)
    def put(self, user_id):
        """Met à jour les limites de transactions d'un utilisateur"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            limites_ns.abort(400, "Données JSON invalides")
        
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')
        
        if not email or not mot_de_passe:
            limites_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            limites_ns.abort(401, "Authentification échouée")
        
        if utilisateur.id != user_id and not utilisateur.is_admin:
            limites_ns.abort(403, "Accès non autorisé")
        
        limite = LimiteTransaction.query.filter_by(utilisateur_id=user_id).first()
        if not limite:
            limite = LimiteTransaction(utilisateur_id=user_id)
            db.session.add(limite)
        
        if 'limite_quotidienne' in data:
            limite.limite_quotidienne = data['limite_quotidienne']
        if 'limite_mensuelle' in data:
            limite.limite_mensuelle = data['limite_mensuelle']
        
        db.session.commit()
        
        return limite, 200

@limites_ns.route('/<int:id>')
class LimiteTransactionItem(Resource):
    @limites_ns.doc('get_limite')
    @limites_ns.marshal_with(limite_model)
    def get(self, id):
        """Récupère une limite spécifique"""
        limite = LimiteTransaction.query.get_or_404(id)
        return limite

def reset_quotidien_si_necessaire(limite):
    """Réinitialise le montant quotidien si le jour est nouveau"""
    maintenant = datetime.utcnow()
    if maintenant.date() != limite.date_reset_quotidien.date():
        limite.montant_quotidien = 0.0
        limite.date_reset_quotidien = maintenant
        db.session.commit()

def reset_mensuel_si_necessaire(limite):
    """Réinitialise le montant mensuel si le mois est nouveau"""
    maintenant = datetime.utcnow()
    if (maintenant.year, maintenant.month) != (limite.date_reset_mensuel.year, limite.date_reset_mensuel.month):
        limite.montant_mensuel = 0.0
        limite.date_reset_mensuel = maintenant
        db.session.commit()

def verifier_limites(utilisateur_id, montant):
    """Vérifie si l'utilisateur a dépassé ses limites"""
    limite = LimiteTransaction.query.filter_by(utilisateur_id=utilisateur_id).first()
    
    if not limite:
        limite = LimiteTransaction(utilisateur_id=utilisateur_id)
        db.session.add(limite)
        db.session.commit()
    
    reset_quotidien_si_necessaire(limite)
    reset_mensuel_si_necessaire(limite)
    
    if limite.montant_quotidien + montant > limite.limite_quotidienne:
        return False, f"Limite quotidienne dépassée. Limite: {limite.limite_quotidienne}€, Utilisé: {limite.montant_quotidien}€"
    
    if limite.montant_mensuel + montant > limite.limite_mensuelle:
        return False, f"Limite mensuelle dépassée. Limite: {limite.limite_mensuelle}€, Utilisé: {limite.montant_mensuel}€"
    
    return True, "Limites respectées"

def ajouter_montant_limite(utilisateur_id, montant):
    """Ajoute le montant aux compteurs de limites"""
    limite = LimiteTransaction.query.filter_by(utilisateur_id=utilisateur_id).first()
    
    if limite:
        reset_quotidien_si_necessaire(limite)
        reset_mensuel_si_necessaire(limite)
        
        limite.montant_quotidien += montant
        limite.montant_mensuel += montant
        db.session.commit()
