import os

from autopwn2.commands.util import *
import sqlite3

from autopwn2.commands import settings, tools


@click.command()
@click.option('-d', '--database', help='The location of the old autopwn sqlite database')
@click.pass_context
def migrate_from_v1(ctx, database):
    """Migrates old autopwn data to new database"""
    if not os.path.exists(database):
        click.echo('Can\'t access database: %s' % database)
    else:
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute('SELECT * FROM options')
        ctx.base_url = '%s/settings/' % ctx.obj['URL']
        for row in cur.fetchall():
            ctx.invoke(settings.add, name=row[1], value=row[2])
        cur.execute('SELECT * FROM tools')
        ctx.base_url = '%s/tools/' % ctx.obj['URL']
        for row in cur.fetchall():
            ctx.invoke(tools.add, name=row[1], url=row[2], description=row[3], command=row[4], stdout=row[5])
