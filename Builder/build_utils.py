#
#   Needs to run under python2 or python3
#
from __future__ import print_function

import sys
import os
import subprocess

log = None

if sys.version_info[0] == 2:
    unicode_type = unicode

else:
    unicode_type = str

class BuildError(Exception):
    def __init__( self, msg ):
        super(BuildError, self).__init__( msg )

# use a python3 compatible subprocess.run() function
class CompletedProcess(object):
    def __init__(self, returncode, stdout=None, stderr=None):
        self.returncode = returncode

        if stdout is not None:
            self.stdout = stdout.decode( 'utf-8' )
        else:
            self.stdout = stdout

        if stderr is not None:
            self.stderr = stderr.decode( 'utf-8' )
        else:
            self.stderr = stderr

class Popen(subprocess.Popen):
    def __init__( self, *args, **kwargs ):
        super(Popen, self).__init__( *args, **kwargs )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()

        # Wait for the process to terminate, to avoid zombies.
        self.wait()

def run( cmd, check=True, output=False, cwd=None ):
    kwargs = {}
    if type(cmd) is unicode_type:
        log.info( 'Running %s' % (cmd,) )
        kwargs['shell'] = True
    else:
        log.info( 'Running %s' % (' '.join( cmd ),) )
    if cwd:
        kwargs['cwd'] = cwd
    else:
        cwd = os.getcwd()

    if output:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE

    with Popen(cmd, **kwargs) as process:
        try:
            stdout, stderr = process.communicate( input=None )

        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise

        retcode = process.poll()
        r = CompletedProcess( retcode, stdout, stderr )
        if check and retcode != 0:
            raise BuildError( 'Cmd failed %s - %r' % (retcode, cmd) )

    return r
