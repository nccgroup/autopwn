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
# for /jobs
parser.add_argument('tool')
parser.add_argument('target')
parser.add_argument('target_name')
parser.add_argument('protocol')
parser.add_argument('port_number')
parser.add_argument('user')
parser.add_argument('password')
parser.add_argument('user_file')
parser.add_argument('password_file')


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
        return data

    # Submit a new tool
    def post(self):
        args = parser.parse_args()
        return args

class Jobs(Resource):
    # List jobs
    def get (self):
        args = parser.parse_args()
        con = sqlite3.connect('assets.db')
        cur = con.cursor()

        # If /jobs?search=xxx not specified then SELECT *
        if args['search'] != None:
           cur.execute("SELECT * FROM jobs WHERE tool LIKE ? OR target LIKE ? OR target_name LIKE ? OR protocol LIKE ? OR port_number LIKE ? OR user like ? OR password LIKE ? OR user_file LIKE ? OR password_file LIKE ?",('%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%'))
        else:
           cur.execute("SELECT * FROM tools")
        data = cur.fetchall()

        # Close connection
        if con:
            con.close()
        return data

    # Submit new job
    def post(self):
        args = parser.parse_args()
        con = sqlite3.connect('assets.db')
        cur = con.cursor()

        # curl -i --data "tool=1&target=localhost&target_name=target_name&protocol=https&port_number=1337&user=a_user&password=a_password&user_file=/user/file&password_file=/password/file" http://127.0.0.1:5000/jobs
        cur.execute("INSERT INTO jobs(tool,target,target_name,protocol,port_number,user,password,user_file,password_file) VALUES(?,?,?,?,?,?,?,?,?)",(args['tool'],args['target'],args['target_name'],args['protocol'],args['port_number'],args['user'],args['password'],args['user_file'],args['password_file']))
        data = cur.lastrowid
        con.commit()

        # Close connection
        if con:
            con.close()
        return { 'id':data }, 201

# List individual jobs
class JobsId(Resource):
    def get(self, job_id):
        con = sqlite3.connect('assets.db')
        cur = con.cursor()

        cur.execute("SELECT * FROM jobs WHERE id = ?",(job_id))
        data = cur.fetchall()

        # Close connection
        if con:
            con.close()
        return data

# Execute job
class JobsIdExecute(Resource):
    def get(self, job_id):
       return {'message':'Job Id to be executed here'}

class Dependencies(Resource):
    def get(self):
        con = sqlite3.connect('assets.db')
        cur = con.cursor()

        cur.execute("SELECT * FROM dependency_names")
        data = cur.fetchall()

        # Close connection
        if con:
            con.close()
        return data

# Retrieve dependencies for tool
class DependenciesId(Resource):
    def get(self, tool_id):
        con = sqlite3.connect('assets.db')
        cur = con.cursor()

        cur.execute("SELECT dependency FROM dependencies WHERE tool = ?",(tool_id))
        data = cur.fetchall()

        # Close connection
        if con:
            con.close()
        return data

# Fetch all tools
api.add_resource(Tools, '/tools')
# Fetch all jobs
api.add_resource(Jobs, '/jobs')
# Fetch job id
api.add_resource(JobsId, '/jobs/<job_id>')
# Execute job id
api.add_resource(JobsIdExecute, '/jobs/<job_id>/execute')
# Fetch all dependencies
api.add_resource(Dependencies, '/dependencies')
# Fetch all dependencies for tool id
api.add_resource(DependenciesId, '/dependencies/<tool_id>')

if __name__ == '__main__':
    app.run(debug=True)
