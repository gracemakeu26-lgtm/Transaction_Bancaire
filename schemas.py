from flask_marshmallow import Marshmallow
from models import Utilisateur

ma = Marshmallow()

class UtilisateurSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Utilisateur