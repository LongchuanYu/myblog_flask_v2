import re
from datetime import datetime
from app import db
from app.api import bp
from flask import request,jsonify,url_for,current_app,g
from app.api.errors import bad_request
from app.models import User,Post,Comment
from app.api.auth import token_auth
@bp.route('/users',methods =['POST'])
def create_user():
    #注册 
    data = request.get_json()
    if not data:
        return bad_request('you must post Json data.')
    message={}
    #先验证json有没有username属性，在验证username是否为空。
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
        message['email']='please use a different email.'
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
    response.headers['Location']=url_for('/api.get_user',id = user.id)
    #response包含 、
    #   { "_links": { "self": "/api/users/2" }, "id": 2, "username": "liyang1" }
    return response

@bp.route('/users',methods=['GET'])
@token_auth.login_required
def get_users():
    #返回用户集合
    #获取request中的'page',没找到返回1，强制转换成int型
    page = request.args.get('page',1,type=int)
    per_page=request.args.get('per_page',10,type=int)
    data = User.to_collection_dict(User.query,page,per_page,'/api.get_users')
    return jsonify(data)

@bp.route('/users/<int:id>',methods=['GET'])
@token_auth.login_required
def get_user(id):
    #返回一个用户
    #get_or_404()是根据primary_key来返回结果
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return jsonify(user.to_dict(include_email=True))
    data = user.to_dict()
    data['is_following'] = g.current_user.is_following(user) 
    return jsonify(data)

@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    '''修改一个用户
    @param {json} user:{
        "username":"liyang",
        "email":"liyang@qq.com",
        #新建用户才有password，修改则没有password
    }
    @emit {json} user:{...}
    '''
    data = request.get_json()
    user = User.query.get_or_404(id)
    if not data:
        return bad_request('Json Required !')
    message={}
    pattern =  '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    
    #（？）这里怎么验证数据？ +
    #   我傻掉了，创建用户才验证数据完整性，即验证是否有username、email等等
    #   而修改则不需要，因为可以选择只修改username或者一部分。。。误：if not 'username' in data or not data.get('username',None):pass
    #   所以验证数据的时候只需要验证传来的json中有的那一部分就可以了。。。
    #验证json数据
    if 'username' in data and not data.get('username',None):
        message['username'] = "Invalid username"
    if 'email' in data and not re.match(pattern,data.get('email',None)):
        message['email'] = "Invalid email"
    #查询修改后的用户名是否重复
    if 'username' in data and User.query.filter_by(username=data['username']).first():
        message['username'] = "Unique username verification failed."
    #查询邮箱是否重复
    if 'email' in data and User.query.filter_by(email=data['email']).first():
        message['email'] = "Unique email verification failed."
    if message:
        return bad_request(message)

    
    #数据库接口
    user.from_dict(data)
    db.session.commit()
    

    #修改完成后返回修改成功的json消息/或者返回修改成功的用户的信息
    return jsonify(user.to_dict())
 

@bp.route('/users/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    '''删除一个用户'''
    pass





'''------------------------------------------------------------------------------------------
    关注与取消关注
'''
@bp.route('/follow/<int:id>',methods=['GET'])
@token_auth.login_required
def follow(id):
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot follow yourself.')
    if g.current_user.is_following(user):
        return bad_request('You have already followed that user.')
    g.current_user.follow(user) 
    db.session.commit()
    return jsonify({
        'status':'success',
        'message':'You are now following %d.' % id
    })

@bp.route('/unfollow/<int:id>',methods=['GET'])
@token_auth.login_required
def unfollow(id):
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot unfollow yourself')
    if not g.current_user.is_following(user):
        return bad_request('You are not following this user.')
    g.current_user.unfollow(user)
    db.session.commit()
    return jsonify({
        'status':'success',
        'message':'You are not following %d anymore.' %id
    })



'''
    返回关注了谁列表和我的粉丝列表
'''
@bp.route('/users/<int:id>/followeds/',methods=['GET'])
@token_auth.login_required
def get_followeds(id):
    user = User.query.get_or_404(id)
    page=request.args.get('page',1,type=int)
    per_page = min(request.args.get('per_page',current_app.config['USERS_PER_PAGE'],type=int),100)
    #（？）怎么理解user.followeds ？ +
    # 答：查询user关注了谁，user.followeds返回了一个查询结果，经过to_collection_dict()实现分页
    data = User.to_collection_dict(user.followeds,page,per_page,'/api.get_followeds',id=id)

    for item in data['items']:
        #（？）item['is_following']怎么理解？ + 
        # 答：首先要知道data['items']是什么，很明显它是user的关注列表，
        #   item是一个经过to_dict()后的字典，但是字典里面并没有is_following
        #   所以说这里是新加了一个is_following的字典项，目的是为了返回更多信息给前台
        #   居然可以这样用，长见识了！！
        # 但是感觉这样有点多余，为什么要给每一个关注的用户打上已关注的标签呢？，毕竟既然他存在这里，就一定是关注了的。
        item['is_following'] = g.current_user.is_following(User.query.get(item['id']))


        # 获取用户开始关注 followed 的时间
        #（？）如何理解db.engine.execute？ +
        # 答：调查了文档，engine.execute执行给定的结构语句，返回一个ResultProxy。
        #   ResultProxy是一个包装了DB-API的指针对象，我们可以通过它轻易的访问行和列
        #   简而言之就是返回了一个二维数组* ，描述了返回结果的表。
        #（？）为什么返回的res可以列表化？ +
        # 答：请查看上面问题的回答
        res = db.engine.execute(
            "select * from followers where follower_id={} and followed_id={}".
            format(user.id, item['id']))
        item['timestamp'] = datetime.strptime(
            list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
    return jsonify(data)

@bp.route('/users/<int:id>/followers/', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['USERS_PER_PAGE'], type=int), 100)
    data = User.to_collection_dict(
        user.followers, page, per_page, '/api.get_followers', id=id)
    # 为每个 follower 添加 is_following 标志位
    for item in data['items']:
        item['is_following'] = g.current_user.is_following(
            User.query.get(item['id']))
        # 获取 follower 开始关注该用户的时间
        res = db.engine.execute(
            "select * from followers where follower_id={} and followed_id={}".
            format(item['id'], user.id))
        item['timestamp'] = datetime.strptime(
            list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
    return jsonify(data)

#返回关注的人的文章列表
@bp.route('/users/<int:id>/followeds-posts/', methods=['GET'])
def get_user_followed_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Post.to_collection_dict(
        user.followed_posts.order_by(Post.timestamp.desc()), page, per_page,
        '/api.get_user_followed_posts', id=id)
    return jsonify(data)

#返回用户的文章列表
@bp.route('/users/<int:id>/posts/', methods=['GET'])
# @token_auth.login_required
def get_user_posts(id):
    '''返回该用户的所有文章文章列表'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['POSTS_PER_PAGE'], type=int), 100)
    data = Post.to_collection_dict(
        user.posts.order_by(Post.timestamp.desc()), page, per_page,
        '/api.get_user_posts', id=id)
    return jsonify(data)



@bp.route('/users/<int:id>/comments',methods=['GET'])
@token_auth.login_required
def get_user_comments(id):
    user = User.query.get_or_404(id)
    page = 1
    per_page=5
    data = user.comments.order_by(Comment.timestamp.desc()).paginate(page,per_page,False)
    return 'jsonify(data)'