#
#   git_cmd.py
#
import sys
import subprocess
import selectors
import ctypes
import fcntl
import os

class GitCmdUnix:
    def __init__( self, cmd, io_handlers ):
        assert type(cmd) == list
        self.io_handlers = io_handlers

        self.proc = subprocess.Popen( cmd, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )

        self.__setNonBlocking( self.proc.stdout )
        self.__setNonBlocking( self.proc.stderr )
        self.__setNonBlocking( self.proc.stdin )

        self.selector = selectors.DefaultSelector()
        self.key_stdout = self.selector.register( self.proc.stdout, selectors.EVENT_READ )
        self.key_stderr = self.selector.register( self.proc.stderr, selectors.EVENT_READ )
        self.key_stdin = None

    def __setNonBlocking( self, fileobj ):
        fl = fcntl.fcntl( fileobj.fileno(), fcntl.F_GETFL )
        fcntl.fcntl( fileobj.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def dispatch( self ):
        rc = None
        draining = False
        while rc is None or draining:
            if rc is None:
                rc = self.proc.poll()

            if rc is None and self.key_stdin is not None and self.io_handlers._hasInput():
                self.key_stdin = self.selector.register( self.proc.stdin )

            draining = False
            for key, events in self.selector.select( 0.1 ):
                if key == self.key_stdout:
                    text = self.proc.stdout.read()
                    if len(text) == 0:
                       self.selector.unregister( self.proc.stdout )

                    else:
                        draining = True
                        self.io_handlers._handleStdOut( text.decode( sys.getdefaultencoding() ) )

                elif key == self.key_stderr:
                    text = self.proc.stderr.read()
                    if len(text) == 0:
                       self.selector.unregister( self.proc.stderr )

                    else:
                        draining = True
                        self.io_handlers._handleStdErr( text.decode( sys.getdefaultencoding() ) )

                elif key == self.key_stdin:
                    self.proc.stdout.write( self.io_handlers._getInput().encode( sys.getdefaultencoding() ) )
                    if self.io_handlers._hasInput() and rc is None:
                        self.selector.unregister( self.proc.stdin )

        return rc

class GitCmdWindows:
    def __init__( self, cmd, io_handlers ):
        assert type(cmd) == list
        self.io_handlers = io_handlers

        self.proc = subprocess.Popen( cmd, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )

    def dispatch( self ):
        rc = None
        draining = False
        while rc is None or draining:
            if rc is None:
                rc = self.proc.poll()

            if rc is None and self.key_stdin is not None and self.io_handlers._hasInput():
                self.key_stdin = self.selector.register( self.proc.stdin )

            draining = False
            for key, events in self.selector.select( 0.1 ):
                if key == self.key_stdout:
                    text = self.proc.stdout.read()
                    if len(text) == 0:
                       self.selector.unregister( self.proc.stdout )

                    else:
                        draining = True
                        self.io_handlers._handleStdOut( text.decode( sys.getdefaultencoding() ) )

                elif key == self.key_stderr:
                    text = self.proc.stderr.read()
                    if len(text) == 0:
                       self.selector.unregister( self.proc.stderr )

                    else:
                        draining = True
                        self.io_handlers._handleStdErr( text.decode( sys.getdefaultencoding() ) )

                elif key == self.key_stdin:
                    self.proc.stdout.write( self.io_handlers._getInput().encode( sys.getdefaultencoding() ) )
                    if self.io_handlers._hasInput() and rc is None:
                        self.selector.unregister( self.proc.stdin )

        return rc

if sys.platform == 'win32':
    GitCmd = GitCmdWindows
else:
    GitCmd = GitCmdUnix

class GitOutputStream:
    def __init__( self ):
        self.__buffer = ''

    def addText( self, text ):
        self.__buffer = self.__buffer + text

    def getLine( self, delim ):
        if delim in self.__buffer:
            index = self.__buffer.index( delim ) + 1
            line = self.__buffer[:index]
            self.__buffer = self.__buffer[index:]
            return line

        else:
            return None

class GitIoHandler:
    def __init__( self ):
        self.__input = ''
        self.__output = GitOutputStream()
        self.__error = GitOutputStream()

    def sendInput( self, text ):
        self.__input = self.__input + text

    def stdOutLine( self, text ):
        pass

    def stdErrLine( self, text ):
        pass

    # all the _xxx functions are internal and used by GitCmd
    def _hasInput( self ):
        return len( self.__input ) > 0

    def _getInput( self ):
        assert self.hasInput()

        text = self.__input[:1024]
        self.__input = self.__input[1024:]

        return text

    def _handleStdOut( self, text ):
        self.__handleOutput( text, self.__output, self.stdOutLine )

    def _handleStdErr( self, text ):
        self.__handleOutput( text, self.__error, self.stdErrLine )

    def __handleOutput( self, text, output, line_fn ):
        output.addText( text )

        for delim in ('\r', '\n'):
            while True:
                line = output.getLine( delim )
                if line is None:
                    break
                line_fn( line )

class DebugGitIoHandler(GitIoHandler):
    def __init__( self ):
        super().__init__()

    def stdOutLine( self, text ):
        print( 'stdOutLine( %r )' % (text,) )

    def stdErrLine( self, text ):
        print( 'stdErrLine( %r )' % (text,) )

if __name__ == '__main__':
    import sys
    cmd = sys.argv[1:]

    cmd = GitCmd( cmd, DebugGitIoHandler() )
    rc = cmd.dispatch()
    print( 'rc %r' % (rc,) )
