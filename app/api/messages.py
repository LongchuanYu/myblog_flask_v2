# -*- coding: utf-8
from flask import request,jsonify,url_for,g,current_app
from app import db
from app.api import bp
from app.api.auth import token_auth,basic_auth
from app.api.errors import error_response,bad_request
from app.models import User,Message
from app.utils.decorator import admin_required


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
    msg = Message()
    page = request.args.get('page',type=int,default=1)
    per_page = request.args.get('per_page',type=int,default=current_app.config['MESSAGE_PER_PAGE'])
    data = msg.to_collection_dict(Message.query.order_by(Message.timestamp.desc()),page,per_page,'/api.get_messages')
    return jsonify(data)


# 返回单个私信
@bp.route('/messages/<int:id>',methods=['GET'])
def get_message(id):
    response = Message.query.get_or_404(id)    
    return jsonify(response.to_dict())


# 修改单个私信
@bp.route('/messages/<int:id>',methods=['PUT'])
def update_message(id):
    pass


# 删除单个私信
@bp.route('/messages/<int:id>',methods=['DELETE'])
def delete_message(id):
    pass

@bp.route('/send-messages', methods=['POST'])
@token_auth.login_required
@admin_required
def send_messages():
    '''群发私信'''
    if g.current_user.get_task_in_progress('send_messages'):  # 如果用户已经有同名的后台任务在运行中时
        return bad_request('上一个群发私信的后台任务尚未结束')
    else:
        data = request.get_json()
        if not data:
            return bad_request('You must post JSON data.')
        if 'body' not in data or not data.get('body'):
            return bad_request(message={'body': 'Body is required.'})
        # 将 app.utils.tasks.send_messages 放入任务队列中
        g.current_user.launch_task('send_messages', '正在群发私信...', kwargs={'user_id': g.current_user.id, 'body': data.get('body')})
        return jsonify(message='正在运行群发私信后台任务')
