#!/usr/bin/env python3

import errno
import json
import os
import shutil
#import ssl
import sqlite3
import sys
import threading

from collections import OrderedDict, defaultdict
from flask import Flask, make_response, send_file
from flask_restful import reqparse, abort, Api, Resource
from time import gmtime, strftime
from locale import getlocale
from subprocess import Popen, PIPE

# TODO
#      - TLS
app = Flask(__name__, static_url_path=os.path.dirname(os.path.abspath(__file__)))
api = Api(app)

parser = reqparse.RequestParser()
# for /tools
parser.add_argument('search')
# for /assessments/jobs and /tools/jobs
parser.add_argument('id')
parser.add_argument('assessment')
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
    def __init__(self, tool, job, context):
        threading.Thread.__init__(self)
        self.tool_stdout = ''
        self.tool_sterr = ''
        self.tool = tool
        self.job = job
        self.context = context

    def execute_tool(self, job, context):
        # Always check any tools provided by
        # community members
        print("Running")
        proc = Popen(self.tool['execute_string'], stdout=PIPE, stderr=PIPE, shell=True)

        decode_locale = lambda s: s.decode(getlocale()[1])
        self.tool_stdout, self.tool_stderr = map(decode_locale, proc.communicate())

        # Callback / pause from here
        return_code = proc.returncode
        # Zip resulting directory - This is crap because when doing assessment
        # this will be run at each tool execution.
        zip_file = os.path.dirname(os.path.abspath(__file__)) + \
            "/" + job['target_name'] + '_' + str(job['id'])
        shutil.make_archive(zip_file, 'zip', job['output_dir'])

        # Update completed and return_code field in db
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        cur = con.cursor()
        if context == 'tool':
            cur.execute("UPDATE tool_jobs SET executed = 1, return_code = ?, zip_file = ? WHERE id = ?",(str(return_code),str(zip_file),str(job['id'])))
            con.commit()
        if context == 'assessment':
            # Pull and check for 0
            cur.execute("SELECT return_code FROM assessment_jobs WHERE id = ? AND return_code == 0",(str(job['id'])))
            data = cur.fetchall()
            if len(data) == 0 or data[0][0] == 0:
                cur.execute("UPDATE assessment_jobs SET executed = 1, return_code = ?, zip_file = ? WHERE id = ?",(str(return_code),str(zip_file),str(job['id'])))
                con.commit()

        # Close connection
        if con:
            con.close()

    def run(self):
        self.execute_tool(self.job, self.context)

class Pong(Resource):
    def get(self):
        return { 'message':'pong' }

class Assessments(Resource):
    # Get assessments
    def get(self):
        args = parser.parse_args()
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # If /assessments?search=xxx not specified then SELECT *
        if args['search'] != None:
            cur.execute("SELECT * FROM assessments WHERE name LIKE ? OR description LIKE ?",('%' + args['search'] + '%','%' + args['search'] + '%'))
        else:
            cur.execute("SELECT * FROM assessments")
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Add tools to assessment
        for i, assessment in enumerate(data['result']):
            cur.execute("SELECT tool FROM assessment_tools WHERE assessment = ?",(str(i+1),))
            tool_ids = dict(result=[dict(r) for r in cur.fetchall()])
            assessment['tools'] = tool_ids['result']

        # Close connection
        if con:
            con.close()
        return data

    # Submit a new tool
    def post(self):
        args = parser.parse_args()
        return args

class AssessmentsId(Resource):
    # Get assessments
    def get(self, assessment_id):
        args = parser.parse_args()
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM assessments WHERE id = ?",(assessment_id),)
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Add tools to assessment
        for i, assessment in enumerate(data['result']):
            cur.execute("SELECT tool FROM assessment_tools WHERE assessment = ?",(str(i+1),))
            tool_ids = dict(result=[dict(r) for r in cur.fetchall()])
            assessment['tools'] = tool_ids['result']

        # Close connection
        if con:
            con.close()
        return data

    # Submit a new tool
    def post(self):
        args = parser.parse_args()
        return args

class Tools(Resource):
    # Get tools
    def get(self):
        args = parser.parse_args()
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
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

class ToolsId(Resource):
    # Get tools
    def get(self, tool_id):
        args = parser.parse_args()
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM tools WHERE id =?",(tool_id,))
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()
        return data

    # Submit a new tool
    def post(self):
        args = parser.parse_args()
        return args

class ToolsJobs(Resource):
    # List jobs
    def get (self):
        args = parser.parse_args()
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # If /jobs?search=xxx not specified then SELECT *
        if args['search'] != None:
           cur.execute("SELECT * FROM tool_jobs WHERE tool LIKE ? OR target LIKE ? OR target_name LIKE ? OR protocol LIKE ? OR port_number LIKE ? OR user like ? OR password LIKE ? OR user_file LIKE ? OR password_file LIKE ?",('%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%','%' + args['search'] + '%'))
        else:
           cur.execute("SELECT * FROM tool_jobs")
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

    # Submit new job
    def post(self):
        args = parser.parse_args()
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        cur = con.cursor()

        # curl -i --data "tool=1&target=localhost&target_name=target_name&protocol=https&port_number=1337&user=a_user&password=a_password&user_file=/user/file&password_file=/password/file" http://127.0.0.1:5000/jobs
        cur.execute("INSERT INTO tool_jobs(tool,target,target_name,protocol,port_number,user,password,user_file,password_file) VALUES(?,?,?,?,?,?,?,?,?)",(args['tool'],args['target'],args['target_name'],args['protocol'],args['port_number'],args['user'],args['password'],args['user_file'],args['password_file']))
        data = cur.lastrowid
        con.commit()

        # Close connection
        if con:
            con.close()

        return { 'id':data }, 201

