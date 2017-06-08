'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_shell_unix_commands.py

'''
import os
import signal
import subprocess
import types
import shlex
import tempfile
import pathlib

from PyQt5 import QtCore

__all__ = ('setupCommands', 'getTerminalProgramList', 'getFileBrowserProgramList'
          ,'guiDiffFiles', 'shellDiffFiles', 'editFile'
          ,'shellOpen', 'commandShell', 'fileBrowser')

__sigchld_handler_installed = False

gui_terminals = ['gnome-terminal', 'konsole', 'xterm', 'xfce4-terminal']
gui_file_browsers = ['nautilus', 'konqueror', 'thunar', 'dolphin']

def setupCommands():
    # install the sig child handler to get rid of the zombie processes
    global __sigchld_handler_installed
    if not __sigchld_handler_installed:
        signal.signal( signal.SIGCHLD, __sigchld_handler )
        __sigchld_handler_installed = True

def __sigchld_handler( signum, frame ):
    try:
        while True:
            pid, status = os.waitpid( -1, os.WNOHANG )
            if pid == 0:
                break

    except OSError:
        pass

def getTerminalProgramList():
    return gui_terminals[:]

def getFileBrowserProgramList():
    return gui_file_browsers[:]

def editFile( app, working_dir, all_filenames ):
    app.log.infoheader( T_('Edit %s') % (' '.join( [str(name) for name in all_filenames] ),) )
    p = app.prefs.editor

    editor = p.program
    if editor == '':
        app.log.warning( T_('Please configure the editor in the Preferences Editor tab') )
        return

    options = p.options

    editor_args = []
    if options != '':
        editor_args = shlex.split( options )

    editor_args.extend( all_filenames )


    __run_command( app, editor, editor_args, working_dir )

def shellOpen( app, working_dir, all_filenames ):
    app.log.infoheader( T_('Open %s') % (' '.join( [str(name) for name in all_filenames] ),) )

    for filename in all_filenames:
        # xdg-open only accepts 1 filename at a time
        __run_command( app, '/usr/bin/xdg-open', [filename], working_dir )

def guiDiffFiles( app, args ):
    __run_command( app, app.prefs.getDiffTool().gui_diff_tool, args. os.getcwd() )

def shellDiffFiles( app, args ):
    return __run_command_with_output( app, app.prefs.getDiffTool().shell_diff_tool, args )

def __titleFromPath( working_dir ):
    title = []
    try:
        rel_path = working_dir.relative_to( os.environ['HOME'] )
    except ValueError:
        rel_path = working_dir

    empty = pathlib.Path('.')
    while rel_path != empty:
        title.append( rel_path.name )
        rel_path = rel_path.parent

    return ' '.join( title )

def commandShell( app, working_dir ):
    app.log.infoheader( 'Shell in %s' % (working_dir,) )
    p = app.prefs.shell

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = __titleFromPath( working_dir )

    with tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.sh' ) as f:
        app.all_temp_files.append( f.name )

        if len( p.terminal_init ) > 0:
            f.write( ". '%s'\n" % (p.terminal_init,) )
        f.write( 'exec "$SHELL" -i\n' )
        f.close()
        # chmod +x
        os.chmod( f.name, 0o700 )

    path = os.environ.get( 'PATH' )
    if p.terminal_program == '':
        app.log.warning( T_('Please configure the Terminal in the Preferences Shell tab') )
        return

    found = False
    for folder in path.split( os.pathsep ):
        exe = pathlib.Path( folder ) / p.terminal_program
        if exe.is_file():
            found = True
            break

    if not found:
        app.log.warning( T_('Cannot find the Terminal program %s.') % (p.terminal_program,) )
        app.log.warning( T_('Please configure a terminal program that is installed on the system in the Preferences Shell tab') )
        return

    os.environ['WB_WD'] = str( working_dir )
    try:
        if p.terminal_program == 'konsole':
            __run_command( app, p.terminal_program,
                ['--title',  title, '--workdir', working_dir, '-e', '/bin/bash', f.name],
                working_dir )

        elif p.terminal_program in ('gnome-terminal', 'xfce4-terminal'):
            __run_command( app, p.terminal_program,
                ['--title',  title, '--working-directory', working_dir, '-x', f.name],
                working_dir )

        elif terminal_program == 'xterm':
            __run_command( app, p.terminal_program,
                ['-T',  title, '-e', f.name],
                working_dir )

    finally:
        del os.environ['WB_WD']

def fileBrowser( app, working_dir ):
    app.log.infoheader( 'Browse files in %s' % (working_dir,) )
    p = app.prefs.shell

    path = os.environ.get("PATH")
    found = False

    if p.file_browser == '':
        app.log.warning( T_('Please configure the File Browser in the Preferences Shell tab') )
        return

    for folder in path.split( os.pathsep ):
        exe = pathlib.Path( folder ) / p.file_browser
        if exe.is_file():
            found = True
            break

    if not found:
        app.log.warning( T_('Cannot find the File Browser program %s.') % (p.file_browser,) )
        app.log.warning( T_('Please configure a File Browser program that is installed on the system in the Preferences Shell tab') )
        return

    if p.file_browser == 'konqueror':
        __run_command( app,
                p.file_browser,
                ['--mimetype', 'inode/directory', working_dir],
                working_dir )

    elif p.file_browser in ('nautilus', 'thunar', 'dolphin'):
        __run_command( app,
                p.file_browser,
                [working_dir],
                working_dir )

def __run_command( app, cmd, all_args, working_dir ):
    all_args = [str(arg) for arg in all_args]
    app.log.info( '%s %s' % (cmd, ' '.join( all_args ) ) )
    proc = QtCore.QProcess()
    proc.setStandardInputFile( proc.nullDevice() )
    proc.setStandardOutputFile( proc.nullDevice() )
    proc.setStandardErrorFile( proc.nullDevice() )
    proc.startDetached( cmd, all_args, str( working_dir ) )

def __run_commandQQQ( app, cmd, args ):
    app.log.info( '%s %s' % (cmd, ' '.join( args ) ) )

    env = os.environ.copy()
    cmd = asUtf8( cmd )
    args = [asUtf8( arg ) for arg in args]

    os.spawnvpe( os.P_NOWAIT, cmd, [cmd]+args, env )

def asUtf8( s ):
    if isinstance( s, pathlib.Path ):
        s = str( s )

    if type( s ) == str:
        return s.encode( 'utf-8' )
    else:
        return s

def __run_command_with_output( app, cmd, args ):
    app.log.info( '%s %s' % (cmd, ' '.join( args )) )

    try:
        cmd = asUtf8( cmd )
        args = [asUtf8( arg ) for arg in args]
        proc = subprocess.Popen(
                    [cmd]+args,
                    close_fds=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                    )

        output = proc.stdout.read()
        proc.wait()

    except EnvironmentError as e:
        return 'error running %s %s: %s' % (cmd, ' '.join( args ), str(e))

    return output
