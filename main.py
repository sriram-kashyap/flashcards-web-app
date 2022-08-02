from flask import Flask
from database import db, DB_NAME
from os import path
from flask_login import LoginManager, login_manager
from flask_restful import Api
from flask_caching import Cache
import workers
config = {
    "DEBUG": True,         
    "CACHE_TYPE": "SimpleCache",  
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CELERY_BROKER_URL": "redis://localhost:6379/1",
    "CELERY_RESULT_BACKEND" : "redis://localhost:6379/2"

}



celery= None

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(config)
    app.config['SECRET_KEY']='kashyap'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    cache = Cache(app)
    db.init_app(app)
    api = Api(app)

    from api import UserAPI, DeckAPI, CardAPI, ExportAPI

    api.add_resource(UserAPI, '/api/user', '/api/user/<string:username>')
    api.add_resource(DeckAPI, '/api/deck/<string:username>')
    api.add_resource(CardAPI, '/api/<string:username>/<string:deck>/card', '/api/card/<string:card_id>','/api/<string:deck>')
    api.add_resource(ExportAPI, '/api/<string:deck>/cards' )

    from views import views

    app.register_blueprint(views, url_prefix="/")

    from models import User, Deck, Card

    create_db(app)

    login_manager = LoginManager()
    login_manager.login_view = "views.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    celery = workers.celery
    #update with config
    celery.conf.update(
        broker_url = app.config["CELERY_BROKER_URL"],
        result_backend = app.config["CELERY_RESULT_BACKEND"]
    )
        
    celery.Task = workers.ContextTask

    app.app_context().push()
    return  app, api, celery
  

def create_db(app):
    if not path.exists("Flashcards/"+ DB_NAME):
        db.create_all(app=app)

