from flask import request,g,current_app,jsonify
from app import db
from app.api import bp
from app.models import Comment,Post,User
from app.api.errors import bad_request
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
    