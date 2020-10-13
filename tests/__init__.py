# -*- coding: utf-8
from config import Config
class TestConfig(Config):
    #这里继承了全局配置文件
    TESTING=True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'