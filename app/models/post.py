# -*- coding: utf-8
from app.models.base import *
class Post(PaginatedAPIMixin,db.Model):
    __tablename__='posts'
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(255))
    body =db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    summary = db.Column(db.Text)
    views = db.Column(db.Integer,default=0)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    
    comments = db.relationship('Comment',backref='post',lazy='dynamic',cascade='all,delete-orphan')

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
