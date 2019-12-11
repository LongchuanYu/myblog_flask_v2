from flask import jsonify,g
from app.api import bp
from app import db
from app.models import User

@bp.route('/ping',methods=['POST'])
def ping():
    print(g.get('current_user'))
    return "123"
