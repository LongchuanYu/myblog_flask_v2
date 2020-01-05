import os
#__file__:
#   命令行运行python config.py则只获得文件名+后缀
#   命令行运行python 绝对路径\config.py则可获得完整路径

#os.path.dirname ：去掉文件名，返回目录
#os.path.abspath：获取绝对路径

basedir = os.path.abspath(os.path.dirname(__file__))
class Config(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir,'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'DEV'
    USERS_PER_PAGE = 10
    POSTS_PER_PAGE=10
    COMMENT_PER_PAGE=50