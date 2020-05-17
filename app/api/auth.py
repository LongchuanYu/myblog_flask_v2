from flask import g
from flask_httpauth import HTTPBasicAuth,HTTPTokenAuth
from app.models import User
from app.api.errors import error_response

#这是一个basic认证的入口，在其他地方导入basic_auth
# basic_auth用于登录认证用户
basic_auth=HTTPBasicAuth()

# 登录后的认证依靠token_token
token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verify_password(username,password):
    print("basic_auth")
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False
    g.current_user = user
    return user.check_password(password)

@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)

@token_auth.verify_token
def verify_token(token):
    print("verify_token")
    g.current_user = User.verify_jwt(token) if token else None
    #   根据返回的true或false来判断验证是否成功
    return g.current_user is not None

@token_auth.error_handler
def token_auth_error():
    return error_response(401)