# List individual jobs
class ToolsJobsId(Resource):
    def get(self, job_id):
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM tool_jobs WHERE id = ?",(job_id,))
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

# Execute job
class ToolsJobsIdExecute(Resource):
    def post(self):
        # Process placeholders
        tool = {}
        job = {}
        args = parser.parse_args()
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Get job id columns
        cur.execute("SELECT * FROM tool_jobs WHERE id = ?",(args['id'],))
        job_data = dict(result=[dict(r) for r in cur.fetchall()])

        # Index is now tied to database schema, yuck
        job = job_data['result'][0]
        tool['id'] = job['tool']

        # Get tool execute string and tool name
        cur.execute("SELECT * FROM tools WHERE id = ?",(tool['id'],))
        tool_data = dict(result=[dict(r) for r in cur.fetchall()])
        tool = tool_data['result'][0]

        # TODO Allow set in config file
        job['tools_directory'] = "/root/tools"
        job['date'] = strftime("%Y%m%d_%H%M%S%z")
        job['output_dir'] = os.path.dirname(os.path.abspath(__file__)) + \
                                '/' + strftime("%Y%m%d") + \
                                "_autopwn_" + \
                                job_data['result'][0]['target_name'] + \
                                "_" + tool['name']
        try:
            os.makedirs(job['output_dir'])
        except OSError as e:
            pass
            #if e.errno == errno.EEXIST:
            #    return {'message':'Directory exists'}, 500

        # Get dependencies
        cur.execute("SELECT dependency from dependencies WHERE tool = ?",(tool['id'],))
        dependency = dict(result=[dict(r) for r in cur.fetchall()])

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
        thread.append(RunThreads(tool,job,'tool'))
        # If main process dies, everything else *SHOULD* as well
        thread[-1].daemon = True
        # Start threads
        thread[-1].start()

        return {'message':'Tool executed'}, 201

class Dependencies(Resource):
    def get(self):
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
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
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
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
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT option, required FROM tool_options WHERE tool = ?",(tool_id,))
        data = dict(result=[dict(r) for r in cur.fetchall()])

        # Close connection
        if con:
            con.close()

        return data

class ToolsExports(Resource):
    def get(self):
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT id, zip_file FROM tool_jobs")
        data = dict(result=[dict(r) for r in cur.fetchall()])
        print(data)

        # Close connection
        if con:
            con.close()

        return data

# Retrieve output for job id
class ToolsExportsId(Resource):
    def get(self, job_id):
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT zip_file FROM tool_jobs WHERE id = ?",(job_id,))
        data = dict(result=[dict(r) for r in cur.fetchall()])
        zip_file = data['result'][0]['zip_file'] + '.zip'

        # Close connection
        if con:
            con.close()

        return send_file(zip_file, as_attachment=True)

# Retrieve dependencies for tool
class DependenciesId(Resource):
    def get(self, tool_id):
        con = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/assets.db')
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
# Fetch tool id
# curl -i http://127.0.0.1:5000/tools/1
api.add_resource(ToolsId, '/tools/<tool_id>')
# Fetch all assessments
# curl -i http://127.0.0.1:5000/assessments
api.add_resource(Assessments, '/assessments')
# Fetch assessment id
# curl -i http://127.0.0.1:5000/assessments/1
api.add_resource(AssessmentsId, '/assessments/<assessment_id>')


# Fetch all tool jobs
# curl -i http://127.0.0.1:5000/jobs
api.add_resource(ToolsJobs, '/tools/jobs')
# Fetch tool job id
# curl -i http://127.0.0.1:5000/jobs/1
api.add_resource(ToolsJobsId, '/tools/jobs/<job_id>')
# Execute tool job id
# curl -i --data "id=1" http://127.0.0.1:5000/jobs/execute
api.add_resource(ToolsJobsIdExecute, '/tools/jobs/execute')

# Fetch all dependencies
# curl -i http://127.0.0.1:5000/dependencies
api.add_resource(Dependencies, '/dependencies')
# Fetch all dependencies for tool id
api.add_resource(DependenciesId, '/dependencies/<tool_id>')
# TODO Review (/tools/options? /assessment/options?)
# Fetch all options
# curl -i http://127.0.0.1:5000/options
api.add_resource(Options, '/options')
# Fetch all options for tool id
# curl -i http://127.0.0.1:5000/options/1
api.add_resource(OptionsId, '/options/<tool_id>')

# Fetch all tool outputs
# curl -i http://127.0.0.1:5000/exports
api.add_resource(ToolsExports, '/tools/jobs/exports')
# Fetch tool output from job id
# curl -i http://127.0.0.1:5000/exports/1
api.add_resource(ToolsExportsId, '/tools/jobs/exports/<job_id>')

def main():
    print(os.path.dirname(os.path.abspath(__file__)))
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #context.load_cert_chain('yourserver.crt', 'yourserver.key')

    if os.path.isfile('/.dockerinit'):
        print("Running in docker")
        #app.run(host='0.0.0.0', debug=True,threaded=True,ssl_context=context)
        app.run(host='0.0.0.0', debug=True,threaded=True)
    else:
        #app.run(debug=True,threaded=True,ssl_context=context)
        app.run(debug=True,threaded=True,port=5000)

if __name__ == '__main__':
    main()
