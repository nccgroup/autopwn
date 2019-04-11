from autopwn2.api import get_or_model
from autopwn2.database import db, with_session
from autopwn2.database.models import Setting, Tool, Job
from autopwn2.schedule import scheduler, scheduled_task


@with_session
def create_setting(data):
    name = data.get('name')
    value = data.get('value')
    example = data.get('example')
    setting = Setting(name, value, example)
    db.session.add(setting)


@with_session
def update_setting(id, data):
    setting = Setting.query.filter(Setting.id == id).one()
    setting.name = get_or_model('name', data, setting)
    setting.value = get_or_model('value', data, setting)
    setting.example = get_or_model('example', data, setting)
    db.session.add(setting)


@with_session
def delete_setting(id):
    setting = Setting.query.filter(Setting.id == id).one()
    db.session.delete(setting)


@with_session
def create_tool(data):
    name = data.get('name')
    command = data.get('command')
    description = data.get('description')
    url = data.get('url')
    stdout = data.get('stdout')
    tool = Tool(name, command, description, url, stdout)
    db.session.add(tool)


@with_session
def update_tool(id, data):
    tool = Tool.query.filter(Tool.id == id).one()
    tool.name = get_or_model('name', data, tool)
    tool.command = get_or_model('command', data, tool)
    tool.description = get_or_model('description', data, tool)
    tool.url = get_or_model('url', data, tool)
    tool.stdout = get_or_model('stdout', data, tool)
    db.session.add(tool)


@with_session
def delete_tool(id):
    tool = Tool.query.filter(Tool.id == id).one()
    db.session.delete(tool)


@with_session
def create_job(data):
    settings = {}
    for s in Setting.query.all():
        settings[s.name] = s.value
    # command = data.get('command')
    tool = Tool.query.filter(Tool.id == data['tool_id']).one()
    command = tool.command.format(**settings)
    job = Job(command, tool)
    job.tool = tool
    db.session.add(job)


@with_session
def update_job(id, data):
    job = Job.query.filter(Job.id == id).one()
    job.command = get_or_model('command', data, job)
    tool_id = data.get('tool_id')
    job.tool = Tool.query.filter(Tool.id == tool_id).one()
    db.session.add(job)


@with_session
def delete_job(id):
    job = Job.query.filter(Job.id == id).one()
    db.session.delete(job)


def start_job(id):
    scheduler.add_job(func=scheduled_task, trigger='date', args=[id], id='j' + str(id))
