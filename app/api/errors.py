# -*- coding: utf-8
from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from app import db
from app.api import bp


def error_response(status_code,message=None):
    #HTTP_STATUS_CODES是一个A dict of status code，这里用get取得字典值
    payload = {
        'error':HTTP_STATUS_CODES.get(status_code,"Unknown error")
    }
    #message是一个包含多个错误字段的字典,或者字符串
    #   message将会拼接到payload中返回
    if message:
        payload['message']=message
    response = jsonify(payload)
    #（？），response用jsonify格式成字符串了，为什么还能.status_code
    #   It turns the JSON output into a Response object with the application/json mimetype
    #   jsonify也能序列化一个数组或者把多个参数转换成字典
    #   参照flask文档，既然是Response object，那么它就有一个status_code的属性
    response.status_code = status_code
    return response

def bad_request(message):
    return error_response(400,message)

@bp.app_errorhandler(404)
def not_found_error(error):
    return error_response(404)
@bp.app_errorhandler(500)
def internal_error(error):

    #（？）为什么要回滚？
    db.session.rollback()
    return error_response(500)
