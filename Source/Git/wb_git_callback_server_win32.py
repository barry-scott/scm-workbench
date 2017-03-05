'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_askpass_server_win32.py

'''
import sys
import ctypes
import threading

PIPE_UNLIMITED_INSTANCES = 255
PIPE_ACCESS_DUPLEX = 3
FILE_FLAG_OVERLAPPED = 0x40000000

PIPE_TYPE_MESSAGE = 4
PIPE_READMODE_MESSAGE = 2
PIPE_REJECT_REMOTE_CLIENTS = 8

INFINITE = -1
ERROR_PIPE_CONNECTED = 535
WAIT_OBJECT_0 = 0

class WbGitAskPassServer(threading.Thread):
    def __init__( self, app, ui_component ):
        super().__init__()

        self.app = app
        self.ui_component = ui_component

        self.setDaemon( 1 )
        self.running = 1

        self.pipe_name = r'\\.\pipe\SCM workbench AskPass'

        self.__thread = None
        self.__h_wait_stop = None
        self.__h_wait_reply = None
        self.__overlapped = None

    def shutdown( self ):
        ctypes.windll.kernel32.SetEvent( self.__h_wait_stop )

    def setReply( self, code, value ):
        self.__reply_code = code
        self.__reply_value = value

        ctypes.windll.kernel32.SetEvent( self.__h_wait_reply )

    def run( self ):
        class OVERLAPPED(ctypes.Structure):
            _fields_ =  [('status', ctypes.c_ulonglong)
                        ,('transfered', ctypes.c_ulonglong)
                        ,('offset', ctypes.c_ulonglong)
                        ,('hevent', ctypes.c_ulonglong)]

        # Used to signal the thread to exit
        self.__h_wait_stop = ctypes.windll.kernel32.CreateEventW( None, 0, 0, None )

        # Used to signal the thread that the reply is valid
        self.__h_wait_reply = ctypes.windll.kernel32.CreateEventW( None, 0, 0, None )

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
            self.app.log.error( 'Failed to CreateNamedPipeW( %s ): %s' %
                                    (self.pipe_name, self.__getLastErrorMessage()) )

        # Loop accepting and processing connections
        while True:
            hr = ctypes.windll.kernel32.ConnectNamedPipe( h_pipe, ctypes.byref( self.__overlapped ) )
            if hr == ERROR_PIPE_CONNECTED:
                # Client is fast, and already connected - signal event
                ctypes.windll.kernel32.SetEvent( self.__overlapped.hevent )

            # Wait for either a connection, or a service stop request.
            rc = self.__waitForMultipleObjects( (self.__h_wait_stop, self.__overlapped.hevent) )
            if rc == WAIT_OBJECT_0:
                # Stop event
                break

            else:
                # Pipe event - read the data, and write it back.
                buf_size = ctypes.c_uint( 256 )
                buf_client = ctypes.create_string_buffer( buf_size.value )
                hr = ctypes.windll.kernel32.ReadFile( h_pipe, buf_client, buf_size, ctypes.byref( buf_size ), None )
                prompt = buf_client.raw[:buf_size.value].decode( 'utf-8' )

                reply = ctypes.create_string_buffer( 256 )

                state, answer = self.__waitForReply( prompt )

                reply.value = ('%d%s' % (state, answer)).encode( 'utf-8' )
                reply_size = ctypes.c_uint( len( reply.value ) )

                hr = ctypes.windll.kernel32.WriteFile( h_pipe, reply, reply_size, ctypes.byref( reply_size ), None )

                # And disconnect from the client.
                ctypes.windll.kernel32.DisconnectNamedPipe( h_pipe )

    def __waitForMultipleObjects( self, all_handles ):
        num_handles = len( all_handles )
        wait_handles_t = ctypes.c_uint64 * num_handles
        wait_handles = wait_handles_t( *all_handles )
        return ctypes.windll.kernel32.WaitForMultipleObjects( num_handles, ctypes.byref( wait_handles ), 0, INFINITE )

    def __waitForReply( self, prompt ):
        self.app.runInForeground( self.ui_component.getGitCredentials, (prompt,) )

        rc = self.__waitForMultipleObjects( (self.__h_wait_reply,) )
        if rc == WAIT_OBJECT_0:
            return self.__reply_code, self.__reply_value

        else:
            self.app.log.error( 'WaitForMultipleObjects returned 0x%x' % (rc,) )
            return 1, ''

    def __getLastErrorMessage( self ):
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
