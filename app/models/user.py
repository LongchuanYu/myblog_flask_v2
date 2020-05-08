from app.models.base import *
from app.models.exts import Post,Comment,comments_likes,Notification
LOGIN_EXPIRES_IN = 28800
MAIL_EXPIRES_IN = 28800
followers = db.Table(
    'followers',
    db.Column('follower_id',db.Integer,db.ForeignKey('users.id')), #我关注了谁？
    db.Column('followed_id',db.Integer,db.ForeignKey('users.id')), #我的粉丝是谁？
    db.Column('timestamp',db.DateTime,default=datetime.utcnow)
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

    last_recived_comments_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 用户的粉丝 页面的时间，用来判断哪些粉丝是新的
    last_follows_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 收到的点赞 页面的时间，用来判断哪些点赞是新的
    last_likes_read_time = db.Column(db.DateTime)
    # 用户最后一次查看私信的时间
    last_messages_read_time = db.Column(db.DateTime)

    comments = db.relationship('Comment',backref='author',lazy='dynamic',cascade='all,delete-orphan')
    posts = db.relationship('Post',backref='author',
        lazy='dynamic',cascade='all,delete-orphan')
    #（？）怎么理解参数secondary？ +
    #   答：查看文档，在多对多关系中，secondary指定中间表
    #（？）怎么理解followeds.c.follower_id? +
    #   答：这c应该是column的缩写，这里引用中间表followeds的follower_id列
    #（？）如何理解followeds和反向引用db.backref('followers')? +
    #   答：followeds:我关注了谁
    #       followers：我的粉丝是谁
    #       更多信息请阅读文档
    followeds = db.relationship(  
        'User',secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id==id),
        backref=db.backref('followers',lazy='dynamic'),
        lazy='dynamic'
    )

    notifications = db.relationship('Notification',backref='user',
        lazy='dynamic', cascade='all, delete-orphan')

    # 用户是否已确认邮箱
    confirmed = db.Column(db.Boolean, default=False)
 
    # 用户发送的私信
    # （？）relationship指定foreign_keys的意义？ +
    # 答：一般relationship会自动指定外键，但是这里和message有关的user有可能是发送者，也有可能是接收者，因此需要单独指定外键
    # 参考https://docs.sqlalchemy.org/en/13/orm/relationship_api.html#sqlalchemy.orm.relationship
    messages_sent = db.relationship(
        'Message',
        backref='sender',
        foreign_keys='Message.sender_id',
        lazy='dynamic',
        cascade='all,delete-orphan'
    )
    # 用户接受到的私信
    messages_received = db.relationship(
        'Message',
        backref='recipient',
        foreign_keys='Message.recipient_id',
        lazy='dynamic',
        cascade='all,delete-orphan'
    )
    #（？）这一段一直不理解 +
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
            #（？） 为什么要加个'z' -
            'member_since': self.member_since.isoformat() + 'Z' if self.member_since else "", 
            'last_seen': self.last_seen.isoformat() + 'Z' if self.last_seen else "",
            'posts_count':self.posts.count(),
            #（？）如何理解followed_posts_count？哪来的followed_posts？ +
            #   答：followed_posts是User类定义的一个方法，但是用property修饰了
            #       最后返回一个经过加工的属性。
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
    # data是客户端传来的json数据
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
    def get_jwt(self,expires_in=LOGIN_EXPIRES_IN):
        now = datetime.utcnow()
        payload = {
            'confirmed': self.confirmed,
            'user_id':self.id,
            'user_name':self.name if self.name else self.username,
            'user_avatar':base64.b64encode(self.avatar(24).encode('utf-8')).decode('utf-8'),
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
            # （？）这里怎么验证token过期呢？ +
            #   Expiration time is automatically verified in jwt.decode() and raises jwt.ExpiredSignatureError if the expiration time is in the past
            print(e)
            return None
        return User.query.get(payload.get('user_id'))

    def generate_confirm_jwt(self,expires_in=MAIL_EXPIRES_IN):
        now = datetime.utcnow()
        payload = {
            'confirm':self.id,
            'exp':now+timedelta(seconds=expires_in),
            'iat':now
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        ).decode('utf-8')

    def verify_confirm_jwt(self,token):
        '''验证用户是否点击邮件，通过JWT检验'''
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms='HS256'
            )
        except (jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.DecodeError) as e:
                return False
        if payload.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True


    def verify_confirm_jwt(self, token):
            '''用户点击确认邮件中的URL后，需要检验 JWT，如果检验通过，则把新添加的 confirmed 属性设为 True'''
            try:
                payload = jwt.decode(
                    token,
                    current_app.config['SECRET_KEY'],
                    algorithms=['HS256'])
            except (jwt.exceptions.ExpiredSignatureError,
                    jwt.exceptions.InvalidSignatureError,
                    jwt.exceptions.DecodeError) as e:
                # Token过期，或被人修改，那么签名验证也会失败
                return False
            if payload.get('confirm') != self.id:
                return False
            self.confirmed = True
            db.session.add(self)
            return True


    #（？）这个“avatar”是一个方法，也没有用Property装饰器修饰，如果别的地方要用到这个avatar的url怎么办？ +
    # 答：avatar只要有email地址就有一个专属的头像，所以别的地方要用的话就调用这个方法返回头像地址，怎么都不会变的
    def avatar(self,size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def is_following(self,user):
        #（？）这里如何理解？ +
        #   答：功能 -> 我是否关注了user？
        #   ....在我的关注列表(followeds)里面查找id(也就是我关注了谁followed_id)等于user.id的项目
        return self.followeds.filter(
            followers.c.followed_id == user.id).count()>0
    def follow(self,user):
        if not self.is_following(user):
            #（？）这里followeds字段是列表吗？为什么可以用append？ +
            #   答：参照SQLAlchemy文档-Working with Related Objects
            #   ....它可以是各种collection types，默认是Python List

            self.followeds.append(user)
    def unfollow(self,user):
        if self.is_following(user):
            self.followeds.remove(user)

    #（？）property装饰器的作用是什么？ +
    #   答：1.方法属性化，直接用User.followed_posts访问,最后作为一个属性返回
    #   2.只读属性，不允许直接修改。但是可以用setter装饰器修改。
    @property
    def followed_posts(self):
        '''获取当前用户的关注者的所有文章列表'''
        #（？）如何理解join里面的两个参数？ +
        #   第一个参数指定表，第二个参数是链接条件，相当于SQL的ON
        #   详见官方文档：Querying with Joins

        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.author_id)).filter(
                followers.c.follower_id == self.id)
        # 包含当前用户自己的文章列表
        # own = Post.query.filter_by(user_id=self.id)
        # return followed.union(own).order_by(Post.timestamp.desc())
        return followed.order_by(Post.timestamp.desc())
