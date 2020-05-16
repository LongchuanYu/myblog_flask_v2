from app.models.base import *

class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE = 0x04
    ADMIN = 0x80


class Role(PaginatedAPIMixin,db.Model):
    __tablename__='roles'
    id = db.Column(db.Integer,primary_key=True)


    slug = db.Column(db.String(255),unique=True)

    # 角色名称：读者、作者、管理者...
    name = db.Column(db.String(255))

    # 是否为默认角色：默认角色是'reader'
    default = db.Column(db.Boolean,default=False,index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User',backref='role',lazy='dynamic')

    def __init__(self,**kwargs):
        # （？）调用父类的__init__，传入子类的参数？ -
        super(Role,self).__init__(**kwargs)
        if self.permissions is None:
            # 初始没有任何权限：0b00000000
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'shutup': ('小黑屋', ()),
            'reader': ('读者', (Permission.FOLLOW, Permission.COMMENT)),
            'author': ('作者', (Permission.FOLLOW, Permission.COMMENT, Permission.WRITE)),
            'administrator': ('管理员', (Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.ADMIN)),
        }
        default_role = 'reader'

        # 扫描角色：'shutup','reader','author','administrator'
        for r in roles:
            role = Role.query.filter_by(slug=r).first()
            if role is None:
                # （？）如果数据库里面没有这个角色，就新加一个 +
                role = Role(slug=r, name=roles[r][0])
            role.reset_permissions()
            for perm in roles[r][1]:
                role.add_permission(perm)
            role.default = (role.slug == default_role)
            db.session.add(role)
        db.session.commit()

    def get_permissions(self):
        '''获取角色的具体操作权限列表'''
        p = [(Permission.FOLLOW, 'follow'), (Permission.COMMENT, 'comment'), (Permission.WRITE, 'write'), (Permission.ADMIN, 'admin')]
        # 过滤掉没有权限，注意不能用 for 循环，因为遍历列表时删除元素可能结果并不是你想要的，参考: https://segmentfault.com/a/1190000007214571
        new_p = filter(lambda x: self.has_permission(x[0]), p)
        return ','.join([x[1] for x in new_p])  # 用逗号拼接成str


    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        # （？）判断是否有权限的算法逻辑？ +
        # 答：假设现有权限self.permissions = 0000 1111
        #     需要验证：perm = 0000 0011是否在已有权限中
        #     则：
        #     self.permissions & perm  
        #      = 0000 1111 & 0000 0011
        #      = 0000 0011
        #      = perm
        #      可见perm已经在权限中了
        return self.permissions & perm   ==   perm

    def add_permission(self, perm):
        #（？）增加权限的算法逻辑？ -
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Role {}>'.format(self.name)


