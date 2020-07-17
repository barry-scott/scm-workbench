#!/usr/bin/env python3
import sys
import os
import pathlib
import shutil

def copyFile( src, dst_dir ):
    dst = dst_dir / src.name
    shutil.copy( str( src ), str( dst ) )

if len(sys.argv) < 3:
    print( 'Usage: %s <version> <kits-folder> [--test] [--install]' % (sys.argv[0],) )
    print( '       %s 0.9.3 /shared/Downloads/ScmWorkbench/0.9.3' % (sys.argv[0],) )

version = sys.argv[1]
built_kits_dir = pathlib.Path( sys.argv[2] )
testing = '--test' in sys.argv[3:]
install = '--install' in sys.argv[3:]

# source paths
builder_top_dir = pathlib.Path( os.environ['BUILDER_TOP_DIR'] )
src_dir = builder_top_dir / 'Source'
docs_dir = builder_top_dir / 'Docs'
web_site_dir = builder_top_dir / 'WebSite'
root_dir = web_site_dir / 'root'
docs_files_dir = docs_dir / 'scm-workbench_files'

# output paths
output_dir = pathlib.Path( 'tmp' )
output_kits_dir = output_dir / 'kits'
output_user_guide_dir = output_dir / 'user-guide'
output_user_guide_files_dir = output_dir / 'user-guide' / 'scm-workbench_files'

shutil.rmtree( str( output_dir ) )

output_dir.mkdir( parents=True, exist_ok=True )
output_kits_dir.mkdir( parents=True, exist_ok=True )

for src in root_dir.glob( '*.html' ):
    copyFile( src, output_dir )

# use the user guide's CSS
copyFile( docs_dir / 'scm-workbench.css', output_dir )

rc = os.system( '"%s/build-docs.py" "%s"' % (docs_dir, output_user_guide_dir) )
if rc != 0:
    print( 'build docs failed' )
    sys.exit( 1 )

# copy doc images
output_user_guide_files_dir.mkdir( parents=True, exist_ok=True )
for src in docs_files_dir.glob( '*.png' ):
    copyFile( src, output_user_guide_files_dir )

kit_values = {
    'VERSION': version,
    }

for kit_fmt in ('SCM-Workbench-%(VERSION)s-setup.exe',
                'SCM-Workbench-%(VERSION)s.dmg'):
    copyFile( built_kits_dir / (kit_fmt % kit_values), output_kits_dir )

with open( str( output_dir / 'index.html' ), encoding='utf-8' ) as f:
    index = f.read()

with open( str( output_dir / 'index.html' ), 'w', encoding='utf-8' ) as f:
    f.write( index % kit_values )

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

if install:
    web_root = '/var/www/scm-workbench.barrys-emacs.org'
    os.system( 'ssh root@qrm.org.uk mkdir -p %s/kits' % (web_root,) )
    os.system( 'ssh root@qrm.org.uk mkdir -p %s/user-guide/scm-workbench_files' % (web_root,) )
    os.system( 'scp tmp/index.html tmp/scm-workbench.css root@qrm.org.uk:%s/' % (web_root,) )
    os.system( 'scp tmp/kits/* root@qrm.org.uk:%s/kits/' % (web_root,) )
    os.system( 'scp tmp/user-guide/* root@qrm.org.uk:%s/user-guide/' % (web_root,) )
    os.system( 'scp tmp/user-guide/scm-workbench_files/* root@qrm.org.uk:%s/user-guide/scm-workbench_files' % (web_root,) )
    os.system( 'ssh root@qrm.org.uk chmod -R -v  a+r %s' % (web_root,) )

sys.exit( 0 )
