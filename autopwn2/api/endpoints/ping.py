from flask_restplus import Resource, reqparse

from autopwn2.api import api

parser = reqparse.RequestParser()


@api.route('/ping')
class Ping(Resource):
    @api.param('message', 'Testing message')
    def get(self):
        parser.add_argument('message')
        args = parser.parse_args()
        message = args['message']
        if message is None:
            return {'message': 'pong'}
        else:
            return {'message': ' received message [%s]' % message}
