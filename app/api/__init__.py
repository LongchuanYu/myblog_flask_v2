
#这应该是是一个蓝图生成器...
from flask import Blueprint
bp = Blueprint('api',__name__)

from app.api import ping
