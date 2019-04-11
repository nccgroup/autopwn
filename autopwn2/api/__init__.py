import logging
import traceback

from flask_restplus import Api
from sqlalchemy.orm.exc import NoResultFound

from autopwn2 import settings

log = logging.getLogger(__name__)

api = Api(title='AutoPwn, the server',
          version='1.0',
          description='rest services for AutoPwn')


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not settings.FLASK_DEBUG:
        return {'message': message}, 500


@api.errorhandler(NoResultFound)
def database_not_found_error_handler(e):
    log.warning(traceback.format_exc())
    return {'message': 'A database result was required but none was found.'}, 404


def get_or_model(key, data, model):
    if key in data:
        return data[key]
    else:
        return model.__dict__[key]
