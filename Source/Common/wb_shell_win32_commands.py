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
import string
import subprocess
import tempfile
import ctypes

import wb_platform_win32_specific

def setupCommands():
    pass

def getTerminalProgramList():
    return ['CMD']

def getFileBrowserProgramList():
    return ['Explorer']

def EditFile( app, working_dir, all_filenames ):
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

def GuiDiffFiles( app, options ):
    cmd_list= [app.prefs.getDiffTool().gui_diff_tool, options]
    CreateProcess( app, cmd_list, os.path.curdir )

def ShellDiffFiles( app, options ):
    cmd_list = [app.prefs.getDiffTool().shell_diff_tool, options]
    return __run_command_with_output( cmd_list )

def ShellOpen( app, working_dir, filename ):
    app.log.info( T_('Open %s') % filename )

    SW_SHOWNORMAL = 1

    try:
        ShellExecuteW = ctypes.windll.shell32.ShellExecuteA
        ShellExecuteW( None, 'open', str(filename), None, str( working_dir ), SW_SHOWNORMAL )

    except RuntimeError as e:
        if e[0] == 31:
            app.log.error( T_('Unable to shell open %s\n'
                 'Is an application associated with this file type?') % filename )
        else:
            app.log.error( T_('Unable to shell open %(filename)s - %(error)s') %
                            {'filename': filename
                            ,'error': e[2]} )

def CommandShell( app, working_dir ):
    p = app.prefs.shell

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = list(working_dir.parts[1:])
    title.reverse()

    cmd_lines = [
        u"@title %s\n" % (' '.join( title ),),
        u"@set PYTHONPATH=\n",
        u'@cd %s\n' % (working_dir,),
        u'@echo on\n',
        ]
    if len( p.terminal_init ) > 0:
        cmd_lines.append( u'call %s\n' % (p.terminal_init,) )

    f = tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.cmd' )
    app.all_temp_files.append( f.name )
    for line in cmd_lines:
        f.write( line )
    f.close()

    command_list = [os.environ['ComSpec'], u'/k', f.name]

    CreateProcess( app, command_list, working_dir )

def FileBrowser( app, working_dir ):
    explorer = wb_platform_win32_specific.getWindowsDir() / 'explorer.exe'
    command_list = [str(explorer), '/e,%s' % (working_dir,)]

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
    command_line = ' '.join( ["%s" % (arg,) for arg in command_list] )

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
            app.log.info( T_('Created directory %s') % (current_dir,) )

        except IOError as e:
            app.log.error( T_('Create directory %(dir)s - %(error)s') %
                            {'dir': current_dir
                            ,'error': e} )
            return 0

    elif not working_dir.is_dir():
        app.log.error( T_('%s is not a directory') % (current_dir,) )
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
