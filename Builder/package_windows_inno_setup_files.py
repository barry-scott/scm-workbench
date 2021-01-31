import sys
import time
import os
import datetime
import pathlib
import build_utils

class InnoSetup:
    def __init__( self, log, arch, vc_ver, wb_version_info ):
        self.log = log

        self.wb_version_info = wb_version_info

        self.arch = arch
        self.vc_ver = vc_ver

        self.build_time  = time.time()
        self.build_time_str = time.strftime( '%d-%b-%Y %H:%M', time.localtime( self.build_time ) )

        self.year = datetime.datetime.now().year
        self.BUILDER_TOP_DIR = os.environ[ 'BUILDER_TOP_DIR' ]

        self.all_code_items = []
        self.all_setup_items = []
        self.all_task_items = []
        self.all_file_items = []
        self.all_registry_items = []
        self.all_icon_items = []
        self.all_run_items = []

    def createInnoInstall( self ):
        self.setupInnoItems()
        self.generateInnoFile()

    def setupInnoItems( self ):
        self.log.info( 'Create info_before.txt' )

        version = self.wb_version_info[ 'version' ]

        f = open( r'tmp\info_before.txt', 'w' )
        f.write(
'''SCM Workbench %(version)s for %(arch)s

    Barry Scott

    %(date)s
''' %   {'version': version
        ,'arch': self.arch
        ,'date': self.build_time_str} )
        f.close()

        self.all_setup_items.extend( [
                r'''AppName=%(APP_NAME)s''' % self.wb_version_info,
                r'''AppVerName=SCM Workbench %(major)s.%(minor)s.%(patch)s''' % self.wb_version_info,
                r'''AppCopyright=Copyright (C) %(copyright_years)s Barry A. Scott''' % self.wb_version_info,
                r'''DefaultDirName={pf}\Barry Scott\%(APP_NAME)s''' % self.wb_version_info,
                r'''DefaultGroupName=%(APP_NAME)s''' % self.wb_version_info,
                r'''UninstallDisplayIcon={app}\SCM Workbench.exe''',
                r'''ChangesAssociations=yes''',
                r'''DisableStartupPrompt=yes''',
                r'''InfoBeforeFile=info_before.txt''',
                r'''Compression=bzip/9''',
                ] )

        self.all_task_items.extend( [
                r'''Name: "option_desktop_icon"; Flags: unchecked; Description: "Place %(APP_NAME)s icon on the Desktop"''' % self.wb_version_info,
                r'''Name: "option_start_menu_icon"; Description: "Place %(APP_NAME)s on the Start menu"''' % self.wb_version_info,
                ] )

        self.all_icon_items.extend( [
                r'''Name: "{group}\SCM Workbench"; Filename: "{app}\SCM Workbench.exe"''',
                r'''Name: "{group}\SCM Workbench Web Site"; Filename: "http://www.barrys-emacs.org/scm-workbench/";''',
                #
                #    Add an Emacs icon to the Desktop
                #
                r'''Name: "{commondesktop}\%(APP_NAME)s"; Filename: "{app}\SCM Workbench.exe"; Tasks: "option_desktop_icon"''' % self.wb_version_info,

                #
                #    Add an Emacs icon to the Start menu
                #
                r'''Name: "{commonstartmenu}\%(APP_NAME)s"; Filename: "{app}\SCM Workbench"; Tasks: "option_start_menu_icon"''' % self.wb_version_info,

                ] )

        self.addAllAppFiles()

        #for dll in [dll for dll in os.listdir( 'tmp' ) if dll.lower().endswith( '.dll' )]:
        #    self.all_file_items.append( 'Source: "%s"; DestDir: "{app}"; Flags: ignoreversion' % (dll,) )

        if self.vc_ver == '14.0':
            redist_year = '2015'

        else:
            print( 'Error: Unsupported VC_VER of %s' % (self.vc_ver,) )
            return 1

        if self.arch == 'win64':
            redist_arch = 'x64'
            code_file = os.path.join( self.BUILDER_TOP_DIR, r'Builder\win_code.iss' )
            self.all_setup_items.append( 'ArchitecturesAllowed=x64' )
            self.all_setup_items.append( 'ArchitecturesInstallIn64BitMode=x64' )

        else:
            print( 'Error: Unsupported ARCH of %s' % (self.arch,) )
            return 1

        with open( code_file, 'r' ) as f:
            self.all_code_items.append( f.read() % self.wb_version_info )

        redist_file = 'vcredist_%s_%s.exe' % (redist_arch, redist_year)

        self.log.info( r'Assuming redist files are in K:\subversion' )
        build_utils.copyFile( r'k:\subversion\%s' % (redist_file,), r'tmp\app', 0o700 )

        self.all_file_items.append( 'Source: "%s"; DestDir: {tmp}; Flags: deleteafterinstall' %
                                    (r'app\%s' % (redist_file,)) )
        self.all_run_items.append( r'Filename: {tmp}\%s; Parameters: "/q"; StatusMsg: Installing VC++ %s %s Redistributables...' %
                                    (redist_file, redist_year, self.arch) )

    def addAllAppFiles( self ):
        os.chdir( 'tmp' )
        kitfiles_folder = pathlib.Path( 'app' )

        all_files = []

        for dirpath, all_dirnames, all_filenames in os.walk( str( kitfiles_folder ) ):
            for filename in all_filenames:
                filepath = pathlib.Path( dirpath ) / filename
                filepath = filepath.relative_to( kitfiles_folder )
                if filepath.suffix != '.pyc':
                    all_files.append( filepath )

        for filepath in sorted( all_files ):
            src_path = kitfiles_folder / filepath
            dst_path = pathlib.Path( '{app}' ) / filepath
            self.all_file_items.append( 'Source: "%s"; DestDir: "%s"' % (src_path, dst_path.parent) )

        os.chdir( '..' )

    def generateInnoFile( self ):
        inno_file = r'tmp\scm-workbench.iss'
        self.log.info( 'Generating %s' % (inno_file,) )
        f = open( inno_file, 'w' )

        f.write( ';\n; scm-workbench.iss generate by package_windows_inno_setup_files.py\n;\n' )

        self.__generateSection( f, 'Code', self.all_code_items )
        self.__generateSection( f, 'Setup', self.all_setup_items )
        self.__generateSection( f, 'Tasks', self.all_task_items )
        self.__generateSection( f, 'Files', self.all_file_items )
        self.__generateSection( f, 'Icons', self.all_icon_items )
        self.__generateSection( f, 'Registry', self.all_registry_items )
        self.__generateSection( f, 'Run', self.all_run_items )

        f.close()

    def __generateSection( self, f, name, all_items ):
        if len(all_items) > 0:
            f.write( '\n' )
            f.write( '[%s]\n' % (name,) )
            for item in all_items:
                f.write( item )
                f.write( '\n' )
