import click

from autopwn2.commands import *


@click.group(invoke_without_command=True, context_settings={'help_option_names': ['-h', '--help'],
                                                            'ignore_unknown_options': True,
                                                            'allow_extra_args': True, })
@click.option('-d', '--debug / --no-debug', default=False, help="Show debug info")
@click.option('-u', '--url', default="http://localhost:5000", help="Set autopwn url (default: http://localhost:5000)", metavar='<url>')
@click.pass_context
def cli(ctx, debug, url):
    ctx.obj = {'DEBUG': debug, 'URL': url}
    check_server(ctx)
    if ctx.invoked_subcommand is None:
        shell = make_click_shell(ctx, prompt='> ', title='autopwn', intro='AutoPwn interactive ...')
        # ctx.obj['INTERACTIVE'] = shell
        shell.cmdloop()


add_to_cli(cli)

if __name__ == '__main__':
    cli()
