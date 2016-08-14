import sys
import time
import os
import datetime
import pathlib

import wb_scm_version

def main( argv ):
    print( 'Info: setup_kit_files.py' )
    inno = InnoSetup( argv )
    return inno.createInnoInstall()

class InnoSetup:
    def __init__( self, argv ):
        self.app_name = "SCM Workbench"
        self.app_id = "SCM Workbench"    # for use in Pascal code
        self.arch = sys.argv[1]
        self.vc_ver = sys.argv[2]

        self.build_time  = time.time()
        self.build_time_str = time.strftime( '%d-%b-%Y %H:%M', time.localtime( self.build_time ) )

        self.year = datetime.datetime.now().year

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
        print( 'Info: Create info_before.txt' )

        f = open( r'setup.tmp\info_before.txt', 'w' )
        f.write(
'''SCM Workbech %(major)d.%(minor)d.%(patch)d commit %(commit)s

After the installation is completed please
see the readme.txt file for changes new in
this kit.

    Barry Scott

    %(date)s
''' %   {'major': wb_scm_version.major
        ,'minor': wb_scm_version.minor
        ,'patch': wb_scm_version.patch
        ,'commit': wb_scm_version.commit
        ,'date': self.build_time_str} )
        f.close()

        print( 'Info: Create setup_copy.cmd' )
        kitname = 'SCM-Workbench-%d.%d.%d-setup.exe' % (wb_scm_version.major, wb_scm_version.minor, wb_scm_version.patch)
        f = open( r'setup.tmp\setup_copy.cmd', 'w' )
        f.write( r'copy setup.tmp\Output\setup.exe %s' '\n' % (kitname,) )
        f.write( r'dir /s /b %s' '\n' % (kitname,) )
        f.close()

        self.all_setup_items.extend( [
                r'''AppName=%(app_name)s''' % self.__dict__,
                r'''AppVerName=%s %d.%d.%d''' % (self.app_name, wb_scm_version.major, wb_scm_version.minor, wb_scm_version.patch),
                r'''AppCopyright=Copyright (C) %s Barry A. Scott''' % (wb_scm_version.copyright_years,),
                r'''DefaultDirName={pf}\Barry Scott\%(app_name)s''' % self.__dict__,
                r'''DefaultGroupName=%(app_name)s''' % self.__dict__,
                r'''UninstallDisplayIcon={app}\%(app_name)s.exe''' % self.__dict__,
                r'''ChangesAssociations=yes''',
                r'''DisableStartupPrompt=yes''',
                r'''InfoBeforeFile=info_before.txt''',
                r'''Compression=bzip/9''',
                ] )

        self.all_task_items.extend( [
                r'''Name: "option_desktop_icon"; Flags: unchecked; Description: "Place %(app_name)s icon on the Desktop"''' % self.__dict__,
                r'''Name: "option_start_menu_icon"; Description: "Place %(app_name)s on the Start menu"''' % self.__dict__,
                ] )

        self.all_icon_items.extend( [
                r'''Name: "{group}\SCM Workbench"; Filename: "{app}\%(app_name)s.exe"''' % self.__dict__,
                r'''Name: "{group}\Web Site"; Filename: "https://github.com/barry-scott/scm-workbench";''',
                #
                #    Add an Emacs icon to the Desktop
                #
                r'''Name: "{commondesktop}\%(app_name)s"; Filename: "{app}\%(app_name)s.exe"; Tasks: "option_desktop_icon"''' % self.__dict__,

                #
                #    Add an Emacs icon to the Start menu
                #
                r'''Name: "{commonstartmenu}\%(app_name)s"; Filename: "{app}\%(app_name)s.exe"; Tasks: "option_start_menu_icon"''' % self.__dict__,

                ] )

        self.all_registry_items.extend( [
                ] )

        self.all_file_items.extend( [
                ] )

        self.addAllKitFiles()

        #for dll in [dll for dll in os.listdir( 'setup.tmp' ) if dll.lower().endswith( '.dll' )]:
        #    self.all_file_items.append( 'Source: "%s"; DestDir: "{app}"; Flags: ignoreversion' % (dll,) )

        if self.vc_ver == '14.0':
            redist_year = '2015'

        else:
            print( 'Error: Unsupported VC_VER of %s' % (self.vc_ver,) )
            return 1

        if self.arch == 'Win64':
            redist_arch = 'x64'
            code_file = 'win64_code.iss'
            self.all_setup_items.append( 'ArchitecturesAllowed=x64' )
            self.all_setup_items.append( 'ArchitecturesInstallIn64BitMode=x64' )

        else:
            print( 'Error: Unsupported ARCH of %s' % (self.arch,) )
            return 1

        f = open( code_file, 'r' )
        self.all_code_items.append( f.read() % self.__dict__ )
        f.close()

        redist_file = 'vcredist_%s_%s.exe' % (redist_arch, redist_year)

        os.system( r'copy k:\subversion\%s setup.tmp' % (redist_file,) )

        self.all_file_items.append( 'Source: "%s"; DestDir: {tmp}; Flags: deleteafterinstall' %
                                    (redist_file,) )
        self.all_run_items.append( r'Filename: {tmp}\%s; Parameters: "/q"; StatusMsg: Installing VC++ %s %s Redistributables...' %
                                    (redist_file, redist_year, self.arch) )

        # finally show the readme.txt
        self.all_run_items.append( r'Filename: "{app}\%(app_name)s.exe"; ' 
                                   r'Flags: nowait postinstall skipifsilent; Description: "Start %(app_name)s"' % self.__dict__ )

    def addAllKitFiles( self ):
        os.chdir( 'setup.tmp' )
        kitfiles_folder = pathlib.Path( r'..\setup.tmp' )

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
        inno_file = r'setup.tmp\scm-workbench.iss'
        print( 'Info: Generating %s' % (inno_file,) )
        f = open( inno_file, 'w' )

        f.write( ';\n; scm-workbench.iss generate by setup_kit_files.py\n;\n' )

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

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )
