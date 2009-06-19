import subprocess
import logging
from flexget.plugin import *

__pychecker__ = 'unusednames=parser'

log = logging.getLogger('exec')

class OutputExec:
    """
    Execute command for entries that reach output.
    
    Example:
    
    exec: echo 'found %(title)s at %(url)s > file
    
    You can use all (available) entry fields in the command.
    """
    def validator(self):
        from flexget import validator
        return validator.factory('text')

    def feed_output(self, feed):
        for entry in feed.accepted:
            cmd = feed.config['exec'] % entry
            log.debug('executing cmd: %s' % cmd)
            p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
            (r, w) = (p.stdout, p.stdin)
            r.close()
            w.close()

register_plugin(OutputExec, 'exec')