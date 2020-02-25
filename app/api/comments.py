from flask import request,g,current_app,jsonify
from app import db
from app.api import bp
from app.models import Comment,Post,User
from app.api.errors import bad_request,error_response
from app.api.auth import token_auth

@bp.route('/comments',methods=['POST'])
@token_auth.login_required
def create_comment():
    '''create new comment in post'''
    data = request.get_json()
    if not data:
        return bad_request('you must have a Json data.')
    if not 'body' in data or not data.get('body').strip():
        return bad_request('Body is required.')
    if not 'post_id' in data or not data.get('post_id'):
        return bad_request('Post id is required.')
    post = Post.query.get_or_404(int(data.get('post_id')))
    comment = Comment()
    comment.from_dict(data)
    comment.author = g.current_user
    comment.post= post
    db.session.add(comment)
    db.session.commit()
    # 新增评论的时候把通知写入db
    if data.get('parent_id'):
        #是回复就通知回复的对象
        reply_comment = Comment.query.get_or_404(int(data.get('parent_id')))
        reply_comment.author.add_notification('unread_recived_comments_count',reply_comment.author.new_recived_comments())
    else:
        #是评论就通知文章作者，。
        print('评论')
        post.author.add_notification('unread_recived_comments_count',post.author.new_recived_comments())
    db.session.commit()
    response = comment.to_dict()
    return response

@bp.route('/comments',methods=['GET'])
@token_auth.login_required
def get_comments():
    '''Get All Comments'''
    page = request.args.get('page',1,type=int)
    per_page=min(request.args.get(
        'per_page',current_app.config['COMMENT_PER_PAGE'],type=int
    ),100)
    data = Comment.to_collection_dict(
        Comment.query.order_by(Comment.timestamp.desc()),
        page,
        per_page,
        '/api.get_comments'
    )
    return jsonify(data)
    
@bp.route('/comments/<int:id>',methods=['DELETE'])
@token_auth.login_required
def delete_comment(id):
    '''Delete Comments
    post作者可以删除所有comment
    或者
    comment作者只能删除自己的comment
    相反
    既不是post作者也不是comment作者
    '''
    comment = Comment.query.get_or_404(id)
    if g.current_user != comment.author and g.current_user != comment.post.author:
        return error_response(403)
    # 给文章作者发送新评论通知(需要自动减1)
    comment.post.author.add_notification('unread_recived_comments_count',
                                         comment.post.author.new_recived_comments())
    db.session.delete(comment)
    db.session.commit()
    return '',204
@bp.route('/comments/<int:id>',methods=['GET'])
@token_auth.login_required
def get_comment(id):
    '''返回一个comment'''
    comment = Comment.query.get_or_404(id) 
    return jsonify(comment.to_dict())


@bp.route('/comments/<int:id>',methods=['PUT'])
@token_auth.login_required
def update_comment(id):
    data = request.get_json()
    comment = Comment.query.get_or_404(id)
    if not data or not data.get('body',None):
        return bad_request('Invalid Json Data')
    if g.current_user != comment.author and g.current_user != comment.post.author:
        return error_response(403)
    
    comment.body = data['body']
    db.session.commit()
    return jsonify(comment.to_dict())

###
# Star
###
@bp.route('/comments/<int:id>/like',methods=['GET'])
@token_auth.login_required
def like_comment(id):
    '''当前用户来点赞这个评论'''
    comment = Comment.query.get_or_404(id)
    comment.liked_by(g.current_user)
    # 通知这个评论的主人有新消息了
    new_likes_count = comment.author.new_likes_count()
    comment.author.add_notification(
        'unread_likes_count',
        new_likes_count
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({
        'status':'success',
        'message':'like it.'
    })

@bp.route('/comments/<int:id>/unlike',methods=['GET'])
@token_auth.login_required
def unlike_comment(id):
    '''取消点赞'''
    comment = Comment.query.get_or_404(id)
    comment.unliked_by(g.current_user)
    # 更新点赞消息
    new_likes_count = comment.author.new_likes_count()
    comment.author.add_notification(
        'unread_likes_count',
        new_likes_count
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({
        'status':'success',
        'message':'Unlike it.'
    })