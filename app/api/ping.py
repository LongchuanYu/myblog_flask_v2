from flask import jsonify,g
from app.api import bp
from app import db
from app.models import User
from app.api.auth import token_auth

@bp.route('/ping',methods=['POST'])
@token_auth.login_required
def ping():
    user = g.current_user
    print('current_user test')
    return "123"
