from flask import Blueprint, request, jsonify
from models import db, Utilisateur
import re
from datetime import datetime

utilisateur_bp = Blueprint('utilisateur', __name__, url_prefix='/api/utilisateurs')

# Validation simple d'email
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Génération simple de numéro de compte (à remplacer par une logique plus robuste en production)
def generer_numero_compte():
    import random
    return f"FR76{random.randint(10000000000, 99999999999)}"

@utilisateur_bp.route('', methods=['POST'])
def ajouter_utilisateur():
    """
    Ajoute un nouvel utilisateur (client bancaire) dans le système.
    ---
    Attend un JSON avec les champs requis.
    """
    data = request.get_json()
    
    # Validation des champs obligatoires
    required_fields = ['nom', 'prenom', 'email', 'telephone', 'date_naissance', 
                       'adresse', 'type_compte', 'solde_initial']
    for field in required_fields:
        if field not in data:
            return jsonify({'erreur': f'Champ manquant : {field}'}), 400

    # Validation email
    if not is_valid_email(data['email']):
        return jsonify({'erreur': 'Format d\'email invalide'}), 400

    # Validation type de compte
    types_valides = ['courant', 'epargne', 'joint']
    if data['type_compte'] not in types_valides:
        return jsonify({'erreur': f'Type de compte invalide. Choisir parmi {types_valides}'}), 400

    # Vérification unicité email
    if Utilisateur.query.filter_by(email=data['email']).first():
        return jsonify({'erreur': 'Cet email est déjà utilisé'}), 409

    try:
        date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erreur': 'Format de date invalide. Utiliser YYYY-MM-DD'}), 400

    # Création de l'utilisateur
    nouvel_utilisateur = Utilisateur(
        nom=data['nom'],
        prenom=data['prenom'],
        email=data['email'],
        telephone=data['telephone'],
        date_naissance=date_naissance,
        adresse=data['adresse'],
        type_compte=data['type_compte'],
        numero_compte=generer_numero_compte(),
        solde_initial=float(data['solde_initial']),
        statut=data.get('statut', 'actif')
    )

    db.session.add(nouvel_utilisateur)
    db.session.commit()

    return jsonify(nouvel_utilisateur.to_dict()), 201

@utilisateur_bp.route('', methods=['GET'])
def lister_utilisateurs():
    """
    Retourne la liste de tous les utilisateurs enregistrés.
    Possibilité de filtrer par statut via paramètre ?statut=actif
    """
    statut_filtre = request.args.get('statut')
    query = Utilisateur.query
    
    if statut_filtre:
        query = query.filter_by(statut=statut_filtre)
    
    utilisateurs = query.all()
    return jsonify([u.to_dict() for u in utilisateurs]), 200