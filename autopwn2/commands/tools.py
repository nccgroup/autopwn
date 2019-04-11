import click

from . import make_click_shell
from autopwn2.commands.util import get, post, put


def show_setting(tool):
    click.echo('ID         : %d' % tool['id'])
    click.echo('name       : %s' % tool['name'])
    click.echo('command    : %s' % tool['command'])
    click.echo('description: %s' % tool['description'])
    click.echo('url        : %s' % tool['url'])
    click.echo('stdout     : %s' % tool['stdout'])


@click.group(invoke_without_command=True, name='tools')
@click.pass_context
def base(ctx, ):
    ctx.base_url = '%s/tools/' % ctx.obj['URL']
    """Validate or initalise a configuration file"""
    # shell = ctx.obj['INTERACTIVE']
    # shell.set_context_level('config')
    # ctx.obj = {'DEBUG': debug, 'URL': url, 'INTERACTIVE': False}
    if ctx.invoked_subcommand is None:
        shell = make_click_shell(ctx, title='autopwn', prompt=':tools> ')
        # ctx.obj['INTERACTIVE'] = shell
        shell.cmdloop()


@base.command()
@click.option('--id', default=-1, help='Select the identifier to show (default = all)')
@click.option('--search', default=None, help='Searches for a specific setting')
@click.pass_context
def show(ctx, id, search):
    if id == -1:
        if search is None:
            response = get(ctx.parent.base_url, debug=ctx.obj['DEBUG'])
            # click.echo('Response: %s' % (response['data']))
        else:
            response = get(ctx.parent.base_url, {'search': search}, debug=ctx.obj['DEBUG'])
        for s in response['data']:
            show_setting(s)
    else:
        response = get("%s%d" % (ctx.parent.base_url, id), debug=ctx.obj['DEBUG'])
        # click.echo('Response: %s' % (response))
        show_setting(response)


@base.command()
@click.option('--name', help='Name of the setting')
@click.option('--command', help='')
@click.option('--stdout', type=int, help='')
@click.option('--description', default=None, help='')
@click.option('--url', default=None, help='')
@click.pass_context
def add(ctx, name, command, stdout, description, url):
    response = post(ctx.parent.base_url, {k: v for k, v in ctx.params.items() if v}, debug=ctx.obj['DEBUG'])
    if ctx.obj['DEBUG']:
        click.echo('Response: %s' % (response))
    click.echo('Setting added.')


# id = db.Column(db.Integer, primary_key=True, autoincrement=True)
# description = db.Column(db.String, nullable=True)
# command = db.Column(db.String, nullable=False)
# name = db.Column(db.String, nullable=False)
# url = db.Column(db.String, nullable=True)
# stdout = db.Column(db.Integer, nullable=False)
# jobs = db.relationship('Job', backref='used_tool', cascade="all,delete")
@base.command()
@click.option('--id', type=int, help='Select the identifier to show (default = all)')
@click.option('--name', default=None, help='Name of the setting')
@click.option('--command', default=None, help='')
@click.option('--url', default=None, help='')
@click.option('--stdout', default=None, help='')
@click.option('--description', default=None, help='')
@click.pass_context
def edit(ctx, id, name, command, stdout, description, url):
    url = "%s%d" % (ctx.parent.base_url, id)
    new = {k: v for k, v in ctx.params.items() if v}
    response = get(url, debug=ctx.obj['DEBUG'])
    response.update(new)
    del response['id']
    response = put(url, response, debug=ctx.obj['DEBUG'])
    if ctx.obj['DEBUG']:
        click.echo('Response: %s' % (response))
    click.echo('Setting updated.')
