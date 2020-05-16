import re,math
from operator import itemgetter
from datetime import datetime
from app import db
from app.api import bp
from flask import request, jsonify, url_for, current_app, g
from app.api.errors import bad_request, error_response
from app.models import User, Post, Comment, Notification,comments_likes,Message
from app.api.auth import token_auth
from sqlalchemy import or_,and_
from app.utils.email import send_email
@bp.route('/users', methods=['POST'])
def create_user():
    # 注册
    data = request.get_json()
    if not data:
        return bad_request('you must post Json data.')
    message = {}
    # 先验证json有没有username属性，在验证username是否为空。
    if 'username' not in data or not data.get('username', None):
        message['username'] = 'Please provide a valid username'
    pattern = '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if 'email' not in data or not re.match(pattern, data.get('email', None)):
        message['email'] = 'Please provide a valid email address'
    if 'password' not in data or not data.get('password', None):
        message['password'] = 'please provide a valid password'
    if User.query.filter_by(username=data.get('username', None)).first():
        message['username'] = 'please use a different username.'
    if User.query.filter_by(email=data.get('email', None)).first():
        message['email'] = 'please use a different email.'
    if message:
        return bad_request(message)
    
    
    user = User()
    # 这里在实例user中添加了username和email属性
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()


    test = user.role
    # send confirm email
    token = user.generate_confirm_jwt()
    if not data.get('confirm_email_base_url'):
        confirm_url = current_app.config['CONFIRM_URL'] + token
    else:
        confirm_url = data.get('confirm_email_base_url') + token
    text_body = '''
    您好，{} ~
    欢迎注册！
    '''.format(user.username)
    html_body = '''
    <p>您好，{0}</p>
    <p>欢迎注册我的博客！大家一起来分享技术，畅谈人生~</p>
    <p></p>
    <p>请点击<a href="{1}">这里</a>确认您的账户</p>
    <p>或者把下面的链接粘贴到浏览器打开：</p>
    <p>{1}</p>
    '''.format(user.username,confirm_url)
    send_email(
        '邮件地址确认',
        sender=current_app.config['MAIL_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

    # to_dict()返回一个字典
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('/api.get_user', id=user.id)
    # response包含 、
    #   { "_links": { "self": "/api/users/2" }, "id": 2, "username": "liyang1" }
    return response


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    # 返回用户集合
    # 获取request中的'page',没找到返回1，强制转换成int型
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    data = User.to_collection_dict(
        User.query, page, per_page, '/api.get_users')
    return jsonify(data)


@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    # 返回一个用户
    # get_or_404()是根据primary_key来返回结果
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
    message = {}
    pattern = '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'

    # （？）这里怎么验证数据？ +
    #   我傻掉了，创建用户才验证数据完整性，即验证是否有username、email等等
    #   而修改则不需要，因为可以选择只修改username或者一部分。。。误：if not 'username' in data or not data.get('username',None):pass
    #   所以验证数据的时候只需要验证传来的json中有的那一部分就可以了。。。
    # 验证json数据
    if 'username' in data and not data.get('username', None):
        message['username'] = "Invalid username"
    if 'email' in data and not re.match(pattern, data.get('email', None)):
        message['email'] = "Invalid email"
    # 查询修改后的用户名是否重复
    if 'username' in data and User.query.filter_by(username=data['username']).first():
        message['username'] = "Unique username verification failed."
    # 查询邮箱是否重复
    if 'email' in data and User.query.filter_by(email=data['email']).first():
        message['email'] = "Unique email verification failed."
    if message:
        return bad_request(message)

    # 数据库接口
    user.from_dict(data)
    db.session.commit()

    # 修改完成后返回修改成功的json消息/或者返回修改成功的用户的信息
    return jsonify(user.to_dict())


@bp.route('/users/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    '''删除一个用户'''
    pass


'''------------------------------------------------------------------------------------------
    关注与取消关注
'''
@bp.route('/follow/<int:id>', methods=['GET'])
@token_auth.login_required
def follow(id):
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot follow yourself.')
    if g.current_user.is_following(user):
        return bad_request('You have already followed that user.')
    g.current_user.follow(user)
    #关注别人的时候给对方通知
    user.add_notification(
        'unread_follows_count',
        user.new_follows()
    )
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are now following %d.' % id
    })


@bp.route('/unfollow/<int:id>', methods=['GET'])
@token_auth.login_required
def unfollow(id):
    user = User.query.get_or_404(id)
    if g.current_user == user:
        return bad_request('You cannot unfollow yourself')
    if not g.current_user.is_following(user):
        return bad_request('You are not following this user.')
    g.current_user.unfollow(user)
    user.add_notification('unread_follows_count',user.new_follows())
    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'You are not following %d anymore.' % id
    })


'''
    返回关注了谁列表和我的粉丝列表----------------------------------------------------------------------
'''
@bp.route('/users/<int:id>/followeds/', methods=['GET'])
@token_auth.login_required
def get_followeds(id):
    '''获取用户关注列表'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get(
        'per_page', current_app.config['USERS_PER_PAGE'], type=int), 100)
    # （？）怎么理解user.followeds ？ +
    # 答：查询user关注了谁，user.followeds返回了一个查询结果，经过to_collection_dict()实现分页
    # （？）这里的user.followeds如何排序呢？用的是中间表，不知如何排序。。 -
    # 答：
    data = User.to_collection_dict(
        user.followeds, page, per_page, '/api.get_followeds', id=id)

    for item in data['items']:
        # （？）item['is_following']怎么理解？ +
        # 答：首先要知道data['items']是什么，很明显它是user的关注列表，
        #   item是一个经过to_dict()后的字典，但是字典里面并没有is_following
        #   所以说这里是新加了一个is_following的字典项，目的是为了返回更多信息给前台
        #   居然可以这样用，长见识了！！
        # 但是感觉这样有点多余，为什么要给每一个关注的用户打上已关注的标签呢？，毕竟既然他存在这里，就一定是关注了的。
        item['is_following'] = g.current_user.is_following(
            User.query.get(item['id']))

        # 获取用户开始关注 followed 的时间
        # （？）如何理解db.engine.execute？ +
        # 答：调查了文档，engine.execute执行给定的结构语句，返回一个ResultProxy。
        #   ResultProxy是一个包装了DB-API的指针对象，我们可以通过它轻易的访问行和列
        #   简而言之就是返回了一个二维数组(*有误) ，描述了返回结果的表。
        # （？）为什么返回的res可以列表化？ -
        # 答：请查看上面问题的回答，但是我还没有完全消化。
        res = db.engine.execute(
            "select * from followers where follower_id={} and followed_id={}".
            format(user.id, item['id']))
        item['timestamp'] = datetime.strptime(
            list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
    #按时间排序
    data['items']=sorted(data['items'],key=itemgetter('timestamp'), reverse=True)
    return jsonify(data)


@bp.route('/users/<int:id>/followers/', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    '''获取用户粉丝列表'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['USERS_PER_PAGE'], type=int), 100)
    data = User.to_collection_dict(
        user.followers, page, per_page, '/api.get_followers', id=id)
    last_follows_read_time = user.last_follows_read_time or datetime(1990,1,1)
    # 为每个 follower 添加 is_following 标志位
    for item in data['items']:
        item['is_following'] = g.current_user.is_following(
            User.query.get(item['id']))
        # 获取 follower 开始关注该用户的时间
        #（？）这里，为什么要用这么奇葩的方式查找数据库呢？ +
        # 答：每一次循环都会查询一次数据库，用sql语句执行可以提升性能
        res = db.engine.execute(
            "select * from followers where follower_id={} and followed_id={}".
            format(item['id'], user.id)
        )
        item['timestamp'] = datetime.strptime(
            list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f'
        )
        if item['timestamp']>last_follows_read_time:
            item['is_new'] = True
    data['items'] = sorted(data['items'], key=itemgetter('timestamp'), reverse=True)
    return jsonify(data)

# 返回关注的人的文章列表
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

# 返回用户的文章列表
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


@bp.route('/users/<int:id>/comments', methods=['GET'])
@token_auth.login_required
def get_user_comments(id):
    '''返回用户的所有评论'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['COMMENT_PER_PAGE'], type=int),
        100
    )
    data = Comment.to_collection_dict(user.comments.order_by(
        Comment.timestamp.desc()), page, per_page, '/api.get_user_comments', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/recived-comments/', methods=['GET'])
@token_auth.login_required
def get_user_recived_comments(id):
    '''获取用户收到的评论 和 回复'''
    #（？）获取用户收到的评论，现在A发了A的文章下发表了评论，如果评论下面c回复了b，那么只有A能收到消息，b却收不到，如何解决？ -
    # 答：
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(
        request.args.get(
            'per_page', current_app.config['COMMENT_PER_PAGE'], type=int),
        100
    )
    if not user:
        return bad_request('User not found.')
    ###
    # 1.获取用户的所有文章mypostid
    # 2.获取用户所有的评论mycommentid
    # 3.在comment表中筛选出，用户所有文章中的非回复评论 或者 回复我的
    # 
    ###
    mypostid = [post.id for post in user.posts]
    mycommentid = [comment.id for comment in user.comments]
    data = Comment.to_collection_dict(Comment.query.filter(
        or_(
            and_(Comment.post_id.in_(mypostid) , Comment.parent_id == None),
            Comment.parent_id.in_(mycommentid)
        )
    ).order_by(Comment.timestamp.desc()), page, per_page, '/api.get_user_recived_comments', id=id)

    # 为每一个评论添加是否是新消息的标签
    last_read_time = user.last_recived_comments_read_time or datetime(1990, 1, 1)
    for item in data['items']:
        if item['timestamp'] > last_read_time:
            item['is_new'] = True

    # user.last_recived_comments_read_time = datetime.utcnow()
    # user.add_notification('unread_recived_comments_count', 0)
    

    return jsonify(data)
@bp.route('/users/<int:id>/recived-comments-likes/', methods=['GET'])
@token_auth.login_required
def get_user_recived_comments_likes(id):
    '''返回该用户收到的评论赞'''
    # （？）点赞在comment_likes表（拿不到），评论在comments表（可以拿到）,如何获得用户收到的评论赞呢？ +
    # 答:comment_likes表拿不到？你导入啊！！
    user = User.query.get_or_404(id)
    page = request.args.get('page',1,type=int)
    per_page = request.args.get('per_page',5,type=int)
    if page<1:
        return error_response(404)
    if per_page<1:
        return error_response(404)
    last_read_time = user.last_likes_read_time or datetime(1990,1,1)
    user_all_likes_comments = user.comments.join(
        comments_likes,
    ).all()
    # （？）取得的数据是comment对象，并不知道谁点赞了这个comment，因为数据格式是likers[1,2] +
    #  表明这个comment的点赞对象是user1、user2，如何获得点赞对象的username呢？ 
    # 答：没办法，只有迭代user_all_likes_comments和likers数组，拆开来。
    # （？）这种分页方式会出现问题，同一个comment被不同用户点赞后，分页还是1个，1页。如何解决？ -
    # 答：算了，手动写分页功能。。
    data = {
        'items':[],
        '_meta':'',
        '_links':'',

    }
    for item in user_all_likes_comments:
        # item是一个comment对象
        for liker in item.likers:
            t = {}
            t['like_from_user'] = liker.to_dict()
            t['like_to_comment'] = item.to_dict()
            # 通过sql语句在中间表comments_likes中查找timestamp，加入进去
            res = db.engine.execute(
                "select * from comments_likes where user_id={} and comment_id={}"
                .format(liker.id,item.id)
            )
            t['timestamp'] = datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
            if t['timestamp']>last_read_time:
                t['is_new']=True
            data['items'].append(t)

    # 分页
    total_items = len(data['items'])
    total_pages = math.ceil(total_items / per_page)
    data['_meta'] = {
        'page':page,
        'per_page':per_page,
        'total_pages':total_pages,
        'total_items':total_items
    }
    data['_links'] = {
        'next':'',
        'prev':'',
        'self':''
    }

    data['items'] = sorted(data['items'],key=itemgetter('timestamp'),reverse=True)
    data['items'] = data['items'][(page-1)*per_page : page*per_page]
    return jsonify(data)

    





@bp.route('/users/<int:id>/clear-notifications/',methods=['GET'])
@token_auth.login_required
def clear_comments(id):
    user = User.query.get_or_404(id)
    if not user:
        return bad_request('User not found.')
    type = request.args.get('type',0,type=int)
    if type is None:
        return bad_request('Error: clear type is Null..')
    if type<0 or type>3:
        return error_response(404)
    if type==0:
        #comments
        user.last_recived_comments_read_time = datetime.utcnow()
        user.add_notification('unread_recived_comments_count', 0)
    elif type==1:
        #私信
        pass
    elif type==2:
        #新粉丝
        user.last_follows_read_time = datetime.utcnow()
        user.add_notification('unread_follows_count', 0)
    elif type==3:
        #收到的赞
        user.last_likes_read_time = datetime.utcnow()
        user.add_notification('unread_likes_count',0)
    db.session.commit()
    return jsonify({
        'status':'ok',
        'message':'clear comments ok.'
    })




@bp.route('/users/<int:id>/notifications', methods=['GET'])
@token_auth.login_required
def get_user_notifications(id):
    '''获取用户的最新通知列表'''
    user = User.query.get_or_404(id)
    since = request.args.get('since',0,type=float)
    if not user:
        return error_response(403)
    notes = user.notifications.order_by(
        Notification.timestamp.desc()
    )
    return jsonify([note.to_dict() for note in notes])
    






# -------------------------------------------私信
@bp.route('/users/<int:id>/messages-recipients/',methods=['GET'])
@token_auth.login_required
def get_user_messages_recipients(id):
    '''当前用户给谁发了私信，返回这些用户'''
    user = User.query.get_or_404(id)
    page = request.args.get('page',type=int,default=1)
    per_page=request.args.get('per_page',type=int) or 50
    if g.current_user != user:
        return error_response(403)
    data = user.to_collection_dict(
        user.messages_sent.group_by(Message.recipient_id).order_by(Message.timestamp.desc()),
        page,per_page,'/api.get_user_messages_recipients',id=id
    )

    return jsonify(data)

@bp.route('/users/<int:id>/messages-senders/',methods=['GET'])
@token_auth.login_required
def get_user_messages_senders(id):
    '''哪些用户 给我 发送了私信'''
    user = User.query.get_or_404(id)
    page = request.args.get('page',type=int,default=1)
    per_page=request.args.get('per_page',type=int) or 50
    data = user.to_collection_dict(
        user.messages_received.group_by(Message.sender_id).order_by(Message.timestamp.desc()),
        page,per_page,'/api.get_user_messages_senders',id=id
    )
    return jsonify(data)

@bp.route('/users/<int:id>/history-messages/',methods=['GET'])
@token_auth.login_required
def get_user_history_messages(id):
    '''取得我和from用户之间的私信记录'''
    user = User.query.get_or_404(id)
    if g.current_user != user:
        return bad_request(403)
    page = request.args.get('page',1,type=int)
    per_page = request.args.get('per_page',10000,type=int)
    from_id = request.args.get('from',type=int)
    if not from_id:
        return bad_request('from_id is None')
    recived = user.messages_received.filter_by(sender_id=from_id)
    sent = user.messages_sent.filter_by(recipient_id=from_id)
    history_messages = recived.union(sent).order_by(Message.timestamp)
    data = user.to_collection_dict(
        history_messages,
        page,per_page,'/api.get_user_history_messages',id=id
    )
    return jsonify(data)


@bp.route('/users/<int:id>/messages-all/',methods=['GET'])
@token_auth.login_required
def get_user_message_all(id):
    '''查询我发送的和我收到的用户'''
    user = User.query.get_or_404(id)
    if g.current_user!=user:
        return bad_request(403)
    page = request.args.get('page',1,type=int)
    per_page = request.args.get('per_page',100,type=int)
    recieved = user.messages_received.group_by(Message.sender_id)

    sent = user.messages_sent.group_by(Message.recipient_id)

    all = recieved.union(sent).order_by(Message.timestamp.desc()).all()
    st = set()
    for al in all:
        if al.sender==g.current_user:
            st.add(al.recipient)
        elif al.recipient == g.current_user:
            st.add(al.sender)
    result = []
    for s in list(st):
        result.append(s.to_dict())

    data = {
        "items":result
    }
    return jsonify(data)

@bp.route('/users/<int:id>/test',methods=['GET'])
@token_auth.login_required
def test(id):
    user = User.query.get_or_404(id)
    ret = user.new_follows()
    return jsonify({
        'rel':'1'
    })




#  ----------------------邮箱验证
# （？）路由传token
@bp.route('/confirm/<token>', methods=['GET'])
@token_auth.login_required
def confirm(token):
    '''用户收到验证邮件后，验证其账户'''
    if g.current_user.confirmed:
        return bad_request('您已经验证过邮箱了.')
    if g.current_user.verify_confirm_jwt(token):
        g.current_user.ping()
        db.session.commit()
        # 给用户发放新 JWT，因为要包含 confirmed: true
        token = g.current_user.get_jwt()
        return jsonify({
            'status': 'success',
            'message': '验证成功!',
            'token': token
        })
    else:
        return bad_request('验证失败，有可能链接过期了.')


@bp.route('/resend-confirm', methods=['POST'])
@token_auth.login_required
def resend_confirmation():
    '''重新发送确认账户的邮件'''
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')
    if 'confirm_email_base_url' not in data or not data.get('confirm_email_base_url').strip():
        return bad_request('Please provide a valid confirm email base url.')

    token = g.current_user.generate_confirm_jwt()



    text_body = '''
    您好，{} ~
    欢迎注册！
    '''.format(g.current_user.username)
    html_body = '''
    <p>您好，{0}</p>
    <p>欢迎注册我的博客！大家一起来分享技术，畅谈人生~</p>
    <p></p>
    <p>请点击<a href="{1}">这里</a>确认您的账户</p>
    <p>或者把下面的链接粘贴到浏览器打开：</p>
    <p>{1}</p>
    '''.format(g.current_user.username,data.get('confirm_email_base_url') + token)

    send_email('邮件地址确认',
               sender=current_app.config['MAIL_SENDER'],
               recipients=[g.current_user.email],
               text_body=text_body,
               html_body=html_body)
    return jsonify({
        'status': 'success',
        'message': '邮件已重新发送.'
    })

