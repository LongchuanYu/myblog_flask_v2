from app.models.base import *
class Message(PaginatedAPIMixin,db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer,primary_key=True)
    # 消息体
    body = db.Column(db.Text)
    # 时间戳
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    # 谁发的
    sender_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    # 发给了谁
    recipient_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    def __repr__(self):
        return '<Message {}>'.format(self.id)
    def to_dict(self):
        data = {
            'id':self.id,
            'body':self.body,
            'timestamp':self.timestamp,
            'sender':self.sender_id,
            'recipient':self.recipient_id,
            '_links':{
                
            }
        }
        return data
    def from_dict(self,data):
        for field in ['body','timesatmp']:
            if field in data:
                setattr(self,field,data[field])
        
