from app import db
from app.models import Post
from app.api import bp
from app.api.errors import bad_request,error_response
from app.api.auth import token_auth

from flask import request,jsonify,g

@bp.route('/posts',methods=['POST'])
@token_auth.login_required
def create_post():
    '''创建单个post'''
    data = request.get_json()
    if not data:
        return bad_request("Json expected!")
    message={}
    if not 'title' in data or not data.get('title',None):
        message['title'] = 'The title cannot be empty!'
    if not 'author_id' in data or not data.get('author_id',None):
        message['author_id'] = 'Author id necessary'
    if message:
        return bad_request(message)
    post = Post()
    post.from_dict(data)
    #（？）g.current_user是当前登录用户的一个User对象，可以把对象挂在post实例的属性上的吗？
    #       ....换句话提问就是数据库能储存对象了？
    #       ....既然没有作为字段存在数据库中，为什么在修改文章（update_post）中仍然可以访问post.author
    #   1.初步推测挂在post上的新增属性，但是类属性里面并没有定义，因此不会提交到数据库
    #       ....而是作为一个普通属性来使用
    #   2.有点明白了，请仔细阅读sqlalchemy文档，backref的相关内容
    #（？）为什么会出现错误？g对象没有current_user？
    #   g对象在auth.py中出现，换句话说通过验证后才会有current_user
    #   所以，你tm倒是把验证的装饰器给加上去啊！
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    response = post.to_dict()
    return jsonify(response)
    
@bp.route('/posts',methods=['GET'])
def get_posts():
    '''返回所有的posts合集'''
    page = request.args.get('page',1,type=int)
    per_page=request.args.get('per_page',10,type=int)
    post = Post()
    #这里返回的集合按照时间排序
    #参照flask-sqlalchemy文档：When you access it you will get back a new query object over all records.
    #Post.query会返回Post表中所有记录
    response = post.to_collection_dict(Post.query.order_by(Post.timestamp.desc()),page,per_page,'/api.get_posts')
    return jsonify(response)

@bp.route('/posts/<int:id>',methods=['GET'])
def get_post(id):
    '''返回一篇文章'''
    post = Post.query.get_or_404(id)
    post.views += 1
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict())

@bp.route('/posts/<int:id>',methods=['PUT'])
def update_post(id):
    '''修改post'''
    post = Post.query.get_or_404(id)
    if g.current_user != post.author:
        return error_response(403)
    data = request.get_json()
    if not data:
        return bad_request("Json expected!")
    message={}
    if 'title' in data and not data.get('title',None):
        message['title'] = "Nothing in title!"
    if 'body' in data and not data.get('body',None):
        message['body'] = 'Nothing in body!'
    if message:
        return bad_request(message)
    
    post.from_dict(data)
    db.session.commit()
    return jsonify(post.to_dict())

@bp.route('/posts/<int:id>',methods=['DELETE'])
def delete_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author:
        return error_response(403)
    db.session.delete(post)
    db.session.commit()
    return '',204