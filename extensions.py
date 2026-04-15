from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api

db = SQLAlchemy()

# Création de l'objet Api (sera initialisé dans app.py)
api = Api(
    title="API de Gestion des Transactions Bancaires",
    version="1.0",
    description="Système de gestion des utilisateurs et des transactions. Documentation interactive Swagger.",
    doc="/docs"  # Swagger UI sera accessible sur /docs
)