import logging

from flask import request
from flask_restplus import Resource

from autopwn2.api import api
from autopwn2.api.business import create_tool, update_tool, delete_tool
from autopwn2.api.serializers import _tool
from autopwn2.database.models import Tool

ns = api.namespace('tools', description='Tools')

log = logging.getLogger(__name__)


@ns.route('/')
class _Tools(Resource):
    @api.marshal_list_with(_tool, envelope='data')
    def get(self):
        """List all tools"""
        return Tool.query.all()

    @api.expect(_tool, validate=False)
    @api.response(201, 'Tool successfully created.')
    def post(self):
        """Create a new Tool"""
        create_tool(request.json)
        return None, 201


@ns.route('/<int:id>')
class _Tool(Resource):
    @api.marshal_list_with(_tool)
    def get(self, id):
        """Show a tool"""
        return Tool.query.fiter(Tool.id == id).one()

    @api.expect(_tool, validate=False)
    @api.response(204, 'Tool successfully updated.')
    def put(self, id):
        """Update a tool"""
        update_tool(id, request.json)
        return None, 204

    @api.response(204, 'Tool successfully deleted.')
    def delete(self, id):
        """Delete a tool"""
        delete_tool(id)
        return None, 204
