'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_shell_win32_commands.py

'''
import ctypes
import os
import subprocess
import tempfile
import shutil

import wb_platform_win32_specific

__all__ = ('setupCommands', 'getTerminalProgramList', 'getFileBrowserProgramList'
          ,'editFile', 'hasMeld', 'diffMeldFolder', 'diffMeldTwoFiles'
          ,'shellOpen', 'commandShell', 'fileBrowser')

def U_( s: str ) -> str:
    return s

def setupCommands():
    pass

def getTerminalProgramList():
    return [program for program in ('cmd', 'powershell', 'bash')
            if shutil.which( '%s.exe' % (program,) )]

def getFileBrowserProgramList():
    return ['Explorer']

def editFile( app, working_dir, all_filenames ):
    app.log.infoheader( T_('Edit %s') % (' '.join( [str(name) for name in all_filenames] ),) )
    p = app.prefs.editor

    if p.program:
        if p.options:
            command_list = [p.program, p.options]
            command_list.extend( all_filenames )
        else:
            command_list = [p.program]
            command_list.extend( all_filenames )
    else:
        notepad = wb_platform_win32_specific.getWindowsDir() / 'notepad.exe'
        command_list = [str(notepad)]
        command_list.extend( all_filenames )

    CreateProcess( app, command_list, working_dir )

SW_SHOWNORMAL = 1

ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_BAD_FORMAT = 11

SE_ERR_ACCESSDENIED = 5
SE_ERR_ASSOCINCOMPLETE = 27
SE_ERR_DDEBUSY = 30
SE_ERR_DDEFAIL = 29
SE_ERR_DDETIMEOUT = 28
SE_ERR_DLLNOTFOUND = 32
SE_ERR_NOASSOC = 31
SE_ERR_OOM = 8
SE_ERR_SHARE = 26
SE_ERR_DLLNOTFOUND = 32

se_error_messages = {
    SE_ERR_ACCESSDENIED:    U_('The operating system denied access to the specified file.'),
    SE_ERR_ASSOCINCOMPLETE: U_('The file name association is incomplete or invalid.'),
    SE_ERR_DDEBUSY:         U_('The DDE transaction cannot be completed because other DDE transactions are being processed.'),
    SE_ERR_DDEFAIL:         U_('The DDE transaction failed.'),
    SE_ERR_DDETIMEOUT:      U_('The DDE transaction cannot be completed because the request timed out.'),
    SE_ERR_DLLNOTFOUND:     U_('The specified dynamic-link library is not found.'),
    SE_ERR_NOASSOC:         U_('There is no application associated with the given file name extension.'),
    SE_ERR_OOM:             U_('There is not enough memory or free resources to complete the operation.'),
    SE_ERR_SHARE:           U_('A sharing violation occurred.'),
    SE_ERR_DLLNOTFOUND:     U_('The specified dynamic-link library is not found.'),
}

def __getShellExecuteErrorMessage( err ):
    if err in se_error_messages:
        return T_( se_error_messages[ err ] )

    else:
        return getErrorMessage( err )



meld_program = None

# must call hasMeld before trying to use meld
def hasMeld( app ):
    global meld_program
    if meld_program is None:
        meld_program = shutil.which( 'meld' )

    return meld_program is not None

def getMeld( app ):
    return meld_program

def diffMeldFolder( app, working_dir, folder ):
    __run_command( app, getMeld( app ), [folder], working_dir )

def diffMeldTwoFiles( app, working_dir, file1, header1, file2, header2 ):
    __run_command( app, getMeld( app ),
                    ['--lable=%s' % (header1,), file1
                    ,'--lable=%s' % (header2,), file2], working_dir )

def shellOpen( app, working_dir, all_filenames ):
    app.log.infoheader( T_('Open %s') % (' '.join( [str(name) for name in all_filenames] ),) )
    for filename in all_filenames:
        ShellExecuteW = ctypes.windll.shell32.ShellExecuteW
        rc = ShellExecuteW( None, 'open', str(filename), None, str(working_dir), SW_SHOWNORMAL )
        if rc <= 32:
            if rc == SE_ERR_NOASSOC:
                app.log.error( T_('Unable to shell open %s\n'
                     'Is an application associated with this file type?') % filename )

            else:
                app.log.error( T_('Unable to shell open %(filename)s - %(error)s') %
                                {'filename': filename
                                ,'error': __getShellExecuteErrorMessage( rc )} )

def commandShell( app, working_dir ):
    app.log.infoheader( 'Shell in %s' % (working_dir,) )
    p = app.prefs.shell

    abs_terminal_program = shutil.which( '%s.exe' % (p.terminal_program,) )
    if abs_terminal_program is None:
        app.log.error( 'Cannot find %s.exe' % (p.terminal_program,) )

    if p.terminal_program == 'cmd':
        # calc a title that is leaf to root so that the leaf shows up in a task bar first
        title = list(working_dir.parts[1:])
        title.reverse()

        cmd_lines = [
            '@title %s\n' % (' '.join( title ),),
            '@set PYTHONPATH=\n',
            '@cd %s\n' % (working_dir,),
            '@echo on\n',
            ]
        if len( p.terminal_init ) > 0:
            cmd_lines.append( 'call %s\n' % (p.terminal_init,) )

        with tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.cmd' ) as f:
            app.all_temp_files.append( f.name )
            for line in cmd_lines:
                f.write( line )

        command_list = [abs_terminal_program, '/k', f.name]

    elif p.terminal_program == 'powershell':
        #
        # powershell does not allow scripts to be run by default
        # see http://go.microsoft.com/fwlink/?LinkID=135170 for details
        #
        if False:   # if we find a way to run commands...
            # calc a title that is leaf to root so that the leaf shows up in a task bar first
            title = list(working_dir.parts[1:])
            title.reverse()

            cmd_lines = [
                'set PYTHONPATH=\n',
                'cd %s\n' % (working_dir,),
                '$host.ui.RawUI.WindowTitle = "%s"\n' % (title,),
                ]
            if len( p.terminal_init ) > 0:
                cmd_lines.append( 'call %s\n' % (p.terminal_init,) )

            with tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.ps1' ) as f:
                app.all_temp_files.append( f.name )
                for line in cmd_lines:
                    f.write( line )

        command_list = [abs_terminal_program, '-NoExit' ] #, '-file', f.name]

    elif p.terminal_program == 'bash':
        #
        # bash can be convinced to run a script passed via --rcfile
        # but it seems that it will only run the rcfile if its
        # in the working_dir.
        # create the tmp file in the working_dir using '\n' line endings
        # CR-LF will not work.
        # run the users .bashrc to setup the environment
        #

        # calc a title that is leaf to root so that the leaf shows up in a task bar first
        title = list(working_dir.parts[1:])
        title.reverse()

        rcfile = working_dir / 'wb-shell.bash.tmp'

        cmd_lines = [
            'echo -e "\\e]0;%s\\007"\n' % (' '.join( title ),),
            'unset PYTHONPATH\n',
            'if [ -e "$HOME/.bashrc" ]\n',
            'then\n',
            '    . $HOME/.bashrc\n',
            'fi\n',
            'rm -f %s' % (rcfile.name,),
            ]
        if len( p.terminal_init ) > 0:
            cmd_lines.append( '. %s\n' % (p.terminal_init,) )

        with open( str(rcfile), mode='w', newline='\n' ) as f:
            app.all_temp_files.append( str(rcfile) )
            for line in cmd_lines:
                f.write( line )

        # replace the uses .bashrc with our script
        command_list = [abs_terminal_program, '--rcfile', rcfile.name]

    else:
        app.log.error( 'Unknown shell %r' % (p.terminal_program,) )
        return

    CreateProcess( app, command_list, working_dir )

def fileBrowser( app, working_dir ):
    app.log.infoheader( 'Browse files in %s' % (working_dir,) )

    explorer = wb_platform_win32_specific.getWindowsDir() / 'explorer.exe'
    command_list = [str(explorer), '/e,/root,"%s"' % (working_dir,)]

    CreateProcess( app, command_list, working_dir )

#------------------------------------------------------------
CREATE_NEW_CONSOLE = 0x00000010

class STARTUPINFO(ctypes.Structure):
    _fields_ =  [('cb',                 ctypes.c_uint)
                ,('lpReserved',         ctypes.c_wchar_p)
                ,('lpDesktop',          ctypes.c_wchar_p)
                ,('lpTitle',            ctypes.c_wchar_p)
                ,('dwX',                ctypes.c_uint)
                ,('dwY',                ctypes.c_uint)
                ,('dwXSize',            ctypes.c_uint)
                ,('dwYSize',            ctypes.c_uint)
                ,('dwXCountChars',      ctypes.c_uint)
                ,('dwYCountChars',      ctypes.c_uint)
                ,('dwFillAttribute',    ctypes.c_uint)
                ,('dwFlags',            ctypes.c_uint)
                ,('wShowWindow',        ctypes.c_ushort)
                ,('cbReserved2',        ctypes.c_ushort)
                ,('lpReserved2',        ctypes.c_void_p)
                ,('hStdInput',          ctypes.c_void_p)
                ,('hStdOutput',         ctypes.c_void_p)
                ,('hStdError',          ctypes.c_void_p)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ =  [('hProcess',           ctypes.c_void_p)
                ,('hThread',            ctypes.c_void_p)
                ,('dwProcessId',        ctypes.c_uint)
                ,('dwThreadId',         ctypes.c_uint)]

def CreateProcess( app, command_list, working_dir ):
    if not ensureDirectory( app, working_dir ):
        return

    old_value = ctypes.c_long( 0 )
    try:
        ctypes.windll.kernel32.Wow64DisableWow64FsRedirection( ctypes.byref( old_value ) )

    except:
        pass

    s_info = STARTUPINFO()
    s_info.cb = ctypes.sizeof( s_info )

    p_info = PROCESS_INFORMATION( None, None, 0, 0 )

    working_dir = str(working_dir)
    quoted_args = []
    for arg in command_list:
        arg = str(arg)
        if '"' in arg:
            quoted_args.append( arg )
        else:
            quoted_args.append( '"%s"' % (arg,) )

    command_line = ' '.join( quoted_args )

    app.log.info( command_line )

    rc = ctypes.windll.kernel32.CreateProcessW(
            command_list[0],                # LPCTSTR lpApplicationName,
            command_line,                   # LPTSTR lpCommandLine,
            None,                           # LPSECURITY_ATTRIBUTES lpProcessAttributes,
            None,                           # LPSECURITY_ATTRIBUTES lpThreadAttributes,
            False,                          # BOOL bInheritHandles,
            CREATE_NEW_CONSOLE,             # DWORD dwCreationFlags,
            None,                           # LPVOID lpEnvironment,
            working_dir,                    # LPCTSTR lpCurrentDirectory,
            ctypes.byref( s_info ),         # LPSTARTUPINFO lpStartupInfo,
            ctypes.byref( p_info )          # LPPROCESS_INFORMATION lpProcessInformation
            )
    if rc == 0:
        err = getLastError()
        app.log.error( T_('Create process failed for command - %(command)s\n'
                        'Reason %(reason)s') %
                            {'command': command_line
                            ,'reason': getErrorMessage( err )} )

    try:
        ctypes.windll.kernel32.Wow64RevertWow64FsRedirection( old_value )

    except:
        pass

def getLastError():
    return ctypes.windll.kernel32.GetLastError()

def getErrorMessage( err ):
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


def ensureDirectory( app, working_dir ):
    if not working_dir.exists():
        try:
            working_dir.mkdir( parents=True )
            app.log.info( T_('Created directory %s') % (working_dir,) )

        except IOError as e:
            app.log.error( T_('Create directory %(dir)s - %(error)s') %
                            {'dir': working_dir
                            ,'error': e} )
            return 0

    elif not working_dir.is_dir():
        app.log.error( T_('%s is not a directory') % (working_dir,) )
        return 0

    return 1

def __run_command_with_output( command_line ):
    err_prefix = 'error running %s' % command_line
    try:
        proc = subprocess.Popen(
                    command_line,
                    bufsize=-1,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                    )
        all_output = proc.stdout.read()
        proc.wait()

        return all_output

    except EnvironmentError as e:
        return '%s - %s' % (err_prefix, str(e))
