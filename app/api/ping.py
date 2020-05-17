from flask import jsonify,g
from app.api import bp
from app import db
from app.models import User
from app.api.auth import token_auth

from flask_mail import Message
from app import mail

@bp.route('/ping')
def ping():
    msg = Message(
        'test Subject',
        sender='remly@qq.com',
        recipients=['583345725@qq.com']
    )
    msg.body = 'test body'
    msg.html = '<h1>test html<h1>'
    mail.send(msg)
    return 'ok',204