#-------------------------------------------------------------------通知类
    def new_recived_comments(self):
        '''当前用户发布的文章下新评论总数'''
        #用户发表的所有文章id
        user_posts_ids = [post.id for post in self.posts]
        #用户发表的所有评论id
        user_comment_ids = [comment.id for comment in self.comments]
        last_read_time = self.last_recived_comments_read_time or datetime(1990,1,1)
        # （？）如何查询字段为空的记录？ +
        # 答：详见官网，query.filter(User.name == None) 或者 query.filter(User.name.is_(None))

        # 这里查询用户文章下的所有评论和所有回复我的。
        recived_comment_count = Comment.query.filter(
            Comment.post_id.in_(user_posts_ids) , 
            Comment.parent_id == None,
            Comment.timestamp > last_read_time
        ).count()
        recived_reply_count = Comment.query.filter(
            Comment.parent_id.in_(user_comment_ids),
            Comment.timestamp > last_read_time
        ).count()
        return recived_comment_count + recived_reply_count
    def new_follows(self):
        '''获取新粉丝总数'''
        last_read_time = self.last_follows_read_time or datetime(1990,1,1)
        # （？）这里要计算新粉丝总数，但是User类里面没有时间标签，怎么解决？ +
        # 答：User类里面没有，中间表里面有啊
        return self.followers.filter(
            followers.c.timestamp > last_read_time
        ).count()

    def new_likes_count(self):
        '''获取新点赞总数'''
        last_read_time = self.last_likes_read_time or datetime(1990,1,1)
        # 找到用户所有评论->筛选出被点赞的评论
        c = self.comments.join(
            comments_likes,
            comments_likes.c.comment_id==Comment.id
        ).filter(comments_likes.c.timestamp>last_read_time).count()
        return c
    def add_notification(self,name,data):
        '''
        name：通知类型
        data：通知内容
        '''
        self.notifications.filter_by(name=name).delete()
        #新增一个通知
        n = Notification(name=name,payload_json=json.dumps(data),user=self)
        db.session.add(n)
        #（？）新增通知后应该返回什么？
        return n
