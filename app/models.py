import base64,os,jwt
from app import db
from hashlib import md5
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
    
followers = db.Table(
    'followers',
    db.Column('follower_id',db.Integer,db.ForeignKey('users.id')), #我关注了谁？
    db.Column('followed_id',db.Integer,db.ForeignKey('users.id')), #我的粉丝是谁？
    db.Column('timestamp',db.Integer,default=datetime.utcnow)
)

class User(PaginatedAPIMixin, db.Model):
    __tablename__ = "users"
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
    
    posts = db.relationship('Post',backref='author',
        lazy='dynamic',cascade='all,delete-orphan')
    #（？）怎么理解参数secondary？
    #   答：查看文档，在多对多关系中，secondary指定中间表
    #（？）怎么理解followeds.c.follower_id?
    #   答：这c应该是column的缩写，这里引用中间表followeds的follower_id列
    #（？）如何理解followeds和反向引用db.backref('followers')?
    #   答：followeds:我关注了谁
    #       followers：我的粉丝是谁
    #（？）思考，这里用sql如何实现呢？
    followeds = db.relationship(  
        'User',secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id==id),
        backref=db.backref('followers',lazy='dynamic'),
        lazy='dynamic'
    )
    # 改用jwt来实现token
    # token = db.Column(db.String(32),index=True,unique=True)
    # token_expiration=db.Column(db.DateTime)

    #（？）这一段一致不理解+
    #   打印User对象的时候返回，比如print(User()) -> <User ly1>
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
            'name': self.name,
            'location': self.location,
            'about_me': self.about_me,
            #（？） 为什么要加个'z'
            'member_since': self.member_since.isoformat() + 'Z' if self.member_since else "", 
            'last_seen': self.last_seen.isoformat() + 'Z' if self.last_seen else "",
            'posts_count':self.posts.count(),
            #（？）如何理解followed_posts_count？哪来的followed_posts？ -
            'followed_posts_count':self.followed_posts.count(),
            'followeds_count':self.followeds.count(),
            'followers_count':self.followers.count(),
            '_links': {
                'self': url_for('/api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data
    #data是客户端传来的json数据
    def from_dict(self,data,new_user=False):
        for field in ['username','email', 'name', 'location', 'about_me']:
            if field in data:
                #self指的是类实例对象本身
                #   说到底，字段也就是定义的类里面的属性
                #   因此这里可以把字段添加到实例的属性里面去
                #   通过db.session.add(something)来添加到session里面
                #   ....或者直接commit()
                setattr(self,field,data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
    def get_jwt(self,expires_in=9000):
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
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
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
            print(e)
            return None
        return User.query.get(payload.get('user_id'))
    

    def avatar(self,size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def is_following(self,user):
        #（？）这里如何理解？+
        #   答：功能 -> 我是否关注了user？
        #   ....在我的关注列表(也就是中间表followers)里面查找id(也就是我关注了谁followed_id)等于user.id的项目
        return self.followeds.filter(
            followers.c.followed_id == user.id).count()>0
    def follow(self,user):
        if not self.is_following(user):
            #（？）这里followeds字段是列表吗？为什么可以用append？-
            #   答：参照SQLAlchemy文档-Working with Related Objects
            #   ....它可以是各种collection types，默认是Python List
            self.followeds.append(user)
    def unfollow(self,user):
        if self.is_following(user):
            self.followeds.remove(user)

    #（？）property装饰器的作用是什么？ -
    @property
    def followed_posts(self):
        '''获取当前用户的关注者的所有文章列表'''
        #（？）如何理解join里面的两个参数？-
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.author_id)).filter(
                followers.c.follower_id == self.id)
        # 包含当前用户自己的文章列表
        # own = Post.query.filter_by(user_id=self.id)
        # return followed.union(own).order_by(Post.timestamp.desc())
        return followed.order_by(Post.timestamp.desc())



class Post(PaginatedAPIMixin,db.Model):
    __tablename__='posts'
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(255))
    body =db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    summary = db.Column(db.Text)
    views = db.Column(db.Integer,default=0)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))


    def __repr__(self):
        return '<Post {}>'.format(self.title)

    def from_dict(self,data):
        for field in ['title','body','summary',"author_id"]:
            if field in data:
                setattr(self,field,data[field])
    def to_dict(self):
        data={
            'id':self.id,
            'title':self.title,
            'body':self.body,
            'timestamp':self.timestamp,
            'summary':self.summary,
            'views':self.views,
            'author':self.author.to_dict(),
            "_links":{
                'self':url_for('/api.get_post',id=self.id),
                'author_url':url_for('/api.get_user',id=self.author_id)
            }
        }
        return data


























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