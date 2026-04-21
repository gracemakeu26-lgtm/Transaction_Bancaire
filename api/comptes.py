from flask_restx import Namespace, Resource, fields
from flask import request
from models import db, Compte, Utilisateur
import random

comptes_ns = Namespace('comptes', description='Gestion des comptes bancaires')

compte_model = comptes_ns.model('Compte', {
    'id': fields.Integer(readonly=True),
    'numero_compte': fields.String(readonly=True),
    'type_compte': fields.String(required=True, enum=['courant', 'epargne']),
    'solde': fields.Float(readonly=True),
    'date_creation': fields.DateTime(readonly=True),
    'statut': fields.String(enum=['actif', 'bloque', 'ferme']),
    'utilisateur_id': fields.Integer(required=True)
})

def generer_numero_compte():
    return f"FR76{random.randint(10000000000, 99999999999)}"

@comptes_ns.route('')
class CompteList(Resource):
    @comptes_ns.doc('create_compte')
    @comptes_ns.expect(compte_model)
    @comptes_ns.marshal_with(compte_model, code=201)
    def post(self):
        """Crée un nouveau compte pour un utilisateur existant"""
        data = request.json
        utilisateur = Utilisateur.query.get_or_404(data['utilisateur_id'])
        nouveau_compte = Compte(
            numero_compte=generer_numero_compte(),
            type_compte=data['type_compte'],
            solde=0.0,
            utilisateur_id=utilisateur.id
        )
        db.session.add(nouveau_compte)
        db.session.commit()
        return nouveau_compte, 201

@comptes_ns.route('/<int:id>')
@comptes_ns.param('id', 'ID du compte')
@comptes_ns.response(404, 'Compte non trouvé')
class CompteItem(Resource):
    @comptes_ns.doc('get_compte')
    @comptes_ns.marshal_with(compte_model)
    def get(self, id):
        """Récupère les informations d'un compte"""
        compte = Compte.query.get_or_404(id)
        return compte

    @comptes_ns.doc('delete_compte')
    @comptes_ns.response(204, 'Compte supprimé')
    def delete(self, id):
        """Supprime un compte bancaire"""
        compte = Compte.query.get_or_404(id)
        if compte.solde != 0:
            comptes_ns.abort(400, "Impossible de supprimer un compte avec un solde non nul")
        db.session.delete(compte)
        db.session.commit()
        return '', 204