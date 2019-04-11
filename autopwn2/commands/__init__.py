import click
from click_shell._cmd import ClickCmd, readline
from click_shell._compat import get_method_type
from click_shell.core import get_invoke, get_help, get_complete
from click._compat import raw_input as get_input


class MyClickShell(ClickCmd):

    def __init__(self, ctx=None, hist_file=None, *args, **kwargs):
        super(MyClickShell, self).__init__(ctx, hist_file, *args, **kwargs)
        self.context_level = None
        self.title = ''

    def add_command(self, cmd, name):
        # Use the MethodType to add these as bound methods to our current instance
        setattr(self, 'do_%s' % name, get_method_type(get_invoke(cmd), self))
        setattr(self, 'help_%s' % name, get_method_type(get_help(cmd), self))
        setattr(self, 'complete_%s' % name, get_method_type(get_complete(cmd), self))

    def cmdloop(self, intro=None):
        self.preloop()
        if self.completekey and readline:
            self.old_completer = readline.get_completer()
            self.old_delims = readline.get_completer_delims()
            readline.set_completer(self.complete)
            readline.set_completer_delims(' \n\t')
            to_parse = self.completekey + ': complete'
            readline.parse_and_bind(to_parse)
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                click.echo(self.intro, file=self.stdout)
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    try:
                        line = get_input(self.get_prompt())
                    except EOFError:
                        # We just want to quit here instead of changing the arg to EOF
                        click.echo(file=self.stdout)
                        break
                    except KeyboardInterrupt:
                        # We don't want to exit the shell on a keyboard interrupt
                        click.echo(file=self.stdout)
                        click.echo('KeyboardInterrupt', file=self.stdout)
                        continue
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)

        finally:
            self.postloop()
            if self.completekey and readline:
                readline.set_completer(self.old_completer)
                readline.set_completer_delims(self.old_delims)

    def get_prompt(self):
        prompt = self.title + (':' + self.context_level if self.context_level else '')
        return '%s%s' % (prompt, super(MyClickShell, self).get_prompt())

    def set_context_level(self, level):
        self.context_level = level
        back = click.Command('back', help='go back', callback=self.do_back)
        self.ctx.command.commands[level].commands['back'] = back

    def remove_context_level(self):
        self.context_level = None

    def do_help(self, arg):
        super(MyClickShell, self).do_help(arg)

    def do_back(self, *args, **kwargs):
        if self.ctx.parent is None:
            return False
        else:
            return True

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if 'back' in cmds and self.context_level is None:
            cmds.remove('back')
        # if self.context_level is not None:

        if cmds:
            self.stdout.write("%s\n" % str(header))
            if self.ruler:
                self.stdout.write("%s\n" % str(self.ruler * len(header)))
            self.columnize(cmds, maxcol - 1)
            self.stdout.write("\n")


def make_click_shell(ctx, prompt=None, title=None, intro=None, hist_file=None):
    assert isinstance(ctx, click.Context)
    assert isinstance(ctx.command, click.MultiCommand)

    # Set this to None so that it doesn't get printed out in usage messages
    ctx.info_name = None

    # Create our shell object
    shell = MyClickShell(ctx=ctx, hist_file=hist_file)

    if prompt is not None:
        shell.prompt = prompt

    if intro is not None:
        shell.intro = intro

    if title is not None:
        shell.title = title

    # Add all the commands
    for name in ctx.command.list_commands(ctx):
        command = ctx.command.get_command(ctx, name)
        shell.add_command(command, name)

    return shell


def add_to_cli(cli):
    from autopwn2.commands import settings, ping, migrate, tools, jobs

    cli.add_command(settings.base)
    cli.add_command(tools.base)
    cli.add_command(jobs.base)
    cli.add_command(ping.ping)
    cli.add_command(migrate.migrate_from_v1)


def check_server(ctx):
    try:
        from autopwn2.commands.util import get
        url = '%s/ping' % ctx.obj['URL']
        get(url, {}, debug=False)
    except:
        click.echo('Server not running, exiting')
        exit(1)


__all__ = ['add_to_cli', 'make_click_shell', 'check_server']
