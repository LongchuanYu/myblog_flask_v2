
#这应该是是一个蓝图生成器...
from flask import Blueprint
bp = Blueprint('/api',__name__)

#（？）末尾加入，这里怎么避免循环导入的？
from app.api import ping,users,tokens
