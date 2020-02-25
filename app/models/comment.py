from app.models.base import *
comments_likes = db.Table(
    'comments_likes',
    db.Column('user_id',db.Integer,db.ForeignKey('users.id')),
    db.Column('comment_id', db.Integer, db.ForeignKey('comments.id')),
    db.Column('timestamp',db.DateTime,default=datetime.utcnow)
)
class Comment(PaginatedAPIMixin,db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    mark_read=db.Column(db.Boolean,default=False)
    disabled=db.Column(db.Boolean,default=False)
    #谁评论的？
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))
    #回复了谁？
    parent_id = db.Column(db.Integer,db.ForeignKey('comments.id',ondelete='CASCADE'))
    #（？）cascade必须定义在“多”的那一侧，db.backref()这个是用方法在文档哪里呢？ +
    # 答：初步参照Relationship Configuration - Adjacency List Relationship
    #（？）remote_side无法理解。。。 -
    #（？）这样的自引用关系无法理解！ -
    parent = db.relationship('Comment', backref=db.backref('children', cascade='all, delete-orphan'), remote_side=[id])

    likers = db.relationship(
        'User',
        #（？）报错Can't execute sync rule for source column 'comments.id'怎么办？ -
        # 神tm这里用了单引号！！！secondary='comments_likes'
        # secondaryjoin也不需要！为什么？
        secondary=comments_likes,
        #（？）查询user点赞过的comment，这里user_id怎么获得呢？ +
        # 答：自我引用才需要primaryjoin和secondaryjoin！
        # primaryjoin=(comments_likes.c.user_id == self.post.author_id)
        # secondaryjoin=(comments_likes.c.comment_id == id),
        backref=db.backref('liked_comments',lazy='dynamic')
    )


    def __repr__(self):
        return '<Comment {}>'.format(self.id)
    def get_descendants(self):
        data = set()
        def descendants(slf):
            #如果这条评论有后代
            if slf.children:
                data.update(slf.children)
            #递归后代的后代
            for child in slf.children:
                descendants(child)
        descendants(self)
        return data
    def from_dict(self,data):
        '''把接收到的json附加到对象的属性'''
        for field in ['body','timestamp','mark_read','disabled','author_id','post_id','parent_id']:
            if field in data:
                setattr(self,field,data[field])
    def to_dict(self):
        data = {
            'id':self.id,
            'body':self.body,
            'timestamp':self.timestamp,
            'disabled':self.disabled,
            'post_id':self.post_id,
            'parent_id':self.parent_id, #如果有的话就是评论的评论，否则就是顶级评论
            'post':{
                'id':self.post_id,
                'title':self.post.title
            },
            #每一个评论的用户信息，表明这条评论是谁评论的
            'author':{
                'id':self.author.id,
                'username':self.author.username,
                'name':self.author.name,
                'avatar':self.author.avatar(128)
            },
            'likers_id':self.liked_count
        }
        return data
    def is_liked_by(self,user):
        #（？）为什么followeds是可查询对象，而这里的likers则是列表？ +
        # followeds定义了dynamic，而likers没有。详见博客园文章。
        # return self.likers.filter(
        #     comments_likes.c.user_id == user.id).count()>0
        return user in self.likers


    def liked_by(self,user):
        '''user点赞了这个comment'''
        if not self.is_liked_by(user):
            self.likers.append(user)


    def unliked_by(self,user):
        '''user取消点赞这个comment'''
        if self.is_liked_by(user):
            self.likers.remove(user)
    @property
    def liked_count(self):
        return [user.id for user in self.likers]
