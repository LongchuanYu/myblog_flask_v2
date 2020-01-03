from flask import request,g
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