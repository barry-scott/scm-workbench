'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_shell_macosx_commands.py

'''
import os
import signal
import subprocess
import xml.sax.saxutils
import shlex
import types
import tempfile
import pathlib

__sigchld_handler_installed = False

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

    except OSError, e:
        pass

def getTerminalProgramList():
    return ['Terminal', 'iTerm', 'iTerm2 V3']

def getFileBrowserProgramList():
    return ['Finder']

def GuiDiffFiles( app, args ):
    __run_command( app, app.prefs.getDiffTool().gui_diff_tool, args )

def ShellDiffFiles( app, args ):
    return __run_command_with_output( app, app.prefs.getDiffTool().shell_diff_tool, args )

def EditFile( app, working_dir, filename ):
    p = app.prefs.getEditor()

    if p.editor_image:
        if p.editor_options:
            cmd = p.editor_image
            args = shlex.split( p.editor_options ) + [filename]
        else:
            cmd = p.editor_image
            args = [filename]
    else:
        cmd = '/usr/bin/open'
        args = ['-e', filename]

    cur_dir = os.getcwd()
    try:
        os.chdir( working_dir )
        __run_command( app, cmd, args )

    finally:
        os.chdir( cur_dir )

def ShellOpen( app, working_dir, filename ):
    cur_dir = os.getcwd()
    try:
        os.chdir( working_dir )
        __run_command( app, u'/usr/bin/open', [filename] )

    finally:
        os.chdir( cur_dir )

def CommandShell( app, working_dir ):
    p = app.prefs.getShell()
    if p.shell_terminal == 'iTerm':
        CommandShell_iTerm( app, working_dir )

    elif p.shell_terminal == 'iTerm2 V3':
        CommandShell_iTerm2_V3( app, working_dir )

    else:
        CommandShell_Terminal( app, working_dir )

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

def CommandShell_iTerm( app, working_dir ):
    p = app.prefs.getShell()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = _titleFromPath( working_dir )

    commands = u'cd "%s"' % (working_dir.replace( '"', '\\\\"' ).replace( '$', '\\\\$' ),)

    if len( p.shell_init_command ) > 0:
        commands = commands + u';export WB_WD="$PWD"; . "%s"' % (p.shell_init_command.replace( '"', '\\\\"' ).replace( '$', '\\\\$' ),)

    contents = u'''
tell application "iTerm"
    activate 

    -- make a new terminal
    set work_bench_term to (make new terminal) 

    -- talk to the new terminal
    tell work_bench_term 
        activate current session
        launch session "Default Session"

        -- talk to the session
        tell the last session
            set name to "%s"

            -- execute a command
            exec command "/bin/bash"

            write text "%s"

        end tell

    end tell

end
''' %   (.replace( '"', '\\"' )
        ,commands.replace( '"', '\\"' ))

    f = tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.scpt' )
    app.all_temp_files.append( f.name )
    f.write( contents.encode( 'utf-8' ) )
    f.close()

    __run_command( app, u'/usr/bin/osascript', [f.name] )

def CommandShell_iTerm2_V3( app, working_dir ):
    p = app.prefs.getShell()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = __titleFromPath( working_dir )
    commands = u'cd "%s"' % (working_dir.replace( '"', '\\\\"' ).replace( '$', '\\\\$' ),)

    if len( p.shell_init_command ) > 0:
        commands = commands + u';export WB_WD="$PWD"; . "%s"' % (p.shell_init_command.replace( '"', '\\\\"' ).replace( '$', '\\\\$' ),)

    contents = u'''
tell application "iTerm"
    activate 
    -- make a new terminal
    create window with default profile command "/bin/bash -l"
    tell current window
        tell current session
            set name to "%s"
            write text "%s"
        end tell
    end tell
end tell
''' %   (title.replace( '"', '\\"' )
        ,commands.replace( '"', '\\"' ))

    f = tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-shell', suffix='.scpt' )
    app.all_temp_files.append( f.name )
    f.write( contents.encode( 'utf-8' ) )
    f.close()

    __run_command( app, u'/usr/bin/osascript', [f.name] )

def CommandShell_Terminal( app, working_dir ):
    p = app.prefs.getShell()

    # calc a title that is leaf to root so that the leaf shows up in a task bar first
    title = __titleFromPath( working_dir )

    commands = u"cd '%s'" % (working_dir,)

    if len( p.shell_init_command ) > 0:
        commands = commands + ";. '%s'\n" % (p.shell_init_command,)

    contents = u'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>WindowSettings</key>
    <array>
        <dict>
            <key>CustomTitle</key>
            <string>%s</string>
            <key>ExecutionString</key>
            <string>%s</string>
        </dict>
    </array>
</dict>
</plist>
''' %   (xml.sax.saxutils.escape( title )
        ,xml.sax.saxutils.escape( commands ))

    f = tempfile.NamedTemporaryFile( mode='w', delete=False, prefix='tmp-wb-term', suffix='.term' )
    app.all_temp_files.append( f.name )
    f.write( contents.encode( 'utf-8' ) )
    f.close()

    __run_command( app, u'/usr/bin/open', [f.name] )

def FileBrowser( app, working_dir ):
    __run_command( app, u'/usr/bin/open', [u'-a', u'Finder', working_dir] )

def __run_command( app, cmd, args ):
    app.log.info( '%s %s' % (cmd, ' '.join( args ) ) )

    env = os.environ.copy()
    cmd = asUtf8( cmd )
    args = [asUtf8( arg ) for arg in args]

    os.spawnvpe( os.P_NOWAIT, cmd, [cmd]+args, env )

def __run_command_with_output( app, cmd, args ):
    err_prefix = u'error running %s %s' % (cmd, ' '.join( args ))

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
        return output

    except EnvironmentError, e:
        return '%s - %s' % (err_prefix, str(e))

def asUtf8( s ):
    if type( s ) == types.UnicodeType:
        return s.encode( 'utf-8' )
    else:
        return s