'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_shell_unix_commands.py

'''
from PyQt5 import QtCore

import os
import signal
import subprocess
import types
import shlex
import tempfile
import pathlib

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

    except OSError as e:
        pass

def getTerminalProgramList():
    return gui_terminals[:]

def getFileBrowserProgramList():
    return gui_file_browsers[:]

def EditFile( app, working_dir, all_filenames ):
    p = app.prefs.getEditor()

    editor = p.getEditorProgram()
    if editor == '':
        app.log.warning( T_('Please configure the editor in the Preferences Editor tab') )
        return
    
    options = p.getEditorOptions()

    editor_args = []
    if options != '':
        editor_args = shlex.split( options )

    editor_args.extend( all_filenames )

    __run_command( app, editor, editor_args, working_dir )

def ShellOpen( app, working_dir, all_filenames ):
    app.log.info( T_('Open %s') % (' '.join( [str(name) for name in all_filenames] ),) )

    for filename in all_filenames:
        # xdg-open only accepts 1 filename at a time
        __run_command( app, '/usr/bin/xdg-open', [filename], working_dir )

def GuiDiffFiles( app, args ):
    __run_command( app, app.prefs.getDiffTool().gui_diff_tool, args. os.getcwd() )

def ShellDiffFiles( app, args ):
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

def CommandShell( app, working_dir ):
    p = app.prefs.getShell()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = __titleFromPath( working_dir )

    with tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.sh' ) as f:
        app.all_temp_files.append( f.name )
        
        if len( p.getTerminalInitCommand() ) > 0:
            f.write( ". '%s'\n" % (p.getTerminalInitCommand(),) )
        f.write( 'exec "$SHELL" -i\n' )
        f.close()
        # chmod +x
        os.chmod( f.name, 0o700 )

    path = os.environ.get( 'PATH' )
    terminal_program = p.getTerminalProgram()
    if terminal_program == '':
        app.log.warning( T_('Please configure the Terminal in the Preferences Shell tab') )
        return

    found = False
    for folder in path.split( os.pathsep ):
        exe = os.path.join( folder, terminal_program )
        if os.path.isfile( exe ):
            found = True
            break

    if not found:
        app.log.warning( T_('Cannot find the Terminal program %s.') % (terminal_program,) )
        app.log.warning( T_('Please configure a terminal program that is installed on the system in the Preferences Shell tab') )
        return

    os.environ['WB_WD'] = str( working_dir )
    try:
        if terminal_program == 'konsole':
            __run_command( app, terminal_program,
                ['--title',  title, '--workdir', working_dir, '-e', '/bin/bash', f.name],
                working_dir )

        elif terminal_program in ('gnome-terminal', 'xfce4-terminal'):
            __run_command( app, terminal_program,
                ['--title',  title, '--working-directory', working_dir, '-x', f.name],
                working_dir )

        elif terminal_program == 'xterm':
            __run_command( app, terminal_program,
                ['-T',  title, '-e', f.name],
                working_dir )

    finally:
        del os.environ['WB_WD']

def FileBrowser( app, working_dir ):
    p = app.prefs.getShell()

    path = os.environ.get("PATH")
    found = False

    browser_program = p.getFileBrowserProgram()
    if browser_program == '':
        app.log.warning( T_('Please configure the File Browser in the Preferences Shell tab') )
        return

    for folder in path.split( os.pathsep ):
        exe = os.path.join( folder, browser_program )
        if os.path.isfile(exe):
            found = True
            break

    if not found:
        app.log.warning( T_('Cannot find the File Browser program %s.') % (browser_program,) )
        app.log.warning( T_('Please configure a File Browser program that is installed on the system in the Preferences Shell tab') )
        return

    if browser_program == 'konqueror':
        __run_command( app,
                browser_program,
                ['--mimetype', 'inode/directory', working_dir],
                working_dir )

    elif browser_program in ('nautilus', 'thunar', 'dolphin'):
        __run_command( app,
                browser_program,
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
        rc = proc.wait()

    except EnvironmentError as e:
        return 'error running %s %s: %s' % (cmd, ' '.join( args ), str(e))

    return output
