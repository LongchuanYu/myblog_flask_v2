from app import db
from app.models import Post
from app.api import bp
from app.api.errors import bad_request

from flask import request,jsonify,g

@bp.route('/posts',methods=['POST'])
def create_post():
    '''创建单个post'''
    print(g.current_user)
    return "haha"
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
    #（？）g.current_user是当前登录用户的一个User对象，可以把对象挂在post实例上的吗？

    #（？）为什么会出现错误？g对象没有current_user？
    #   g对象在auth.py中出现，换句话说通过验证后才会有current_user
    #   所以，你tm倒是把验证的装饰器给加上去啊！
    #post.author = g.current_user
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
    response = post.to_collection_dict(Post.query,page,per_page,'/api.get_posts')
    return jsonify(response)

@bp.route('/posts/<int:id>',methods=['GET'])
def get_post(id):
    '''返回单个post'''
    return jsonify(Post.query.get_or_404(id).to_dict())

@bp.route('/posts/<int:id>',methods=['PUT'])
def update_post(id):
    '''修改post'''
    post = Post.query.get_or_404(id)
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
