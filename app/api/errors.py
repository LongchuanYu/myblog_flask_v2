from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES



def error_response(status_code,message=None):
    #HTTP_STATUS_CODES是一个A dict of status code，这里用get取得字典值
    payload = {
        'error':HTTP_STATUS_CODES.get(status_code,"Unknown error")
    }
    #message是一个字典
    if message:
        payload['message']=message
    response = jsonify(payload)
    #（？），response用jsonify格式成字符串了，为什么还能.status_code
    #   It turns the JSON output into a Response object with the application/json mimetype
    #   jsonify也能序列化一个数组或者把多个参数转换成字典
    #   参照flask文档，既然是Response object，name它就有一个status_code的属性
    response.status_code = status_code
    return response

def bad_request(message):
    return error_response(400,message)