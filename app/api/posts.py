from app import db
from app.api import bp

@bp.route('/posts',methods=('POST'))
def create_post():
    '''创建'''
    pass

@bp.route('/posts',methods=('GET'))
def get_posts():
    '''返回posts合集'''
    
    pass