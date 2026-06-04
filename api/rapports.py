from flask_restx import Namespace, Resource, fields
from flask import request, send_file
from models import db, Transaction, Virement, Utilisateur, Compte
from datetime import datetime, timedelta
import csv
import io

rapports_ns = Namespace('rapports', description='Rapports et statistiques bancaires')

statistiques_model = rapports_ns.model('Statistiques', {
    'solde_total': fields.Float(),
    'nombre_transactions': fields.Integer(),
    'montant_total_depots': fields.Float(),
    'montant_total_retraits': fields.Float(),
    'nombre_virements_envoyes': fields.Integer(),
    'nombre_virements_recus': fields.Integer(),
    'montant_virements_envoyes': fields.Float(),
    'montant_virements_recus': fields.Float(),
    'periode': fields.String()
})

@rapports_ns.route('/statistiques')
class StatistiquesGlobales(Resource):
    @rapports_ns.doc('get_statistiques')
    @rapports_ns.marshal_with(statistiques_model)
    def get(self):
        """Récupère les statistiques globales de la banque (admin seulement)"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            rapports_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe or not utilisateur.is_admin:
            rapports_ns.abort(403, "Accès administrateur requis")
        
        comptes = Compte.query.all()
        solde_total = sum(c.solde for c in comptes)
        
        transactions = Transaction.query.all()
        nombre_transactions = len(transactions)
        
        depots = [t for t in transactions if t.type_transaction == 'depot']
        retraits = [t for t in transactions if t.type_transaction == 'retrait']
        
        montant_depots = sum(t.montant for t in depots)
        montant_retraits = sum(t.montant for t in retraits)
        
        virements = Virement.query.filter_by(statut='complétée').all()
        nombre_virements_envoyes = len(virements)
        montant_virements = sum(v.montant for v in virements)
        
        return {
            'solde_total': solde_total,
            'nombre_transactions': nombre_transactions,
            'montant_total_depots': montant_depots,
            'montant_total_retraits': montant_retraits,
            'nombre_virements_envoyes': nombre_virements_envoyes,
            'nombre_virements_recus': nombre_virements_envoyes,
            'montant_virements_envoyes': montant_virements,
            'montant_virements_recus': montant_virements,
            'periode': f"depuis le {min(t.date_transaction for t in transactions).date() if transactions else 'N/A'}"
        }, 200

@rapports_ns.route('/utilisateur/<int:user_id>')
class StatistiquesUtilisateur(Resource):
    @rapports_ns.doc('get_user_statistiques')
    @rapports_ns.marshal_with(statistiques_model)
    def get(self, user_id):
        """Récupère les statistiques d'un utilisateur"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            rapports_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            rapports_ns.abort(401, "Authentification échouée")
        
        if utilisateur.id != user_id and not utilisateur.is_admin:
            rapports_ns.abort(403, "Accès non autorisé")
        
        comptes = Compte.query.filter_by(utilisateur_id=user_id).all()
        solde_total = sum(c.solde for c in comptes)
        
        transactions = Transaction.query.filter(
            Transaction.compte_id.in_([c.id for c in comptes])
        ).all()
        
        nombre_transactions = len(transactions)
        depots = [t for t in transactions if t.type_transaction == 'depot']
        retraits = [t for t in transactions if t.type_transaction == 'retrait']
        
        montant_depots = sum(t.montant for t in depots)
        montant_retraits = sum(t.montant for t in retraits)
        
        virements_envoyes = Virement.query.filter_by(
            compte_source_id=comptes[0].id if comptes else None,
            statut='complétée'
        ).all() if comptes else []
        
        virements_recus = Virement.query.filter(
            Virement.compte_destination_id.in_([c.id for c in comptes]),
            Virement.statut == 'complétée'
        ).all()
        
        return {
            'solde_total': solde_total,
            'nombre_transactions': nombre_transactions,
            'montant_total_depots': montant_depots,
            'montant_total_retraits': montant_retraits,
            'nombre_virements_envoyes': len(virements_envoyes),
            'nombre_virements_recus': len(virements_recus),
            'montant_virements_envoyes': sum(v.montant for v in virements_envoyes),
            'montant_virements_recus': sum(v.montant for v in virements_recus),
            'periode': 'toutes les périodes'
        }, 200

@rapports_ns.route('/export/transactions/<int:compte_id>')
class ExportTransactions(Resource):
    @rapports_ns.doc('export_transactions')
    def get(self, compte_id):
        """Exporte les transactions d'un compte en CSV"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            rapports_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            rapports_ns.abort(401, "Authentification échouée")
        
        compte = Compte.query.get_or_404(compte_id)
        if compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            rapports_ns.abort(403, "Accès non autorisé")
        
        transactions = Transaction.query.filter_by(compte_id=compte_id).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Type', 'Montant', 'Date', 'Description', 'Statut'])
        
        for t in transactions:
            writer.writerow([
                t.id,
                t.type_transaction,
                t.montant,
                t.date_transaction.isoformat(),
                t.description or '',
                t.statut
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'transactions_compte_{compte_id}_{datetime.now().strftime("%Y%m%d")}.csv'
        )

@rapports_ns.route('/export/virements/<int:compte_id>')
class ExportVirements(Resource):
    @rapports_ns.doc('export_virements')
    def get(self, compte_id):
        """Exporte les virements d'un compte en CSV"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        
        if not email or not mot_de_passe:
            rapports_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            rapports_ns.abort(401, "Authentification échouée")
        
        compte = Compte.query.get_or_404(compte_id)
        if compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            rapports_ns.abort(403, "Accès non autorisé")
        
        virements = Virement.query.filter(
            (Virement.compte_source_id == compte_id) | (Virement.compte_destination_id == compte_id)
        ).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'De', 'Vers', 'Montant', 'Date', 'Statut', 'Référence', 'Motif'])
        
        for v in virements:
            writer.writerow([
                v.id,
                v.compte_source.numero_compte,
                v.compte_destination.numero_compte,
                v.montant,
                v.date_virement.isoformat(),
                v.statut,
                v.reference,
                v.motif or ''
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'virements_compte_{compte_id}_{datetime.now().strftime("%Y%m%d")}.csv'
        )

@rapports_ns.route('/solde-quotidien/<int:compte_id>')
class SoldeQuotidien(Resource):
    @rapports_ns.doc('get_solde_quotidien')
    def get(self, compte_id):
        """Récupère l'historique des soldes quotidiens"""
        email = request.args.get('email')
        mot_de_passe = request.args.get('password')
        jours = request.args.get('jours', 30, type=int)
        
        if not email or not mot_de_passe:
            rapports_ns.abort(400, "Email et mot de passe requis")
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur or utilisateur.mot_de_passe != mot_de_passe:
            rapports_ns.abort(401, "Authentification échouée")
        
        compte = Compte.query.get_or_404(compte_id)
        if compte.utilisateur_id != utilisateur.id and not utilisateur.is_admin:
            rapports_ns.abort(403, "Accès non autorisé")
        
        transactions = Transaction.query.filter(
            Transaction.compte_id == compte_id,
            Transaction.date_transaction >= datetime.utcnow() - timedelta(days=jours)
        ).order_by(Transaction.date_transaction).all()
        
        soldes_quotidiens = {}
        solde_courant = compte.solde
        
        for t in transactions:
            date = t.date_transaction.date()
            if date not in soldes_quotidiens:
                soldes_quotidiens[date] = solde_courant
        
        return {
            'compte_id': compte_id,
            'soldes_quotidiens': {str(k): v for k, v in soldes_quotidiens.items()},
            'solde_actuel': compte.solde,
            'periode_jours': jours
        }, 200
