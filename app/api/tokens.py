from flask import jsonify,g
from app import db
from app.api import bp
from app.api.auth import basic_auth,token_auth




@bp.route('/tokens',methods=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_jwt()
    db.session.commit()
    return jsonify({
        'token':token
    })


'''
# 改用jwt来实现token
# jwt只能自然过期
@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    g.current_user.revoke_token()
    #（？）revoke_token没有db.seesion.add()，为什么可以直接commit()？
    #   1.试验了一下，通过user实例修改属性后直接commit可以不用add。。
    db.session.commit()
    return '',204

'''