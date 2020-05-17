from app.models.base import *

class Task(PaginatedAPIMixin, db.Model):
    __tablename__ = 'tasks'
    # 不使用默认的整数主键，而是用 RQ 为每个任务生成的字符串ID
    id = db.Column(db.String(36), primary_key=True)
    # 任务名
    name = db.Column(db.String(128), index=True)
    # 任务描述
    description = db.Column(db.String(128))
    # 任务所属的用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 是否已执行完成
    complete = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Task {}>'.format(self.id)