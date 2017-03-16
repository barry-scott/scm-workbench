#!/usr/bin/env python3
import sys
import os
import pathlib
import shutil

def copyFile( src, dst_dir ):
    dst = dst_dir / src.name
    shutil.copy( str( src ), str( dst ) )

version = sys.argv[1]
built_kits_dir = pathlib.Path( sys.argv[2] )
testing = '--test' in sys.argv[3:]

# source paths
builder_top_dir = pathlib.Path( os.environ['BUILDER_TOP_DIR'] )
src_dir = builder_top_dir / 'Source'
docs_dir = builder_top_dir / 'Docs'
web_site_dir = builder_top_dir / 'WebSite'
root_dir = web_site_dir / 'root'

# output paths
output_dir = pathlib.Path( 'tmp' )
output_kits_dir = output_dir / 'kits'
user_guide_dir = output_dir / 'user-guide'

shutil.rmtree( str( output_dir ) )

output_dir.mkdir( parents=True, exist_ok=True )
output_kits_dir.mkdir( parents=True, exist_ok=True )

for src in root_dir.glob( '*.html' ):
    copyFile( src, output_dir )

# use the user guide's CSS
copyFile( docs_dir / 'scm-workbench.css', output_dir )

rc = os.system( '"%s/build-docs.py" "%s"' % (docs_dir, user_guide_dir) )
if rc != 0:
    print( 'build docs failed' )
    sys.exit( 1 )

for kit_fmt in ('SCM-Workbench-%s-setup.exe',
                'SCM-Workbench-%s.dmg',
                'scm-workbench-%s-1.fc25.noarch.rpm',
                'scm-workbench-%s-1.fc25.src.rpm'):
    copyFile( built_kits_dir / (kit_fmt % (version,)), output_kits_dir )

with open( str( output_dir / 'index.html' ), encoding='utf-8' ) as f:
    index = f.read()

with open( str( output_dir / 'index.html' ), 'w', encoding='utf-8' ) as f:
    f.write( index % {'VERSION': version} )

if testing:
    index = output_dir / 'index.html'
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

print( 'Web Site created in %s for version %s' % (output_dir, version) )

sys.exit( 0 )
