import re
from app import db
from app.api import bp
from flask import request,jsonify,url_for
from app.api.errors import bad_request
from app.models import User

@bp.route('/users',methods =['POST'])
def create_user():
    #注册
    data = request.get_json()
    if not data:
        return bad_request('you must post Json data.')
    message={}
    if 'username' not in data or not data.get('username',None):
        message['username'] = 'Please provide a valid username'
    pattern =  '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if 'email' not in data or not re.match(pattern,data.get('email',None)):
        message['email'] = 'Please provide a valid email address'
    if 'password' not in data or not data.get('password',None):
        message['password'] = 'please provide a valid password'
    if User.query.filter_by(username=data.get('username',None)).first():
        message['username']='please use a different username.'
    if User.query.filter_by(email=data.get('email',None)).first():
        message['username']='please use a different email.'
    if message:
        return bad_request(message)
    user=User()
    #这里在实例user中添加了username和email属性
    user.from_dict(data,new_user=True)
    db.session.add(user)
    db.session.commit()
    #to_dict()返回一个字典
    response = jsonify(user.to_dict())
    response.status_code=201
    response.headers['Location']=url_for('api.get_user',id = user.id)
    #response包含 、
    #   { "_links": { "self": "/api/users/2" }, "id": 2, "username": "liyang1" }
    return response

@bp.route('/users',methods=['GET'])
def get_users():
    #返回用户集合
    #获取request中的'page',没找到返回1，强制转换成int型
    page = request.args.get('page',1,type=int)
    per_page=request.args.get('per_page',10,type=int)
    data = User.query.paginate(page,per_page,False)
    res = {
        'items':[item.to_dict() for item in data.items]
    }
    return jsonify(res)
@bp.route('/users/<int:id>',methods=['GET'])
def get_user(id):
    #返回一个用户
    return jsonify(User.query.get_or_404(id).to_dict())

@bp.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    '''修改一个用户'''
    pass


@bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    '''删除一个用户'''
    pass
