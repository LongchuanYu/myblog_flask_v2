import base64,os,jwt
from app import db
from flask import url_for,current_app
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,timedelta

class PaginatedAPIMixin(object):
    #定义@staticmethod，可以不用实例化类，直接调用，比如：
    #   PaginatedAPIMixin.to_collection_dict()
    @staticmethod
    def to_collection_dict(query,page,per_page,endpoint,**kwargs):
        #获取全部数据的分页，详情请见flask-sqlalchemy文档
        #   返回的是一个Paginate对象
        resources = query.paginate(page,per_page,False)
        #（？）这里为什么可以调用子类的方法？
        #   resources是从子类来的，因此可以调用
        data={
            'items':[item.to_dict() for item in resources.items],
            '_meta':{
                'page':page,
                'per_page':per_page,
                'total_pages':resources.pages,
                'total_tiems':resources.total
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
    

class User(PaginatedAPIMixin, db.Model):
    id = db.Column(db.Integer,primary_key=True)
    #index为索引字段
    username = db.Column(db.String(64),index=True,unique=True)
    email = db.Column(db.String(120),index=True,unique=True)
    password_hash=db.Column(db.String(128))
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    
    
    # 改用jwt来实现token
    # token = db.Column(db.String(32),index=True,unique=True)
    # token_expiration=db.Column(db.DateTime)

    #（？）这一段一致不理解
    def __repr__(self):
        return '<User {}>'.format(self.username)
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
    def to_dict(self,include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            '_links': {
                'self': url_for('/api.get_user', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data
    #data是客户端传来的json数据
    def from_dict(self,data,new_user=False):
        for field in ['username','email']:
            if field in data:
                #self指的是类实例对象本身
                #   说到底，字段也就是定义的类里面的属性
                #   因此这里可以把字段添加到实例的属性里面去
                #   通过db.session.add(something)来添加到session里面
                setattr(self,field,data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
    def get_jwt(self,expires_in=10):
        now = datetime.utcnow()
        payload = {
            'user_id':self.id,
            'name':self.name if self.name else self.username,
            'exp':now+timedelta(seconds=expires_in),
            'iat':now
        }
        return jwt.encode(
            payload,current_app.config['SECRET_KEY'],algorithm="HS256"
        ).decode('utf-8')

    @staticmethod
    def verify_jwt(token):
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256'])
        except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.InvalidSignatureError) as e:
            # （？）这里怎么验证token过期呢？
            #   Expiration time is automatically verified in jwt.decode() and raises jwt.ExpiredSignatureError if the expiration time is in the past
            return None
        return User.query.get(payload.get('user_id'))









'''
# 改用jwt来实现token
def get_token(self,expires_in=3600):
    now = datetime.utcnow()
    #（？），这里怎么理解过期时间>now+60s ?
    if self.token and self.token_expiration > now + timedelta(seconds=60):
        return self.token

    #b64decode后的是二进制，需要decode成字符串
    self.token = base64.b64encode(os.urandom(24)).decode('utf-8')

    self.token_expiration = now + timedelta(seconds=expires_in)
    


    #（？），这里把self添加到session，但是没有commit，为什么？
    #   1.self指User类的实例
    #   2.
    db.session.add(self)
    return self.token
def revoke_token(self):
    #（？）撤回token的原理是什么？为什么要减掉1秒？
    #   卧槽，我傻了。这里是把到期时间（token_expiration）设置为当前时间的前一秒
    #   也就是设置为过去，当然就过期了啊！！
    self.token_expiration=datetime.utcnow() - timedelta(seconds=1)


@staticmethod
def check_token(token):
    user = User.query.filter_by(token=token).first()
    if user is None or user.token_expiration<datetime.utcnow():
        return None
    return user

'''