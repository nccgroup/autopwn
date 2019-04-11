from flask_restplus import fields

from autopwn2.api import api

_setting = api.model('setting', {
    'id': fields.Integer(required=False, description=''),
    'name': fields.String(required=True, description=''),
    'value': fields.String(required=True, description=''),
    'example': fields.String(required=False, description='')
})

_tool = api.model('tool', {
    'id': fields.Integer(required=False, description=''),
    'description': fields.String(required=False, description=''),
    'command': fields.String(required=True, description=''),
    'name': fields.String(required=True, description=''),
    'stdout': fields.Integer(required=True, description=''),
    'url': fields.String(description='')
})

_job = api.model('jobs', {
    'id': fields.Integer(required=False, description=''),
    'tool_id': fields.Integer(required=True, description='', attribute='tool.id'),
    'command': fields.String(required=True, description=''),
    'startTime': fields.DateTime(required=False, description=''),
    'endTime': fields.DateTime(required=False, description=''),
    'return_code': fields.Integer(required=False, description='')
})

_assessment = api.model('assessment', {
    'id': fields.Integer(required=False, description=''),
    'name': fields.String(required=True, description=''),
    'description': fields.String(required=True, description=''),
    'tool': fields.List(fields.Integer(attribute='id'), description='', required=False, attribute='tools')
})