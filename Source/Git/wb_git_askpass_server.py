'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_askpass.py

    called with argv[1:] as the prompt
    expects a single line output as response.

'''
import ctypes

class WbGitAskPassServer:
    def __init__( self ):
        self.pipe_name = r'\\.\pipe\SCM workbench AskPass'

        self.__h_wait_stop = None
        self.__overlapped = None


    def processRequests( self ):
        PIPE_UNLIMITED_INSTANCES = 255
        PIPE_ACCESS_DUPLEX = 3
        FILE_FLAG_OVERLAPPED = 0x40000000

        PIPE_TYPE_MESSAGE = 4
        PIPE_READMODE_MESSAGE = 2
        PIPE_REJECT_REMOTE_CLIENTS = 8

        INFINITE = -1
        ERROR_PIPE_CONNECTED = 535
        WAIT_OBJECT_0 = 0

        class OVERLAPPED(ctypes.Structure):
            _fields_ =  [('status', ctypes.c_ulonglong)
                        ,('transfered', ctypes.c_ulonglong)
                        ,('offset', ctypes.c_ulonglong)
                        ,('hevent', ctypes.c_ulonglong)]

        # QQQ: seems like a hang over from an older design...
        self.__h_wait_stop = ctypes.windll.kernel32.CreateEventW( None, 0, 0, None )

        # We need to use overlapped IO for this, so we dont block when
        # waiting for a client to connect.  This is the only effective way
        # to handle either a client connection, or a service stop request.
        self.__overlapped = OVERLAPPED( 0, 0, 0, 0 )

        # And create an event to be used in the OVERLAPPED object.
        self.__overlapped.hevent = ctypes.windll.kernel32.CreateEventW( None, 0, 0, None )

        # We create our named pipe.

        h_pipe = ctypes.windll.kernel32.CreateNamedPipeW(
                        self.pipe_name,                 #  __in      LPCTSTR lpName,
                        PIPE_ACCESS_DUPLEX
                        | FILE_FLAG_OVERLAPPED,         #  __in      DWORD dwOpenMode,
                        PIPE_TYPE_MESSAGE
                        | PIPE_READMODE_MESSAGE
                        | PIPE_REJECT_REMOTE_CLIENTS,   #  __in      DWORD dwPipeMode,
                        PIPE_UNLIMITED_INSTANCES,       #  __in      DWORD nMaxInstances,
                        0,                              #  __in      DWORD nOutBufferSize,
                        0,                              #  __in      DWORD nInBufferSize,
                        100,                            #  __in      DWORD nDefaultTimeOut, (100ms)
                        None                            #  __in_opt  LPSECURITY_ATTRIBUTES lpSecurityAttributes
                        )
        if h_pipe is None:
            self.app.log_client_log( 'Failed to CreateNamedPipeW( %s ): %s' %
                                    (self.pipe_name, self.__getLastErrorMessage()) )

        # Loop accepting and processing connections
        while True:
            hr = ctypes.windll.kernel32.ConnectNamedPipe( h_pipe, ctypes.byref( self.__overlapped ) )
            if hr == ERROR_PIPE_CONNECTED:
                # Client is fast, and already connected - signal event
                ctypes.windll.kernel32.SetEvent( self.__overlapped.hevent )

            # Wait for either a connection, or a service stop request.
            wait_handles_t = ctypes.c_uint64 * 2
            wait_handles = wait_handles_t( self.__h_wait_stop, self.__overlapped.hevent )

            rc = ctypes.windll.kernel32.WaitForMultipleObjects( 2, ctypes.byref( wait_handles ), 0, INFINITE )

            if rc == WAIT_OBJECT_0:
                # Stop event
                break

            else:
                # Pipe event - read the data, and write it back.
                buf_size = ctypes.c_uint( 256 )
                buf_client = ctypes.create_string_buffer( buf_size.value )
                hr = ctypes.windll.kernel32.ReadFile( h_pipe, buf_client, buf_size, ctypes.byref( buf_size ), None )
                prompt = buf_client.raw[:buf_size.value].decode( 'utf-8' )
                print( 'prompt %r' % (prompt,) )

                reply = ctypes.create_string_buffer( 256 )

                reply.value = ('0Example response: %s' % (prompt,)).encode( 'utf-8' )
                reply_size = ctypes.c_uint( len( reply.value ) )

                hr = ctypes.windll.kernel32.WriteFile( h_pipe, reply, reply_size, ctypes.byref( reply_size ), None )

                # And disconnect from the client.
                ctypes.windll.kernel32.DisconnectNamedPipe( h_pipe )

    def __getLastErrorMessage( self ):
        import ctypes

        err = ctypes.windll.kernel32.GetLastError()

        FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
        FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200

        errmsg_size = ctypes.c_int( 256 )
        errmsg = ctypes.create_string_buffer( errmsg_size.value + 1 )

        rc = ctypes.windll.kernel32.FormatMessageA(
            FORMAT_MESSAGE_FROM_SYSTEM|FORMAT_MESSAGE_IGNORE_INSERTS, # __in      DWORD dwFlags,
            None,           # __in_opt  LPCVOID lpSource,
            err,            # __in      DWORD dwMessageId,
            0,              # __in      DWORD dwLanguageId,
            errmsg,         # __out     LPTSTR lpBuffer,
            errmsg_size,    # __in      DWORD nSize,
            None            # __in_opt  va_list *Arguments
            )
        if rc == 0:
            return 'error 0x%8.8x' % (err,)

        return errmsg.value

if __name__ == '__main__':
    server = WbGitAskPassServer()
    server.processRequests()
