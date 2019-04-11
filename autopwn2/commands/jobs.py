import click

from . import make_click_shell
from autopwn2.commands.util import get, post, put


# id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# tool = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
# command = db.Column(db.String, nullable=False)
# startTime = db.Column(db.DateTime, nullable=True)
# endTime = db.Column(db.DateTime, nullable=True)
# return_code = db.Column(db.Integer, default=-1)

def show_setting(job):
    click.echo('ID         : %d' % job['id'])
    click.echo('command    : %s' % job['command'])
    click.echo('start time : %s' % job['startTime'])
    click.echo('end time   : %s' % job['endTime'])
    click.echo('return code: %s' % job['return_code'])


@click.group(invoke_without_command=True, name='jobs')
@click.pass_context
def base(ctx, ):
    ctx.base_url = '%s/jobs/' % ctx.obj['URL']
    """Validate or initalise a configuration file"""
    if ctx.invoked_subcommand is None:
        shell = make_click_shell(ctx, title='autopwn', prompt=':jobs> ')
        shell.cmdloop()


@base.command()
@click.option('--id', default=-1, help='Select the identifier to show (default = all)')
@click.pass_context
def show(ctx, id, ):
    if id == -1:
        response = get(ctx.parent.base_url, debug=ctx.obj['DEBUG'])
        for s in response['data']:
            show_setting(s)
    else:
        response = get("%s%d" % (ctx.parent.base_url, id), debug=ctx.obj['DEBUG'])
        show_setting(response)


@base.command()
# @click.option('--name', help='Name of the setting')
@click.option('--tool', help='')
# @click.option('--stdout', type=int, help='')
# @click.option('--description', default=None, help='')
# @click.option('--url', default=None, help='')
@click.pass_context
def add(ctx, tool, ):
    #
    response = get('%s/tools/?search=%s' % (ctx.obj['URL'], tool), debug=ctx.obj['DEBUG'])
    _tool = response['data'][0]
    params = {k: v for k, v in ctx.params.items() if v}
    params['tools_id'] = _tool['id']
    params['command'] = _tool['command']
    response = post(ctx.parent.base_url, params, debug=ctx.obj['DEBUG'])
    if ctx.obj['DEBUG']:
        click.echo('Response: %s' % (response))
    click.echo('Job added.')


# id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# description = db.Column(db.String, nullable=True)
# command = db.Column(db.String, nullable=False)
# name = db.Column(db.String, nullable=False)
# url = db.Column(db.String, nullable=True)
# stdout = db.Column(db.Integer, nullable=False)
# jobs = db.relationship('Job', backref='used_tool', cascade="all,delete")
@base.command()
@click.option('--id', type=int, help='Select the identifier')
# @click.option('--name', default=None, help='Name of the setting')
# @click.option('--tool', default=None, help='')
# @click.option('--url', default=None, help='')
# @click.option('--stdout', default=None, help='')
# @click.option('--description', default=None, help='')
@click.option('--tool', help='')
@click.pass_context
def edit(ctx, id, name, tool, stdout, description, url):
    url = "%s%d" % (ctx.parent.base_url, id)
    new = {k: v for k, v in ctx.params.items() if v}
    response = get(url, debug=ctx.obj['DEBUG'])
    response.update(new)
    del response['id']
    response = put(url, response, debug=ctx.obj['DEBUG'])
    if ctx.obj['DEBUG']:
        click.echo('Response: %s' % (response))
    click.echo('Setting updated.')


@base.command()
@click.option('--id', type=int, help='Select the identifier')
@click.pass_context
def execute(ctx, id):
    url = "%s%d/execute" % (ctx.parent.base_url, id)
    response = post(url, debug=ctx.obj['DEBUG'])
    if ctx.obj['DEBUG']:
        click.echo('Response: %s' % (response))
    click.echo('Job executed.')
