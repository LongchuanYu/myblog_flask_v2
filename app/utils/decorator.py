from functools import wraps
from flask import g
from app.api.errors import error_response
from app.models.exts import Permission


def permission_required(permission):
    '''检查常规权限  1.如果该装饰器用于什么函数，那么f就是这个函数'''
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 权限验证不通过，不继续执行f
            if not g.current_user.can(permission):  # 用户通过了Basic Auth认证后，就会在当前会话中附带 g.current_user
                return error_response(403)
            # 验证通过，继续执行函数f
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    '''检查管理员权限'''
    return permission_required(Permission.ADMIN)(f)