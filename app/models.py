from app import db
from flask import url_for
from werkzeug.security import generate_password_hash,check_password_hash
class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    #index为索引字段
    username = db.Column(db.String(64),index=True,unique=True)
    email = db.Column(db.String(120),index=True,unique=True)
    password_hash=db.Column(db.String(128))
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
                'self': url_for('api.get_user', id=self.id)
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
                setattr(self,field,data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])
