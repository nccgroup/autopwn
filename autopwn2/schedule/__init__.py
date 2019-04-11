import datetime
import logging
from locale import getdefaultlocale
from subprocess import Popen, PIPE

from flask_apscheduler import APScheduler

from autopwn2.database import db
from autopwn2.database.models import Job

scheduler = APScheduler()

log = logging.getLogger(__name__)


def init_schedule(app):
    scheduler.init_app(app)
    scheduler.start()


def scheduled_task(id):
    with scheduler.app.app_context():
        log.info('Starting job id #%s' % id)
        job = Job.query.filter(Job.id == id).one()
        _command = job.command
        _toolname = job.tool.name
        _stdout = job.tool.stdout
        job.startTime = datetime.datetime.now()

        # run job
        log.info('Running cmd: %s' % _command)

        proc = Popen(_command, stdout=PIPE, stderr=PIPE, shell=True)
        decode_locale = lambda s: s.decode(getdefaultlocale()[1])
        tool_stdout, tool_stderr = map(decode_locale, proc.communicate())
        return_code = proc.returncode

        # when finished set end time of job
        log.info('Job [%s] finished' % id)
        job.endTime = datetime.datetime.now()
        job.return_code = return_code

        if _stdout == 1:
            filename = '%s-%d-%s.txt' % (_toolname, job.id, job.endTime.strftime('%Y%m%d%H%M%S'))
            with open(filename, 'w') as file:
                file.write('[%s] (job id:%d) started at %s\n' % (job.command, job.id, job.startTime))
                file.write('---------------------------------------------------\n')
                file.write('output:\n')
                file.write(tool_stdout)
                file.write('\n---------------------------------------------------\n')
                file.write('\nerror:\n')
                file.write(tool_stderr)
                file.write('\n---------------------------------------------------\n')
                file.write('\njob (#%d) ended at %s\n' % (job.id, job.endTime))
            log.info('Writtng STDOUT/STSERR to %s' % filename)
        db.session.commit()
