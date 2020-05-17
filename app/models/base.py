import base64,os,jwt,json
from app import db
from hashlib import md5
from time import time
from flask import url_for,current_app
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,timedelta
class PaginatedAPIMixin(object):
    #（？）staticmethod是什么？ +
    #   答案：定义@staticmethod，可以不用实例化类，直接调用，比如：
    #       PaginatedAPIMixin.to_collection_dict()
    @staticmethod
    def to_collection_dict(query,page,per_page,endpoint,**kwargs):
        #（？）paginate是什么？ +
        #   答：获取全部数据的分页，详情请见flask-sqlalchemy文档
        #       返回的是一个Paginate对象
        resources = query.paginate(page,per_page,False)
        #（？）这里为什么可以调用子类的方法？ +
        #   答：resources是从子类来的，因此可以调用
        data={
            'items':[item.to_dict() for item in resources.items],
            '_meta':{
                'page':page, #当前页码
                'per_page':per_page,
                'total_pages':resources.pages,
                'total_items':resources.total
            },
            '_links':{
                'self':url_for(endpoint,page=page,per_page=per_page,**kwargs),
                'next':url_for(endpoint,page=page+1,per_page=per_page,**kwargs) \
                                if resources.has_next else None,
                'prev':url_for(endpoint,page=page-1,per_page=per_page,**kwargs) \
                                if resources.has_prev else None
            }
        }
        return data
    