from datetime import timedelta
import secrets
import sys
import json
from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS
from flask_praetorian import Praetorian
from flask_migrate import Migrate
from celery import Celery
import redis

from server.models import db, users

ACCESS_EXPIRES = timedelta(minutes=10)
argv = sys.argv[1:]


guard = Praetorian()

redis_store = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)

def check_token_blacklisted(jti):
    token_in_redis = redis_store.get(jti)
    if token_in_redis is None:
        return False
    return True


def create_flask_app(config={}, script_info=None):

    _debug = True if "--debug" in argv else False
    # instantiate the app
    app = Flask(
        __name__,
        template_folder="../build/templates",
        static_folder="../build/static",
    )

    # import blueprints
    from server.routes.views import main_blueprint
    from server.routes.apiv1 import apiv1_blueprint
    from server.routes.apiv2 import apiv2_blueprint
    from server.routes.user_management import user_manager_blueprint

    app.logger.addHandler(default_handler)

    # set config
    if _debug:
        app.config.from_file("config.dev.json", load=json.load)
        CORS(apiv1_blueprint)
    elif len(config) > 0:
        app.config.from_mapping(config)
    else:
        app.config.from_file("config.json", load=json.load)
    if app.config.get("JWT_SECRET_KEY", "") == "":
        app.config["JWT_SECRET_KEY"] = str(secrets.SystemRandom())
    if app.config.get("SECRET_KEY", "") == "":
        app.config["SECRET_KEY"] = str(secrets.SystemRandom())

    # Initialize DB after loading config
    db.init_app(app)

    # Initialize the flask-praetorian instance for the app
    guard.init_app(app, user_class=users.User, is_blacklisted=check_token_blacklisted)

    # Flask migrate
    Migrate(app, db)

    # register blueprints
    if not app.config.get("HEADLESS", False):
        app.register_blueprint(main_blueprint)
    app.register_blueprint(apiv1_blueprint)
    app.register_blueprint(apiv2_blueprint)
    app.register_blueprint(user_manager_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})
    return app

def create_celery_app(options:str=""):
    # Initialize celery
    options = options.split(" ")
    celery_app = Celery(__name__)
    
    # Load the config
    config = {}
    if ("--debug" in options or "DEBUG" in options):
        with open("server/config.dev.json") as fh:
            config = json.load(fh)
    else:
        with open("server/config.json") as fh:
            config = json.load(fh)

    # Select the celery section
    config = config["CELERY"]

    # loop trough the items and set the values manually
    for item in config:
        celery_app.conf[item] = config.get(item)

    return celery_app
