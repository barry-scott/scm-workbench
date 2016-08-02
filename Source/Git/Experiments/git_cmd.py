#
#   git_cmd.py
#
import sys
import subprocess

if sys.platform == 'win32':
    import _winapi
    import msvcrt

else:
    import selectors
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
            for key, events in self.selector.select( 0.01 ):
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

            self.io_handlers._dispatch()

        return rc

class GitCmdWindows:
    def __init__( self, cmd, io_handlers ):
        assert type(cmd) == list
        self.io_handlers = io_handlers

        CREATE_NO_WINDOW = 0x08000000
        self.proc = subprocess.Popen( cmd, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=CREATE_NO_WINDOW )
        self.stdin = self.proc.stdin
        self.stdout = self.proc.stdout
        self.stderr = self.proc.stderr

    def dispatch( self ):
        rc = None
        draining = False
        while rc is None or draining:
            if rc is None:
                rc = self.proc.poll()

            all_fileobj = []
            if self.stdout is not None:
                all_fileobj.append( self.stdout )
            if self.stderr is not None:
                all_fileobj.append( self.stderr )

            if rc is None and self.io_handlers._hasInput() and self.stdin is not None:
                all_fileobj.append( self.stdio )

            draining = False
            while rc is None or draining:
                all_handles = [msvcrt.get_osfhandle( fileobj.fileno() ) for fileobj in all_fileobj]
                result = _winapi.WaitForMultipleObjects( all_handles, 0, 10 )
                print( 'result %r' % (result,) )
                if result == _winapi.WAIT_TIMEOUT:
                    break

                handle = all_handles[ result ]
                fileobj = all_fileobj[ result ]

                if fileobj == self.stdout:
                    try:
                        text, err = _winapi.ReadFile( handle, 128, 0 )

                        if len(text) > 0:
                            draining = True
                            self.io_handlers._handleStdOut( text.decode( sys.getdefaultencoding() ) )

                    except BrokenPipeError:
                        self.stdout = None

                elif fileobj == self.stderr:
                    try:
                        text, err = _winapi.ReadFile( handle, 1024, 0 )
                        assert err == 0
                        if len(text) > 0:
                            draining = True
                            self.io_handlers._handleStdErr( text.decode( sys.getdefaultencoding() ) )

                    except BrokenPipeError:
                        self.stderr = None

                elif fileobj == self.stdin:
                    written, err = _winapi.WriteFile( handle, self.io_handlers._getInput().encode( sys.getdefaultencoding() ), False )

            self.io_handlers._dispatch()

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
        self.__output.addText( text )

    def _handleStdErr( self, text ):
        self.__error.addText( text )

    def _dispatch( self ):
        self.__dispatchOutput( self.__output, self.stdOutLine )
        self.__dispatchOutput( self.__error, self.stdErrLine )

    if sys.platform == 'win32':
        delim_list = ('\r\n', '\r', '\n')

    else:
        delim_list = ('\r', '\n')

    def __dispatchOutput( self, output, line_fn ):
        for delim in self.delim_list:
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
    cmd = GitCmd( sys.argv[1:], DebugGitIoHandler() )
    rc = cmd.dispatch()
    print( 'rc %r' % (rc,) )
