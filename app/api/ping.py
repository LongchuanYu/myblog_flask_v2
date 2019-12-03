from flask import jsonify
from app.api import bp
from app import db
from app.models import User

@bp.route('/ping',methods=['GET'])
def ping():
    user = User.query.filter_by(username='liyang1').first()
    user.username="laowang"
    db.session.commit()
    return jsonify('Success!')
