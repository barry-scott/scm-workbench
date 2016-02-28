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

def setupCommands():
    pass

def getTerminalProgramList():
    return ['CMD']

def getFileBrowserProgramList():
    return ['Explorer']

def EditFile( app, project_info, filename ):
    p = app.prefs.getEditor()

    if p.editor_image:
        if p.editor_options:
            command_line = (u'"%s" %s "%s"' %
                (p.editor_image, p.editor_options, filename))
        else:
            command_line = (u'"%s" "%s"' %
                (p.editor_image, filename))
    else:
        command_line = (u'"notepad.exe" "%s"' %
                            (filename,))

    app.log.info( command_line )
    CreateProcess( app, command_line, project_info.getWorkingDir() )

def GuiDiffFiles( app, options ):
    cmd_line = '"%s" %s' % (app.prefs.getDiffTool().gui_diff_tool, options)
    app.log.info( cmd_line )
    CreateProcess( app, cmd_line, os.path.curdir )

def ShellDiffFiles( app, options ):
    cmd_line = (u'"%s" %s' %
                    (app.prefs.getDiffTool().shell_diff_tool
                    ,options))
    app.log.info( cmd_line )
    return __run_command_with_output( cmd_line )

def ShellOpen( app, project_info, filename ):
    app.log.info( T_('Open %s') % filename )
    try:
        # QQQ use ctypes to do ShellExecute
        win32api.ShellExecute( 0, 'open',
                    filename, '',
                    project_info.getWorkingDir(),
                    win32con.SW_SHOWNORMAL )
    except win32api.error, e:
        if e[0] == 31:
            app.log.error( T_('Unable to shell open %s\n'
                 'Is an application associated with this file type?') % filename )
        else:
            app.log.error( T_('Unable to shell open %(filename)s - %(error)s') %
                            {'filename': filename
                            ,'error': e[2]} )

def CommandShell( app, project_info ):
    p = app.prefs.getShell()
    working_dir = project_info.getWorkingDir()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = []
    pi = project_info
    while pi:
        title.append( pi.project_name )
        pi = pi.parent

    cmd_lines = [
        u"@title %s\n" % (' '.join( title ),),
        u"@set PYTHONPATH=\n",
        u'@cd %s\n' % (working_dir,),
        u'@echo on\n',
        ]
    if len( p.shell_init_command ) > 0:
        cmd_lines.append( u'call %s\n' % (p.shell_init_command,) )

    f = tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.cmd' )
    app.all_temp_files.append( f.name )
    for line in cmd_lines:
        f.write( line.encode( 'utf-8' ) )
    f.close()

    command_line = u'"%s" /k "%s"' % (os.environ['ComSpec'], f.name)

    app.log.info( command_line )
    CreateProcess( app, command_line, working_dir )

def FileBrowser( app, project_info ):
    command_line = (u'explorer.exe /e,%s' %
                        (project_info.getWorkingDir(),))

    app.log.info( command_line )
    CreateProcess( app, command_line, project_info.getWorkingDir() )


def CreateProcess( app, command_line, current_dir ):
    if not ensureDirectory( app, current_dir ):
        return

    try:
        import ctypes
        old_value = ctypes.c_long( 0 )
        try:
            ctypes.windll.kernel32.Wow64DisableWow64FsRedirection( ctypes.byref( old_value ) )
        except:
            pass

        si = win32process.STARTUPINFO()
        h_process, h_thread, process_id, thread_id = win32process.CreateProcess(
            None,
            command_line,
            None,               # processAttributes
            None,               # threadAttributes , 
            0,                  # bInheritHandles ,
            win32con.CREATE_NEW_CONSOLE,    # dwCreationFlags ,
            None,               # newEnvironment ,
            current_dir,        # currentDirectory ,
            si                  # startupinfo
            )

        try:
            ctypes.windll.kernel32.Wow64RevertWow64FsRedirection( old_value )
        except:
            pass


    except win32process.error, detail:
        app.log.error( T_('Create process failed for command - %(command)s\n'
                        'Reason %(reason)s') %
                            {'command': command_line
                            ,'reason': detail} )

def ensureDirectory( app, current_dir ):
    if not current_dir.exists():
        try:
            current_dir.mkdir( parents=True )
            app.log.info( T_('Created directory %s') % (current_dir,) )

        except IOError, e:
            app.log.error( T_('Create directory %(dir)s - %(error)s') %
                            {'dir': current_dir
                            ,'error': e} )
            return 0

    elif not current_dir.is_dir():
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

    except EnvironmentError, e:
        return '%s - %s' % (err_prefix, str(e))
