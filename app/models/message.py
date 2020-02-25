from app.models.base import *
class Message(PaginatedAPIMixin,db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    sender_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    def __repr__(self):
        return '<Message {}>'.format(self.id)
    def to_dict(self):
        data = {
            'id':self.id,
            'body':self.body,
            'timestamp':self.timestamp,
            'sender':'',
            'recipient':'',
            '_links':{
                
            }
        }
        return data
    def from_dict(self):
        pass
