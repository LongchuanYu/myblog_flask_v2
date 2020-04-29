from flask import request,jsonify,url_for,g,current_app
from app import db
from app.api import bp
from app.api.auth import token_auth,basic_auth
from app.api.errors import error_response,bad_request
from app.models import User,Message



"""
# 新增一条私信:{
    body:'',
    recipient_id:''
}
"""
@bp.route('/messages',methods=['POST'])
@token_auth.login_required
def create_message(): 
    data = request.get_json()
    body = data.get('body',None)
    recipient_id = data.get('recipient_id',None)
    err = {}
    if not body:
        err['body'] = "No body in json or body is null."
    if not recipient_id:
        err['recipient_id'] = "No recipient_id in json or recipient_id is null."
    if err:
        return bad_request(err)
    
    tar_user = User.query.get_or_404(recipient_id)
    if tar_user == g.current_user:
        return bad_request('can not send to yourself.')
    message = Message()
    message.from_dict(data)
    # Message里面有外键sernder_id、recipient_id，在哪里给这些外键赋值的？ -
    # 答：
    message.sender = g.current_user
    message.recipient = tar_user
    db.session.add(message)
    db.session.commit()
    response = message.to_dict()
    return jsonify(response)


    
    
    
        



# 获取全部私信合集
@bp.route('/messages/',methods=['GET'])
def get_messages():
    pass


# 返回单个私信
@bp.route('/messages/<int:id>',methods=['GET'])
def get_message(id):
    pass


# 修改单个私信
@bp.route('/messages/<int:id>',methods=['PUT'])
def update_message(id):
    pass


# 删除单个私信
@bp.route('/messages/<int:id>',methods=['DELETE'])
def delete_message(id):
    pass

