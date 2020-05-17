from flask import jsonify,g
from app.api import bp
from app import db
from app.models import User
from app.api.auth import token_auth

from flask_mail import Message
from app import mail

@bp.route('/ping')
def ping():
    return 'ok'