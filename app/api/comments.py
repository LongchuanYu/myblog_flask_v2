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
    print(int(data.get('post_id')))
    post = Post.query.get_or_404(int(data.get('post_id')))
    commentcount = post.comments.all()
    return '111'
    # 新增评论的时候把通知写入db
    post.author.add_notification('unread_recived_comments_count')
    comment = Comment()
    comment.from_dict(data)
    comment.author = g.current_user
    comment.post= post
    db.session.add(comment)
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
    '''点赞'''
    comment = Comment.query.get_or_404(id)
    comment.liked_by(g.current_user)
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
    db.session.add(comment)
    db.session.commit()
    return jsonify({
        'status':'success',
        'message':'Unlike it.'
    })