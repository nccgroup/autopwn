import logging.config

import os
from flask import Flask, Blueprint

from autopwn2 import settings
from autopwn2.api import api
from autopwn2.database import db
from autopwn2.schedule import init_schedule
import autopwn2.api.endpoints.ping
from autopwn2.api.endpoints.settings import ns as settings_ns
from autopwn2.api.endpoints.tools import ns as tools_ns
from autopwn2.api.endpoints.jobs import ns as jobs_ns

app = Flask(__name__)
logging_conf_path = os.path.normpath(os.path.join(os.path.dirname(__file__), 'logging.conf'))
logging.config.fileConfig(logging_conf_path)
log = logging.getLogger(__name__)

basedir = os.path.join(os.path.expanduser("~"), '.autopwn')
if not os.path.exists(basedir):
    os.mkdir(basedir)


def configure_app(flask_app, sqlalchemy_database_uri):
    flask_app.config['SERVER_NAME'] = settings.FLASK_SERVER_NAME
    flask_app.config['sqlalchemy_database_uri'] = sqlalchemy_database_uri
    # flask_app.config['sqlalchemy_database_uri'] = settings.SQLALCHEMY_DATABASE_URI
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP


def initialize_app(flask_app, sqlalchemy_database_uri):
    configure_app(flask_app, sqlalchemy_database_uri)

    blueprint = Blueprint('api', __name__)
    api.init_app(blueprint)
    api.add_namespace(settings_ns)
    api.add_namespace(tools_ns)
    api.add_namespace(jobs_ns)
    flask_app.register_blueprint(blueprint)

    init_schedule(app)

    db.init_app(flask_app)


def main(sqlalchemy_database_uri='sqlite:///' + os.path.join(basedir, 'autopwn.db')):
    initialize_app(app, sqlalchemy_database_uri)
    try:
        from autopwn2.database.models import Setting
        with app.app_context():
            Setting.query.all()
    except:
        from autopwn2.database import reset_database
        with app.app_context():
            reset_database()
    log.info('>>>>> Starting AutoPwn server at http://{}/ <<<<<'.format(app.config['SERVER_NAME']))
    app.run(debug=settings.FLASK_DEBUG)


if __name__ == "__main__":
    main(sqlalchemy_database_uri=settings.SQLALCHEMY_DATABASE_URI)
