from flask import jsonify
from app.api import bp

@bp.route('/ping',methods=['GET'])
def ping():
    return jsonify('Success!')
