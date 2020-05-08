from flask import Flask
from config import Config
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
mail = Mail()
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)


    CORS(app)
    db.init_app(app)
    migrate.init_app(app,db)
    mail.init_app(app)



    from app.api import bp as api_bp
    app.register_blueprint(api_bp,url_prefix='/api')

    return app
#（？）为什么加到文件末尾呢？
from app import models