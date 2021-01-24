import sys
import time
import os
import datetime
import pathlib

import brand_version

import build_log
log = build_log.BuildLog()
log.setColour( True )

def main( argv ):
    log.info( argv[0] )
    inno = InnoSetup( argv[1], argv[2] )
    return inno.createInnoInstall()

class InnoSetup:
    def __init__( self, arch, vc_ver ):
        self.app_name = "SCM Workbench"
        self.app_id = "SCM Workbench"    # for use in Pascal code
        self.arch = arch
        self.vc_ver = vc_ver

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
        log.info( 'Create info_before.txt' )

        BUILDER_TOP_DIR = os.environ['BUILDER_TOP_DIR']
        vi = brand_version.VersionInfo( BUILDER_TOP_DIR, print )
        vi.parseVersionInfo( os.path.join( BUILDER_TOP_DIR, 'Builder/version_info.txt' ) )

        version = vi.get('version')

        f = open( r'tmp\info_before.txt', 'w' )
        f.write(
'''SCM Workbench %(version)s for %(arch)s

After the installation is completed please
see the readme.txt file for changes new in
this kit.

    Barry Scott

    %(date)s
''' %   {'version': version
        ,'arch': self.arch
        ,'date': self.build_time_str} )
        f.close()

        self.all_setup_items.extend( [
                r'''AppName=%(app_name)s''' % self.__dict__,
                r'''AppVerName=SCM Workbench %s''' % (version,),
                r'''AppCopyright=Copyright (C) 1980-%s Barry A. Scott''' % (self.year,),
                r'''DefaultDirName={pf}\Barry Scott\%(app_name)s''' % self.__dict__,
                r'''DefaultGroupName=%(app_name)s''' % self.__dict__,
                r'''UninstallDisplayIcon={app}\bemacs.exe''',
                r'''ChangesAssociations=yes''',
                r'''DisableStartupPrompt=yes''',
                r'''InfoBeforeFile=info_before.txt''',
                r'''Compression=bzip/9''',
                ] )

        self.all_task_items.extend( [
                r'''Name: "option_desktop_icon"; Flags: unchecked; Description: "Place %(app_name)s icon on the Desktop"''' % self.__dict__,
                r'''Name: "option_start_menu_icon"; Description: "Place %(app_name)s on the Start menu"''' % self.__dict__,
                r'''Name: "option_edit_with_bemacs"; Description: "Place Edit with %(app_name)s on the Context menu"''' % self.__dict__,
                ] )

        self.all_icon_items.extend( [
                r'''Name: "{group}\SCM Workbench"; Filename: "{app}\scm workbench.exe"''',
                r'''Name: "{group}\Documentation"; Filename: "{app}\Documentation\emacs-documentation.html"''',
                r'''Name: "{group}\FAQ"; Filename: "{app}\documentation\bemacs-faq.html"''',
                r'''Name: "{group}\Readme"; Filename: "{app}\bemacs.exe"; Parameters: """{app}\readme.txt"""''',
                r'''Name: "{group}\SCM Workbench Web Site"; Filename: "http://www.barrys-emacs.org/scm-workbench/";''',
                #
                #    Add an Emacs icon to the Desktop
                #
                r'''Name: "{commondesktop}\%(app_name)s"; Filename: "{app}\bemacs.exe"; Tasks: "option_desktop_icon"''' % self.__dict__,

                #
                #    Add an Emacs icon to the Start menu
                #
                r'''Name: "{commonstartmenu}\%(app_name)s"; Filename: "{app}\bemacs.exe"; Tasks: "option_start_menu_icon"''' % self.__dict__,

                ] )


        self.all_file_items.extend( [
                r'''Source: "%s\Kits\Readme.txt"; DestDir: "{app}";''' % (BUILDER_TOP_DIR,),

                r'''Source: "%s\Editor\PyQtBEmacs\bemacs.png";  DestDir: "{app}\Documentation";''' % (BUILDER_TOP_DIR,),
                r'''Source: "%s\HTML\*.css";  DestDir: "{app}\Documentation";''' % (BUILDER_TOP_DIR,),
                r'''Source: "%s\HTML\*.html"; DestDir: "{app}\Documentation";''' % (BUILDER_TOP_DIR,),
                r'''Source: "%s\HTML\*.gif";  DestDir: "{app}\Documentation";''' % (BUILDER_TOP_DIR,),
                r'''Source: "%s\HTML\*.js";   DestDir: "{app}\Documentation";''' % (BUILDER_TOP_DIR,),
                ] )

        self.addAllKitFiles()

        #for dll in [dll for dll in os.listdir( 'tmp' ) if dll.lower().endswith( '.dll' )]:
        #    self.all_file_items.append( 'Source: "%s"; DestDir: "{app}"; Flags: ignoreversion' % (dll,) )

        if self.vc_ver == '14.0':
            redist_year = '2015'

        else:
            print( 'Error: Unsupported VC_VER of %s' % (self.vc_ver,) )
            return 1

        if self.arch == 'win64':
            redist_arch = 'x64'
            code_file = os.path.join( BUILDER_TOP_DIR, 'Kits/Windows/bemacs_win64_code.iss' )
            self.all_setup_items.append( 'ArchitecturesAllowed=x64' )
            self.all_setup_items.append( 'ArchitecturesInstallIn64BitMode=x64' )

        else:
            print( 'Error: Unsupported ARCH of %s' % (self.arch,) )
            return 1

        f = open( code_file, 'r' )
        self.all_code_items.append( f.read() % self.__dict__ )
        f.close()

        redist_file = 'vcredist_%s_%s.exe' % (redist_arch, redist_year)

        log.info( r'QQQ assuming K:\subversion is a thing' )
        os.system( r'copy k:\subversion\%s tmp' % (redist_file,) )

        self.all_file_items.append( 'Source: "%s"; DestDir: {tmp}; Flags: deleteafterinstall' %
                                    (redist_file,) )
        self.all_run_items.append( r'Filename: {tmp}\%s; Parameters: "/q"; StatusMsg: Installing VC++ %s %s Redistributables...' %
                                    (redist_file, redist_year, self.arch) )

        # finally show the readme.txt
        self.all_run_items.append( r'Filename: "{app}\bemacs.exe"; Parameters: """{app}\readme.txt"""; '
                                        r'Flags: nowait postinstall skipifsilent; Description: "View README.TXT"' )

    def addAllKitFiles( self ):
        os.chdir( 'tmp' )
        kitfiles_folder = pathlib.Path( 'kitfiles' )

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
        inno_file = r'tmp\bemacs.iss'
        log.info( 'Generating %s' % (inno_file,) )
        f = open( inno_file, 'w' )

        f.write( ';\n; bemacs.iss generate by setup_kit_files.py\n;\n' )

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
