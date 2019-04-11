import logging

from flask import request
from flask_restplus import Resource

from autopwn2.api import api
from autopwn2.api.business import create_setting, update_setting, delete_setting
from autopwn2.api.serializers import _setting
from autopwn2.database.models import Setting

ns = api.namespace('settings', description='Settings')

log = logging.getLogger(__name__)


@ns.route('/')
class _Settings(Resource):
    @api.marshal_list_with(_setting, envelope='data')
    def get(self):
        """List all settings"""
        return Setting.query.all()

    @api.expect(_setting, validate=False)
    @api.response(201, 'Setting successfully created.')
    def post(self):
        """Create a new Setting"""
        create_setting(request.json)
        return None, 201


@ns.route('/<int:id>')
class _Setting(Resource):
    @api.marshal_list_with(_setting)
    def get(self, id):
        """Show a setting"""
        return Setting.query.fiter(Setting.id == id).one()

    @api.expect(_setting, validate=False)
    @api.response(204, 'Setting successfully updated.')
    def put(self, id):
        """Update a setting"""
        update_setting(id, request.json)
        return None, 204

    @api.response(204, 'Setting successfully deleted.')
    def delete(self, id):
        """Delete a setting"""
        delete_setting(id)
        return None, 204
