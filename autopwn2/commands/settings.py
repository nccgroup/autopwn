import click

from . import make_click_shell
from autopwn2.commands.util import get, post, put


def show_setting(setting):
    click.echo('ID     : %d' % setting['id'])
    click.echo('name   : %s' % setting['name'])
    click.echo('value  : %s' % setting['value'])
    click.echo('example: %s' % setting['example'])


@click.group(invoke_without_command=True, name='settings')
@click.pass_context
def base(ctx, ):
    ctx.base_url = '%s/settings/' % ctx.obj['URL']
    """Validate or initalise a configuration file"""
    # shell = ctx.obj['INTERACTIVE']
    # shell.set_context_level('config')
    # ctx.obj = {'DEBUG': debug, 'URL': url, 'INTERACTIVE': False}
    if ctx.invoked_subcommand is None:
        shell = make_click_shell(ctx, title='autopwn', prompt=':settings> ')
        # ctx.obj['INTERACTIVE'] = shell
        shell.cmdloop()


@base.command()
@click.option('--id', default=-1, help='Select the identifier to show (default = all)')
@click.pass_context
def show(ctx, id):
    if id == -1:
        response = get(ctx.parent.base_url, debug=ctx.obj['DEBUG'])
        # click.echo('Response: %s' % (response['data']))
        for s in response['data']:
            show_setting(s)
    else:
        response = get("%s%d" % (ctx.parent.base_url, id), debug=ctx.obj['DEBUG'])
        # click.echo('Response: %s' % (response))
        show_setting(response)


@base.command(context_settings=dict(ignore_unknown_options=True,
                                    allow_extra_args=True, ))
@click.option('--name', help='Name of the setting')
@click.option('--value', help='')
@click.option('--example', default=None, help='')
@click.pass_context
def add(ctx, name, value, example):
    response = post(ctx.parent.base_url, {k: v for k, v in ctx.params.items() if v}, debug=ctx.obj['DEBUG'])
    if ctx.obj['DEBUG']:
        click.echo('Response: %s' % (response))
    click.echo('Setting added.')


@base.command()
@click.option('--id', type=int, help='Select the identifier to show (default = all)')
@click.option('--name', default=None, help='Name of the setting')
@click.option('--value', default=None, help='')
@click.option('--example', default=None, help='')
@click.pass_context
def edit(ctx, id, name, value, example):
    url = "%s%d" % (ctx.parent.base_url, id)
    new = {k: v for k, v in ctx.params.items() if v}
    response = get(url, debug=ctx.obj['DEBUG'])
    response.update(new)
    del response['id']
    response = put(url, response, debug=ctx.obj['DEBUG'])
    if ctx.obj['DEBUG']:
        click.echo('Response: %s' % (response))
    click.echo('Setting updated.')
