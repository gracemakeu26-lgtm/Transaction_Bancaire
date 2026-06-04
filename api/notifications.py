from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Notification, Utilisateur
from datetime import datetime

notifications_ns = Namespace('notifications', description='Gestion des notifications')

notification_model = notifications_ns.model('Notification', {
    'id': fields.Integer(readonly=True),
    'utilisateur_id': fields.Integer(readonly=True),
    'type_notification': fields.String(enum=['virement_envoyé', 'virement_reçu', 'depot', 'retrait', 'alerte']),
    'message': fields.String(),
    'date_creation': fields.DateTime(readonly=True),
    'is_read': fields.Boolean(),
    'montant': fields.Float()
})

@notifications_ns.route('')
class NotificationList(Resource):
    @notifications_ns.doc('list_notifications')
    @notifications_ns.marshal_list_with(notification_model)
    def get(self):
        """Liste toutes les notifications de l'utilisateur"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            notifications_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            notifications_ns.abort(401, "Authentification échouée")
        
        notifications = Notification.query.filter_by(utilisateur_id=utilisateur.id).order_by(
            Notification.date_creation.desc()
        ).all()
        return notifications, 200

@notifications_ns.route('/<int:id>')
class NotificationItem(Resource):
    @notifications_ns.doc('get_notification')
    @notifications_ns.marshal_with(notification_model)
    def get(self, id):
        """Récupère une notification spécifique"""
        notification = Notification.query.get_or_404(id)
        return notification
    
    @notifications_ns.doc('mark_as_read')
    @notifications_ns.response(200, 'Notification marquée comme lue')
    def put(self, id):
        """Marque une notification comme lue"""
        notification = Notification.query.get_or_404(id)
        notification.is_read = True
        db.session.commit()
        return {'message': 'Notification marquée comme lue'}, 200

@notifications_ns.route('/utilisateur/<int:user_id>')
class NotificationUtilisateur(Resource):
    @notifications_ns.doc('get_user_notifications')
    @notifications_ns.marshal_list_with(notification_model)
    def get(self, user_id):
        """Liste les notifications d'un utilisateur spécifique (admin seulement)"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            notifications_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe or not utilisateur.is_admin:
            notifications_ns.abort(403, "Accès administrateur requis")
        
        notifications = Notification.query.filter_by(utilisateur_id=user_id).order_by(
            Notification.date_creation.desc()
        ).all()
        return notifications, 200
    
    @notifications_ns.doc('mark_all_as_read')
    @notifications_ns.response(200, 'Toutes les notifications marquées comme lues')
    def put(self, user_id):
        """Marque toutes les notifications comme lues"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            notifications_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            notifications_ns.abort(401, "Authentification échouée")
        
        if utilisateur.id != user_id and not utilisateur.is_admin:
            notifications_ns.abort(403, "Vous ne pouvez modifier que vos notifications")
        
        Notification.query.filter_by(utilisateur_id=user_id).update({'is_read': True})
        db.session.commit()
        return {'message': 'Toutes les notifications marquées comme lues'}, 200

@notifications_ns.route('/unread/<int:user_id>')
class UnreadNotifications(Resource):
    @notifications_ns.doc('get_unread_count')
    def get(self, user_id):
        """Compte les notifications non lues"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            notifications_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            notifications_ns.abort(401, "Authentification échouée")
        
        if utilisateur.id != user_id and not utilisateur.is_admin:
            notifications_ns.abort(403, "Accès non autorisé")
        
        count = Notification.query.filter_by(utilisateur_id=user_id, is_read=False).count()
        return {'unread_count': count}, 200
