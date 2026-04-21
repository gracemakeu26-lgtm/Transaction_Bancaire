from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Compte, Transaction

transactions_ns = Namespace('transactions', description='Opérations de dépôt et retrait')

transaction_model = transactions_ns.model('Transaction', {
    'id': fields.Integer(readonly=True),
    'type_transaction': fields.String(required=True, enum=['depot', 'retrait']),
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
        data = request.json
        compte = Compte.query.get_or_404(data['compte_id'])
        if compte.statut != 'actif':
            transactions_ns.abort(400, "Le compte n'est pas actif")
        
        montant = data['montant']
        if data['type_transaction'] == 'retrait':
            if compte.solde < montant:
                transactions_ns.abort(400, "Solde insuffisant")
            compte.solde -= montant
        else:  # depot
            compte.solde += montant
        
        transaction = Transaction(
            type_transaction=data['type_transaction'],
            montant=montant,
            compte_id=compte.id
        )
        db.session.add(transaction)
        db.session.commit()
        return {'message': 'Transaction réussie', 'nouveau_solde': compte.solde}, 201