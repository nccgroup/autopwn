import logging

from flask import request
from flask_restplus import Resource

from autopwn2.api import api
from autopwn2.api.business import create_job, update_job, delete_job, start_job
from autopwn2.api.serializers import _job
from autopwn2.database.models import Job

ns = api.namespace('jobs', description='Jobs')

log = logging.getLogger(__name__)


@ns.route('/')
class _Jobs(Resource):
    @api.marshal_list_with(_job, envelope='data')
    def get(self):
        """List all jobs"""
        return Job.query.all()

    @api.expect(_job, validate=False)
    @api.response(201, 'Job successfully created.')
    def post(self):
        """Create a new Job"""
        create_job(request.json)
        return None, 201


@ns.route('/<int:id>')
class _Job(Resource):
    @api.marshal_list_with(_job)
    def get(self, id):
        """Show a job"""
        return Job.query.fiter(Job.id == id).one()

    @api.expect(_job, validate=False)
    @api.response(204, 'Job successfully updated.')
    def put(self, id):
        """Update a job"""
        update_job(id, request.json)
        return None, 204

    @api.response(204, 'Job successfully deleted.')
    def delete(self, id):
        """Delete a job"""
        delete_job(id)
        return None, 204


@ns.route('/<int:id>/execute')
class _Execute(Resource):
    def post(self, id):
        start_job(id)
        return None, 202
