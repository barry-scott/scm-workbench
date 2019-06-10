#!/usr/bin/python3
#
#   build_fedora_rpms.py
#
#   cmd - srpm, mock, copr-release, copr-testing
#   --release=auto|<rel>
#   --target=<fedora-version>
#   --arch=<arch>
#   --install
#
import sys
import os
import shutil
import subprocess
import platform
import glob

valid_cmds = ('srpm', 'mock', 'copr-release', 'copr-testing', 'list-release', 'list-testing')

def info( msg ):
    print( '\033[32mInfo:\033[m %s' % (msg,) )

def error( msg ):
    print( '\033[31;1mError:\033[m %s' % (msg,) )

class BuildError(Exception):
    def __init__( self, msg ):
        super().__init__( msg )

class BuildFedoraRpms:
    def __init__( self ):
        self.KITNAME = 'scm-workbench'
        self.cmd = None
        self.release = 'auto'
        self.target = self.fedoraVersion()
        self.arch = platform.machine()
        self.install = False

    def main( self, argv ):
        try:
            self.parseArgs( argv )
            self.setupVars()

            if self.cmd == 'srpm':
                self.buildSrpm()

            elif self.cmd == 'mock':
                self.buildMock()

            elif self.cmd == 'copr-release':
                self.buildCoprRelease()

            elif self.cmd == 'copr-testing':
                self.buildCoprTesting()

            elif self.cmd == 'list-release':
                self.listCoprRelease()

            elif self.cmd == 'list-testing':
                self.listCoprTesting()

            return 0

        except KeyboardInterrupt:
            return 2

        except BuildError as e:
            error( str(e) )
            return 1

    def parseArgs( self, argv ):
        try:
            args = iter( argv )
            next(args)
            self.cmd = next(args)
            if self.cmd not in valid_cmds:
                raise BuildError( 'Invalid cmd %r - pick on of %s' % (cmd, ', '.join( valid_cmds )) )

            while True:
                arg = next(args)
                if arg.startswith('--release='):
                    self.release = arg[len('--release='):]

                elif arg.startswith('--target='):
                    self.target = arg[len('--target='):]

                elif arg.startswith('--arch='):
                    self.arch = arg[len('--arch='):]

                elif arg.startswith('--install'):
                    self.install = True

                else:
                    raise BuildError( 'Unknown option %r' % (arg,) )

        except StopIteration:
            pass

        if self.cmd is None:
            raise BuildError( 'Require a cmd arg' )

    def setupVars( self ):
        self.BUILDER_TOP_DIR = os.environ['BUILDER_TOP_DIR']

        # load the version definitions
        v = {}
        with open( '%s/Builder/version.dat' % (self.BUILDER_TOP_DIR,), 'r' ) as f:
            for line in f:
                line = line.strip()
                if line == '':
                    continue

                if line.startswith( '#' ):
                    continue

                key, value = line.split( '=', 1 )
                v[ key.strip() ] = value.strip()

        self.version = '%s.%s.%s' % (v['major'], v['minor'], v['patch'])

        self.MOCK_ORIG_TARGET_NAME = 'fedora-%d-%s' % (self.target, self.arch)
        self.MOCK_COPR_REPO_FILENAME = '/etc/yum.repos.d/_copr:copr.fedorainfracloud.org:barryascott:tools.repo'
        self.MOCK_TARGET_FILENAME= 'tmp/%s-%s.cfg' % (self.KITNAME, self.MOCK_ORIG_TARGET_NAME)
        self.DISTRO = 'fc%d' % (self.target,)

    def fedoraVersion( self ):
        with open( '/etc/os-release', 'r' ) as f:
            for line in f:
                if line.startswith( 'VERSION_ID=' ):
                    return int( line.strip()[len('VERSION_ID='):] )

        raise BuildError( 'Expected /etc/os-release to have a VERSION_ID= field' )

    def buildSrpm( self ):
        if self.release == 'auto':
            self.release = 1

        self.run( ('rm', '-rf', 'tmp') )
        self.run( ('mkdir', '-p', 'tmp') )

        self.makeTarBall()
        self.ensureMockSetup()
        self.makeSrpm()
        info( 'SRPM is %s' % (self.SRPM_FILENAME,) )

    def buildMock( self ):
        self.buildSrpm()

        info( 'Creating RPM' )
        self.run( ('mock',
                    '--root=%s' % (self.MOCK_TARGET_FILENAME,),
                    '--enablerepo=barryascott-tools',
                    '--rebuild', '--dnf',
                    self.SRPM_FILENAME) )

        ALL_BIN_KITNAMES=[
            self.KITNAME,
            ]

        for BIN_KITNAME in ALL_BIN_KITNAMES:
            basename = '%s-%s-%s.%s.%s.rpm' % (BIN_KITNAME, self.version, self.release, self.DISTRO, 'noarch')
            info( 'Copying %s' % (basename,) )
            shutil.copyfile( '%s/RPMS/%s' % (self.MOCK_BUILD_DIR, basename), 'tmp/%s' % (basename,) )

        info( 'Results in %s/tmp:' % (os.getcwd(),) )
        for filename in os.listdir( 'tmp' ):
            info( 'Kit %s' % (filename,) )

        if self.install:
            info( 'Installing RPMs' )

            for BIN_KITNAME in ALL_BIN_KITNAMES:
                cmd = ('rpm', '-q', BIN_KITNAME)
                p = self.run( cmd, check=False )
                if p.returncode == 0:
                    self.run( ('sudo', 'dnf', '-y', 'remove', BIN_KITNAME) )

            cmd = ['sudo', 'dnf', '-y', 'install']
            cmd.extend( glob.glob( 'tmp/%s*.%s.rpm' % (self.KITNAME, 'noarch') ) )
            self.run( cmd )

    def buildCoprRelease( self ):
        self.buildCopr( 'tools' )

    def buildCoprTesting( self ):
        self.buildCopr( 'tools-testing' )

    def buildCopr( self, copr_repo ):
        if self.release == 'auto':
            p = self.listCopr( copr_repo )
            for line in p.stdout.split('\n'):
                if line.startswith( '%s.src' % (self.KITNAME,) ):
                    parts = line.split()
                    version, rel_distro = parts[1].split('-')
                    release, distro = rel_distro.split('.')

                    if version == self.version and distro == self.DISTRO:
                        self.release = int(release) + 1

                    else:
                        self.release = 1

                    break

        self.buildSrpm()
        self.run( ('copr-cli', 'build', '-r', 'fedora-%s-%s' % (self.target, self.arch), copr_repo, self.SRPM_FILENAME) )

    def listCoprRelease( self ):
        p = self.listCopr( 'tools' )
        print( p.stdout )

    def listCoprTesting( self ):
        p = self.listCopr( 'tools-testing' )
        print( p.stdout )

    def listCopr( self, copr_repo ):
        return self.run( ('dnf', 'list', 'available', '--refresh', '--disablerepo=*', '--enablerepo=barryascott-%s' % (copr_repo,)), output=True )

    def ensureMockSetup( self ):
        info( 'creating mock target file' )
        self.makeMockTargetFile()

        p = self.run( ('mock', '--root=%s' % (self.MOCK_TARGET_FILENAME,), '--print-root-path'), output=True )

        self.MOCK_ROOT = p.stdout.strip()
        self.MOCK_BUILD_DIR = '%s/builddir/build' % (self.MOCK_ROOT,)

        if os.path.exists( self.MOCK_ROOT ):
            info( 'Using existing mock for %s' % (self.MOCK_ORIG_TARGET_NAME,) )

        else:
            info( 'Init mock for %s' % (self.MOCK_TARGET_FILENAME,) )
            self.run( ('mock', '--root=%s' % (self.MOCK_TARGET_FILENAME,), '--init') )

    def makeMockTargetFile( self ):
        with open( '/etc/mock/%s.cfg' % (self.MOCK_ORIG_TARGET_NAME,), 'r' ) as f:
            mock_cfg = compile( f.read(), 'mock_cfg', 'exec' )
            config_opts = {}
            exec( mock_cfg )

        with open( self.MOCK_COPR_REPO_FILENAME, 'r' ) as f:
            repo = f.read()

            config_opts['yum.conf'] += '\n'
            config_opts['yum.conf'] += repo
            config_opts['root'] = os.path.splitext( os.path.basename( self.MOCK_TARGET_FILENAME ) )[0]

        with open( self.MOCK_TARGET_FILENAME, 'w' ) as f:
            for k in config_opts:
                if k == 'yum.conf':
                    print( 'config_opts[\'yum.conf\'] = """', end='', file=f )
                    print( config_opts['yum.conf'], file=f )
                    print( '"""', file=f )

                else:
                    print( 'config_opts[%r] = %r' % (k, config_opts[k]), file=f )

    def makeTarBall( self ):
        self.KIT_BASENAME = '%s-%s' % (self.KITNAME, self.version)

        info( 'Exporting source code' )

        cmd = '(cd ${BUILDER_TOP_DIR}; git archive --format=tar --prefix=%s/ master) | tar xf - -C tmp ' % (self.KIT_BASENAME,)
        self.run( cmd )

        cmd = (os.environ['PYTHON'], '-u',
                '%s/Source/Scm/make_wb_scm_version.py' % (self.BUILDER_TOP_DIR,),
                '%s/Builder/version.dat' % (self.BUILDER_TOP_DIR,),
                'tmp/scm-workbench-%s/Source/Scm//wb_scm_version.py' % (self.version,))
        self.run( cmd )

        self.run( ('tar', 'czf', '%s.tar.gz' % (self.KIT_BASENAME,), self.KIT_BASENAME), cwd='tmp' )

    def makeSrpm( self ):
        info( 'Creating %s.spec' % (self.KITNAME,) )

        with open( '%s.spec.template' % (self.KITNAME,), 'r', encoding='utf-8' ) as f:
            contents = f.read()

        contents = contents.replace( 'SPEC-FILE-VERSION', self.version )
        contents = contents.replace( 'SPEC-FILE-RELEASE', str(self.release) )

        with open( 'tmp/%s.spec' % (self.KITNAME,), 'w', encoding='utf-8' ) as f:
            f.write( contents )

        info( 'Creating SRPM for %s' % (self.KIT_BASENAME,) )

        self.run( ('mock',
                '--root=%s' % (self.MOCK_TARGET_FILENAME,),
                '--buildsrpm', '--dnf',
                '--spec', 'tmp/%s.spec' % (self.KITNAME,),
                '--sources', 'tmp/%s.tar.gz' % (self.KIT_BASENAME,)) )

        SRPM_BASENAME = '%s-%s.%s' % (self.KIT_BASENAME, self.release, self.DISTRO)
        self.SRPM_FILENAME = 'tmp/%s.src.rpm' % (SRPM_BASENAME,)

        src = '%s/SRPMS/%s.src.rpm' % (self.MOCK_BUILD_DIR, SRPM_BASENAME)
        info( 'copy %s %s' % (src, self.SRPM_FILENAME) )
        shutil.copyfile( src, self.SRPM_FILENAME )

    def run( self, cmd, check=True, output=False, cwd=None ):
        kw = {}
        if type(cmd) is str:
            info( 'Running %s' % (cmd,) )
            kw['shell'] = True
        else:
            info( 'Running %s' % (' '.join( cmd ),) )

        if output:
            kw['capture_output'] = True
            kw['encoding'] = 'utf-8'

        if cwd:
            kw['cwd'] = cwd

        p = subprocess.run( cmd, **kw )
        if check and p.returncode != 0:
            raise BuildError( 'Cmd failed %r' % (cmd,) )

        return p

if __name__ == '__main__':
    sys.exit( BuildFedoraRpms().main( sys.argv ) )
