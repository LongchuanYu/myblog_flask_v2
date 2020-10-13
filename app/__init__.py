# -*- coding: utf-8
# -*- coding:utf8 -*- 
from flask import Flask
from config import Config
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

from redis import Redis
import rq


mail = Mail()
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # 不检查路由中最后是否有斜杠/
    app.url_map.strict_slashes = False

    CORS(app)
    db.init_app(app)
    migrate.init_app(app,db)
    mail.init_app(app)


    # 整合RQ任务队列
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('myblog-tasks', connection=app.redis, default_timeout=3600)  # 设置任务队列中各任务的执行最大超时时间为 1 小时
    

    from app.api import bp as api_bp
    app.register_blueprint(api_bp,url_prefix='/api')

    return app

#（？）为什么加到文件末尾呢？
from app import models
