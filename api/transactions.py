from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models import db, Compte, Transaction

transactions_ns = Namespace('transactions', description='Opérations de dépôt et retrait')

transaction_model = transactions_ns.model('Transaction', {
    'id': fields.Integer(readonly=True),
    # Accept both 'type_transaction' and legacy 'type'
    'type_transaction': fields.String(required=False, enum=['depot', 'retrait']),
    'type': fields.String(required=False, enum=['depot', 'retrait']),
    'montant': fields.Float(required=True, min=0.01),
    'compte_id': fields.Integer(required=True)
})


@transactions_ns.route('')
class TransactionResource(Resource):
    @transactions_ns.doc('create_transaction')
    @transactions_ns.expect(transaction_model)
    @transactions_ns.response(201, 'Transaction effectuée')
    @transactions_ns.response(400, 'Solde insuffisant ou compte bloqué')
    def post(self):
        """Effectue un dépôt ou un retrait sur un compte"""
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return {'erreur': 'données JSON invalides'}, 400

        compte_id = data.get('compte_id')
        if compte_id is None:
            return {'erreur': 'compte_id requis'}, 400

        compte = Compte.query.get(compte_id)
        if not compte:
            return {'erreur': 'compte introuvable'}, 404

        if compte.statut != 'actif':
            return {'erreur': 'compte non actif'}, 400

        montant = data.get('montant')
        if montant is None:
            return {'erreur': 'montant requis'}, 400
        try:
            montant = float(montant)
        except (TypeError, ValueError):
            return {'erreur': 'montant invalide'}, 400
        if montant <= 0:
            return {'erreur': 'montant doit etre positif'}, 400

        tx_type = data.get('type_transaction') or data.get('type')
        if tx_type not in ('retrait', 'depot'):
            return {'erreur': 'type de transaction invalide'}, 400

        if tx_type == 'retrait':
            if compte.solde < montant:
                return {'erreur': 'solde insuffisant'}, 400
            compte.solde -= montant
        else:  # depot
            compte.solde += montant

        transaction = Transaction(
            type_transaction=tx_type,
            montant=montant,
            compte_id=compte.id
        )
        db.session.add(transaction)
        db.session.commit()
        return {'nouveau_solde': compte.solde}, 201