from app.models.base import *
class Notification(db.Model):  # 不需要分页
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    #消息类型
    name = db.Column(db.String(128), index=True)
    #消息所在的用户id
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ##
    # user relationship：消息所在的用户对象
    ##
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def __repr__(self):
        return "<Notification {}>".format(self.id)
    def to_dict(self):
        data = {
            'id':self.id,
            'name':self.name,
            'user':{
                'id':self.user_id,
                'username':self.user.username,
            },
            'timestamp':self.timestamp,
            'payload_json':json.loads(str(self.payload_json))
        }
        return data
    def from_dict(self):
        pass
