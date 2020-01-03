
#这是一个蓝图
from flask import Blueprint
bp = Blueprint('/api',__name__)

#（？）末尾加入，这里怎么避免循环导入的？
#   这是该蓝图下的所有视图。。。
from app.api import ping,users,tokens,posts,comments
