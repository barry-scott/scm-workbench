# -*- mode: python ; coding: utf-8 -*-

import wb_scm_version
import os.path
import subprocess

class VersionInfo:
    def __init__( self ):
        self.BUILDER_TOP_DIR = os.environ['BUILDER_TOP_DIR']

        with open( os.path.join( self.BUILDER_TOP_DIR, 'Builder', 'version.dat'), 'r' ) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith( '#' ):
                    key, value = line.split( '=', 1 )
                    if value.startswith( '"' ) and value.endswith( '"' ):
                        value = value[1:-1]

                    setattr( self, key, value )

        result = subprocess.run( ['git', 'show-ref', '--head', '--hash', 'head'], stdout=subprocess.PIPE )
        self.commit = result.stdout.decode('utf-8').strip()

        self.version = '%(major)s.%(minor)s.%(patch)s' % self.__dict__
        self.info_string = '%(APP_NAME)s %(major)s.%(minor)s.%(patch)s %(commit)s ©%(copyright_years)s Barry A. Scott. All Rights Reserved.' % self.__dict__

v = VersionInfo()

block_cipher = None

pathex = os.environ['PYTHONPATH'].split(':')
dist_dir = os.environ['DIST_DIR']

a = Analysis(
    ['Scm/wb_scm_main.py'],
    pathex=pathex,
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
    )

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
    )

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='%(APP_NAME)s',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(dist_dir, 'wb.icns')
    )

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=v.APP_NAME
    )

app = BUNDLE(
    coll,
    name='%s.app' % (v.APP_NAME,),
    icon=os.path.join(dist_dir, 'wb.icns'),
    bundle_identifier=v.APP_ID,
    info_plist=
        dict(
            CFBundleIdentifier=v.APP_ID,
            CFBundleName=v.APP_NAME,
            CFBundleVersion=v.version,
            CFBundleShortVersionString=v.version,
            CFBundleGetInfoString=v.info_string,
            # claim we know about dark mode
            NSRequiresAquaSystemAppearance='false',
            ),

    )
