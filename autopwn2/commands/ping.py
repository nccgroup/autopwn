import click

from autopwn2.commands.util import get


@click.command(name='ping')
@click.option('-m', '--message', help='Select the identifier to show (default = all)')
@click.pass_context
def ping(ctx, message):
    url = '%s/ping' % ctx.obj['URL']
    payload = {}
    if not message == '':
        payload['message']=message
    response = get(url, payload, debug=ctx.obj['DEBUG'])
    click.echo('Response: %s' % (response['message']))
