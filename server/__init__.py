#!/usr/bin/env python3

from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
import sqlite3
import sys

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
# for /tools
parser.add_argument('search')

class Tools(Resource):
    # Get tools
    def get(self):
        args = parser.parse_args()
        con = sqlite3.connect('assets.db')
        cur = con.cursor()

        # If /tools?search=xxx not specified then SELECT *
        if args['search'] != None:
           cur.execute("SELECT * FROM tools WHERE name LIKE ? OR description LIKE ?",('%' + args['search'] + '%','%' + args['search'] + '%'))
        else:
           cur.execute("SELECT * FROM tools")
        data = cur.fetchall()

        # Close connection
        if con:
            con.close()
        print(data)
        return data

    # Submit a new tool
    def post(self):
        args = parser.parse_args()
        return args

class Jobs(Resource):
    # List jobs
    def get (self):
        return {'message':'Jobs to be listed here'}

    # Submit new job
    def post(self):
        args = parser.parse_args()
        return args

class JobsId(Resource):
    def get(self, job_id):
       return {'message':'Job Id to be listed here'}

class JobsIdExecute(Resource):
    def get(self, job_id):
       return {'message':'Job Id to be executed here'}

api.add_resource(Tools, '/tools')
api.add_resource(Jobs, '/jobs')
api.add_resource(JobsId, '/jobs/<job_id>')
api.add_resource(JobsIdExecute, '/jobs/<job_id>/execute')

if __name__ == '__main__':
    app.run(debug=True)
