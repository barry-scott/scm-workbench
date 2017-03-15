#!/usr/bin/env python3
import sys
import os
import pathlib
import shutil

def copyFile( src, dst_dir ):
    dst = dst_dir / src.name
    shutil.copy( str( src ), str( dst ) )

if len(sys.argv) != 2:
    print( 'Usage: %s --test|--strict-test<docs-folder>' % (sys.argv[0],) )
    sys.exit( 1 )

if sys.argv[1] == '--test':
    output_dir = pathlib.Path( 'tmp' )
    testing = 'lazy'

elif sys.argv[1] == '--strict-test':
    output_dir = pathlib.Path( 'tmp' )
    testing = 'strict'

else:
    output_dir = pathlib.Path( sys.argv[1] )
    testing = None

output_files_dir = output_dir / 'scm-workbench_files'

builder_top_dir = pathlib.Path( os.environ['BUILDER_TOP_DIR'] )
src_dir = builder_top_dir / 'Source'
docs_dir = builder_top_dir / 'Docs'

output_dir.mkdir( parents=True, exist_ok=True )
output_files_dir.mkdir( exist_ok=True )

for src in docs_dir.glob( 'scm-workbench*.html' ):
    copyFile( src, output_dir )

copyFile( docs_dir / 'scm-workbench.css', output_dir )
copyFile( src_dir / 'wb.png', output_files_dir )

for src in (docs_dir / 'scm-workbench_files').glob( '*.png' ):
    copyFile( src, output_files_dir )

for src in (src_dir / 'toolbar_images').glob( '*.png' ):
    copyFile( src, output_files_dir )

if testing is not None:
    import check_docs
    cwd = pathlib.Path.cwd()
    os.chdir( str(output_dir) )
    if check_docs.Main().main( sys.argv ) != 0 and testing == 'strict':
        sys.exit( 1 )

    os.chdir( str(cwd) )

    index = output_dir / 'scm-workbench.html'
    if sys.platform == 'win32':
        import ctypes
        SW_SHOWNORMAL = 1
        ShellExecuteW = ctypes.windll.shell32.ShellExecuteW
        rc = ShellExecuteW( None, 'open', str(index), None, None, SW_SHOWNORMAL )

    elif sys.platform == 'darwin':
        cmd = '/usr/bin/open'
        os.spawnvp( os.P_NOWAIT, cmd, [cmd, str(index)] )

    else:
        cmd = '/usr/bin/xdg-open'
        os.spawnvp( os.P_NOWAIT, cmd, [cmd, str(index)] )

sys.exit( 0 )
