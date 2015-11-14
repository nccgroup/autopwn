#!/usr/bin/env python3

import json
import os
import sqlite3
import sys
import threading

from collections import OrderedDict, defaultdict
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from time import gmtime, strftime
from locale import getlocale
from subprocess import Popen, PIPE

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
# for /tools
parser.add_argument('search')
# for /jobs
parser.add_argument('job')
parser.add_argument('tool')
parser.add_argument('target')
parser.add_argument('target_name')
parser.add_argument('protocol')
parser.add_argument('port_number')
parser.add_argument('user')
parser.add_argument('password')
parser.add_argument('user_file')
parser.add_argument('password_file')

class RunThreads (threading.Thread):
    def __init__(self, tool, job):
        threading.Thread.__init__(self)
        self.tool_stdout = ''
        self.tool_sterr = ''
        self.tool = tool
        self.job = job

    def execute_tool(self):
        # Always check any tools provided by
        # community members
        print("Running")
        proc = Popen(self.tool['execute_string'], stdout=PIPE, stderr=PIPE, shell=True)

        decode_locale = lambda s: s.decode(getlocale()[1])
        self.tool_stdout, self.tool_stderr = map(decode_locale, proc.communicate())

        # Callback / pause from here
        return_code = proc.returncode

        # Update completed and return_code field in db
        con = sqlite3.connect('assets.db')
        cur = con.cursor()
        cur.execute("UPDATE jobs SET executed = 1, return_code = ? WHERE id = ?",(str(return_code),str(self.job['id'])))
        con.commit()

        # Close connection
        if con:
            con.close()

    def run(self):
        self.execute_tool()

class Pong(Resource):
    def get(self):
        return { 'message':'pong' }

class Tools(Resource):
    # Get tools
    def get(self):
        args = parser.parse_args()
        con = sqlite3.connect('assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # If /tools?search=xxx not specified then SELECT *
        if args['search'] != None:
            cur.execute("SELECT * FROM tools WHERE name LIKE ? OR description LIKE ?",('%' + args['search'] + '%','%' + args['search'] + '%'))
        else:
            cur.execute("SELECT * FROM tools")
        data = dict(result=[dict(r) for r in cur.fetchall()])

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
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # If /jobs?search=xxx not specified then SELECT *
        if args['search'] != None:
           cur.execute("SELECT * FROM jobs WHERE tool LIKE ? OR target LIKE ? OR target_name LIKE ? OR protocol LIKE ? OR port_number LIKE ? OR user like ? OR password LIKE ? OR user_file LIKE ? OR password_file LIKE ?",('%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%'))
        else:
           cur.execute("SELECT * FROM jobs")
        data = dict(result=[dict(r) for r in cur.fetchall()])

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
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM jobs WHERE id = ?",(job_id,))
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

# Execute job
class JobsIdExecute(Resource):
    def post(self):
        # Process placeholders
        tool = {}
        job = {}
        args = parser.parse_args()
        con = sqlite3.connect('assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Get job id columns
        cur.execute("SELECT * FROM jobs WHERE id = ?",(args['job'],))
        job_data = dict(result=[dict(r) for r in cur.fetchall()])

        # Index is now tied to database schema, yuck
        job = job_data['result'][0]
        job['date'] = strftime("%Y%m%d_%H%M%S%z")
        job['output_dir'] = os.getcwd() + '/' + strftime("%Y%m%d") + \
                                "_autopwn_" + \
                                job_data['result'][0]['target_name']

        tool['id'] = job['tool']
        # Get dependencies
        cur.execute("SELECT dependency from dependencies WHERE tool = ?",(tool['id'],))
        dependency = dict(result=[dict(r) for r in cur.fetchall()])

        # Get tool execute string
        cur.execute("SELECT * FROM tools WHERE id = ?",(tool['id'],))
        tool_data = dict(result=[dict(r) for r in cur.fetchall()])
        tool = tool_data['result'][0]

        # Close connection
        if con:
            con.close()

        ddict_options = defaultdict(lambda:'')
        for option in job:
            ddict_options[option] = job[option]

        tool['execute_string'] = tool['execute_string'].format(**ddict_options)
        print(tool['execute_string'])

        thread = []
        # Tool string generated, execute
        thread.append(RunThreads(tool,job))
        # If main process dies, everything else *SHOULD* as well
        thread[-1].daemon = True
        # Start threads
        thread[-1].start()

        return {'message':'Job Id to be executed here'}, 201

class Dependencies(Resource):
    def get(self):
        con = sqlite3.connect('assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM dependency_names")
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

class Options(Resource):
    def get(self):
        con = sqlite3.connect('assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM options")
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

# Retrieve options for tool
class OptionsId(Resource):
    def get(self, tool_id):
        con = sqlite3.connect('assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT option FROM tool_options WHERE tool = ?",(tool_id,))
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

# Retrieve dependencies for tool
class DependenciesId(Resource):
    def get(self, tool_id):
        con = sqlite3.connect('assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT dependency FROM dependencies WHERE tool = ?",(tool_id,))
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

# Pong!
# curl -i http://127.0.0.1:5000/ping
api.add_resource(Pong, '/ping')
# Fetch all tools
# curl -i http://127.0.0.1:5000/tools
api.add_resource(Tools, '/tools')
# Fetch all jobs
# curl -i http://127.0.0.1:5000/jobs
api.add_resource(Jobs, '/jobs')
# Fetch job id
# curl -i http://127.0.0.1:5000/jobs/1
api.add_resource(JobsId, '/jobs/<job_id>')
# Execute job id
# curl -i --data "job=1" http://127.0.0.1:5000/jobs/execute
api.add_resource(JobsIdExecute, '/jobs/execute')
# Fetch all dependencies
# curl -i http://127.0.0.1:5000/dependencies
api.add_resource(Dependencies, '/dependencies')
# Fetch all dependencies for tool id
api.add_resource(DependenciesId, '/dependencies/<tool_id>')
# Fetch all options
# curl -i http://127.0.0.1:5000/options
api.add_resource(Options, '/options')
# Fetch all options for tool id
# curl -i http://127.0.0.1:5000/options/1
api.add_resource(OptionsId, '/options/<tool_id>')

if __name__ == '__main__':
    app.run(debug=True)
