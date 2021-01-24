#!/usr/bin/env python
#
#   build_scm_workbench.py
#
#   Needs to be able to be run under python2 or python3
#   to allow older systems to use this script.
#
from __future__ import print_function

import sys
import os
import shutil
import subprocess
import platform
import glob
import zipfile
from pathlib import Path

import build_log
import build_utils

log = build_log.BuildLog()

# setup build_utils
build_utils.log = log
# alias run()
run = build_utils.run
BuildError = build_utils.BuildError

class BuildScmWorkbench(object):
    def __init__( self ):
        self.opt_colour = False
        self.opt_verbose = False
        self.opt_vcredist = None
        self.opt_prefix = Path( '/usr' )

        self.wb_version_info = {}

    def main( self, argv ):
        try:
            self.parseArgs( argv )

            log.info( 'Building SCM Workbench' )
            self.setupVars()
            self.setupVersionInfo()
            self.checkBuildDeps()

            self.ruleClean()
            self.ruleBuild()
            log.info( 'Build complete' )

        except BuildError as e:
            log.error( str(e) )
            return 1

        return 0

    def parseArgs( self, argv ):
        positional = []
        try:
            args = iter( argv )
            next(args)

            while True:
                arg = next(args)
                if arg.startswith( '--' ):
                    if arg == '--verbose':
                        self.opt_verbose = True

                    elif arg == '--colour':
                        self.opt_colour = True

                    elif arg.startswith( '--vcredist=' ):
                        self.opt_vcredist = arg[len('--vcredist='):]

                    elif arg.startswith( '--prefix=' ):
                        self.opt_prefix = Path( arg[len('--prefix='):] )

                    else:
                        raise BuildError( 'Unknown option in build_scm_workbench %r' % (arg,) )

                else:
                    positional.append( arg )

        except StopIteration:
            pass

        if len(positional) > 1:
            raise BuildError( 'Extra arguments %r' % (' '.join( positional[1:] ),) )

        if len(positional) == 1:
            self.target = positional[0]

        log.setColour( self.opt_colour )

    def setupVars( self ):
        self.platform = platform.system()
        if self.platform == 'Darwin':
            if platform.mac_ver()[0] != '':
                self.platform = 'MacOSX'

        elif self.platform == 'Windows':
            if platform.architecture()[0] == '64bit':
                self.platform = 'win64'
                self.VC_VER = '14.0'
            else:
                raise BuildError( 'Windows 32 bit is not supported' )

        self.BUILDER_TOP_DIR = Path( os.environ[ 'BUILDER_TOP_DIR' ] )

        if self.platform in ('Linux', 'NetBSD'):
            if 'DESTDIR' in os.environ:
                self.ROOT_DIR = Path( os.environ[ 'DESTDIR' ] )

            else:
                self.ROOT_DIR = self.BUILDER_TOP_DIR / 'Builder/tmp/ROOT'

            self.INSTALL_DOC_DIR = self.opt_prefix / 'share/scm-workbench/doc'
            self.INSTALL_BIN_DIR = self.opt_prefix / 'bin'

            self.BUILD_DOC_DIR = '%s%s' % (self.ROOT_DIR, self.INSTALL_DOC_DIR)
            self.BUILD_BIN_DIR = '%s%s' % (self.ROOT_DIR, self.INSTALL_BIN_DIR)

        elif self.platform == 'MacOSX':
            self.BUILD_BIN_DIR = self.BUILDER_TOP_DIR / "Builder/tmp/app/Barry's Emacs-Devel.app/Contents/Resources/bin"
            self.BUILD_DOC_DIR = self.BUILDER_TOP_DIR / "%s/Builder/tmp/app/Barry's Emacs-Devel.app/Contents/Resources/documentation"

            self.INSTALL_DOC_DIR = self.BUILD_DOC_DIR

        elif self.platform == 'win64':
            self.KITSRC = self.BUILDER_TOP_DIR / 'Kits/Windows'
            self.KITROOT = self.BUILDER_TOP_DIR / 'Builder/tmp'
            self.KITFILES = self.BUILDER_TOP_DIR / 'kitfiles'

            self.BUILD_BIN_DIR = self.KITFILES
            self.BUILD_DOC_DIR = self.KITFILES / 'Documentation'

            self.INSTALL_BIN_DIR = self.BUILD_BIN_DIR
            self.INSTALL_DOC_DIR = self.BUILD_DOC_DIR

            # fix up the PATH that may have a Qt/bin added to it that will break the build
            os.environ['PATH'] = ';'.join( [path for path in os.environ['PATH'].split(';') if not path.endswith(r'PyQt5\Qt\bin')] )

        else:
            raise BuildError( 'Unsupported platform: %s' % (self.platform,) )

    def setupVersionInfo( self ):
        with open( self.BUILDER_TOP_DIR / 'Builder' / 'version.dat' ) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith( '#' ):
                    key, value = line.split( '=', 1 )
                    if value.startswith( '"' ) and value.endswith( '"' ):
                        value = value[1:-1]

                    self.wb_version_info[ key ] = value

        self.wb_version_info[ 'version' ] = '%(major)s.%(minor)s.%(patch)s' % self.wb_version_info

    def checkBuildDeps( self ):
        log.info( 'Checking dependencies...' )
        if sys.version_info.major != 3:
            raise BuildError( 'SCM Workbench needs python version 3' )

        if self.platform in ('Linux',):
            try:
                from PyQt5 import QtWidgets, QtGui, QtCore
            except ImportError:
                raise BuildError( 'PyQt5 is not installed for %s. Hint: dnf install PyQt5' % (sys.executable,) )
            try:
                import xml_preferences
            except ImportError:
                raise BuildError( 'xml-preferences is not installed for %s. Hint: dnf install python3-xml-preferences' % (sys.executable,) )

        if self.platform in ('MacOSX', 'win64', 'NetBSD'):
            try:
                if self.platform == 'win64':
                    # in a venv on Windows need to tell the OS about the dll's that Qt uses
                    import PyQt5
                    qt_bin_dir = os.path.join( os.path.dirname( PyQt5.__file__ ), 'Qt', 'bin' )
                    os.add_dll_directory( qt_bin_dir )

                from PyQt5 import QtWidgets, QtGui, QtCore
            except ImportError:
                raise BuildError( 'PyQt5 is not installed for %s. Hint: pip3 install --user PyQt5' % (sys.executable,) )
            try:
                import xml_preferences
            except ImportError:
                raise BuildError( 'xml-preferences is not installed for %s. Hint: pip3 install --user xml-preferences' % (sys.executable,) )

        if self.platform in ('win64',):
            try:
                import win_app_packager
            except ImportError:
                raise BuildError( 'win_app_packager is not installed for %s. Hint: pip3 install --user win_app_packager' % (sys.executable,) )

            try:
                v = tuple( int(d) for d in win_app_packager.VERSION.split('.') )
                if v < (1, 3, 0):
                    raise ValueError()

            except ValueError:
                raise BuildError( 'win_app_packager version is to old for %s. Hint: pip3 install --user --upgrade win_app_packager' % (sys.executable,) )

    def ruleClean( self ):
        log.info( 'Running ruleClean' )

        if self.platform in ('Linux', 'NetBSD'):
            build_utils.rmdirAndContents( self.ROOT_DIR )

        elif self.platform == 'win64':
            if os.path.exists( self.KITROOT ):
                run( 'cmd /c "rmdir /s /q %s"' % self.KITROOT )

        elif self.platform == 'MacOSX':
            # must not remove tmp/venv
            build_utils.rmdirAndContents( 'tmp/app' )

    def ruleBuild( self ):
        for folder in (self.BUILD_DOC_DIR, self.BUILD_BIN_DIR):
            build_utils.mkdirAndParents( folder )

        self.ruleScmWorkbench()

        if self.platform == 'MacOSX':
            self.ruleMacosPackage()

        if self.platform == 'win64':
            self.ruleInnoInstaller()

    def ruleScmWorkbench( self ):
        log.info( 'Running ruleScmWorkbench' )

        if self.platform == 'MacOSX':
            run( ('./build-macosx.sh'
                 ,'--package'),
                    cwd='../Source' )

        elif self.platform == 'win64':
            run( ('build-windows.cmd'
                 ,self.KITFILES
                 ,self.wb_version_info.get('win_version'))
                 ,cwd=r'..\Source' )

        else:
            run( ('./build-linux.sh'
                 ,self.ROOT_DIR),
                    cwd='../Source' )

    def ruleMacosPackage( self ):
        log.info( 'Make macOS package' )

        pkg_name = 'SCM Workbench-%s' % (self.wb_version_info.get('version'),)
        dmg_folder = '%s/Builder/tmp/dmg' % (self.BUILDER_TOP_DIR,)
        app_folder = '%s/Builder/tmp/app' % (self.BUILDER_TOP_DIR,)

        build_utils.mkdirAndParents( app_folder )
        build_utils.mkdirAndParents( dmg_folder )

        run( ('cp', '-r',
                "%s/SCM Workbench-Devel.app" % (app_folder,),
                "%s/SCM Workbench.app" % (dmg_folder,)) )

        log.info( 'Create DMG' )
        # use 2.7 version as 3.5 version does not work yet (confuses bytes and str)
        run( ('/Library/Frameworks/Python.framework/Versions/2.7/bin/dmgbuild',
                '--settings', 'package_macos_dmg_settings.py',
                'SCM Workbench',
                '%s/%s.dmg' % (dmg_folder, pkg_name)) )

    def ruleInnoInstaller( self ):
        import package_windows_inno_setup_files
        inno_setup = package_windows_inno_setup_files.InnoSetup( self.platform, self.VC_VER, self.opt_vcredist )
        inno_setup.createInnoInstall()

        run( (r'c:\Program Files (x86)\Inno Setup 5\ISCC.exe', r'tmp\bemacs.iss') )
        build_utils.copyFile(
            r'tmp\Output\mysetup.exe',
            r'tmp\scm-workbench-%s-setup.exe' % (self.wb_version_info.get('version'),),
            0o600 )
        log.info( r'Created kit tmp\scm-workbench-%s-setup.exe' % (self.wb_version_info.get('version'),) )

def logNothing( msg ):
    pass

if __name__ == '__main__':
    sys.exit( BuildScmWorkbench().main( sys.argv ) )
