#!/usr/bin/python3
import sys
import os
import subprocess
import re

class FixInstallRPath:
    def __init__( self ):
        executable_frameworks = '@executable_path/../Frameworks'

        self.all_rpath_replacements = [
            (   ['/Library/Frameworks/Python.framework/Versions/%(PYVER)s/lib/python%(PYVER)s/site-packages/pysvn' %
                        {'PYVER': '%d.%d' % (sys.version_info.major, sys.version_info.minor)}],
                executable_frameworks),
            ]

        self.all_dylib_replacements = [
            ('/usr/local/svn.*/lib/(lib.*)', '@loader_path/\\1'),
            ('/Library/Frameworks/Python.framework/Versions/%(PYVER)s/lib/python%(PYVER)s/site-packages/pysvn/(lib.*)' %
                    {'PYVER': '%d.%d' % (sys.version_info.major, sys.version_info.minor)}, '@executable_path/../Frameworks/\\1'),
            ]

    def main( self ):
        cmd = sys.argv[1]
        for filename in sys.argv[2:]:
            if cmd == 'show':
                self.showPaths( filename, system_files=False )

            if cmd == 'show-all':
                self.showPath( filename, system_files=True )

            elif cmd == 'fix':
                self.fixRPath( filename )
                self.fixDynlibPath( filename )
                self.showPaths( filename, system_files=False )

        return 0

    def showPaths( self, filename, system_files ):
        print( 'Showing RPATH in: %s' % (filename,) )
        for rpath in self.getRPaths( filename ):
            print( '    %s' % (rpath,) )

        print( '  Dylibs:' )
        num_system_files = 0

        for name in self.getDylibs( filename ):
            if not system_files:
                if( name.startswith( '/usr/lib/' )
                or name.startswith( '/System/Library' ) ):
                    num_system_files += 1
                    continue

            print( '    %s' % (name,) )
        if not system_files:
            print( '    (%d system library files ellided)' % (num_system_files,) )

    def fixRPath( self, filename ):
        all_rpaths = self.getRPaths( filename )

        all_replacements = []
        print( 'Checking RPATH for %s' % (filename,) )
        for rpath in all_rpaths:
            print( '    Looking at RPATH %s' % (rpath,) )
            for all_orig_rpaths, replacement in self.all_rpath_replacements:
                all_replacements.append( replacement )
                for orig in all_orig_rpaths:
                    if rpath == orig:
                        print( '    Need to replace %s with %s' % (rpath, replacement) )
                        subprocess.run( ['install_name_tool', '-rpath', rpath, replacement, filename], check=True )

        all_rpaths = self.getRPaths( filename )
        for rpath in all_rpaths:
            if rpath not in all_replacements:
                print( '    Delete unused rpath %s' % (rpath,) )
                subprocess.run( ['install_name_tool', '-delete_rpath', rpath, filename], check=True )

    def fixDynlibPath( self, filename ):
        all_dylibs = self.getDylibs( filename )
        print( 'Checking DYLIB for %s' % (filename,) )
        for dylib in all_dylibs:
            for pattern, replacement in self.all_dylib_replacements:
                all_matches = re.match( pattern, dylib )
                if all_matches is not None:
                    new_path = all_matches.expand( replacement )
                    print( '    Replacing %s' % (dylib,) )
                    print( '         With %s' % (new_path,) )
                    subprocess.run( ['install_name_tool', '-change', dylib, new_path, filename], check=True )

    ST_IDLE = 0
    ST_RPATH = 1
    ST_DYNLIB = 2

    def getRPaths( self, filename ):
        all_rpaths = []
        res = subprocess.run( ['otool', '-l', filename], stdout=subprocess.PIPE, universal_newlines=True )
        state = self.ST_IDLE
        for line in res.stdout.split('\n'):
            words = line.strip().split()
            if state == self.ST_IDLE:
                if words == ['cmd','LC_RPATH']:
                    state = self.ST_RPATH

            elif state == self.ST_RPATH:
                if words[0:1] == ['path']:
                    path = words[1]
                    all_rpaths.append( path )
                    state = self.ST_IDLE

        return all_rpaths

    def getDylibs( self, filename ):
        all_dylibs = []
        res = subprocess.run( ['otool', '-l', filename], stdout=subprocess.PIPE, universal_newlines=True )
        state = self.ST_IDLE
        for line in res.stdout.split('\n'):
            words = line.strip().split()
            if state == self.ST_IDLE:
                if words == ['cmd','LC_LOAD_DYLIB']:
                    state = self.ST_DYNLIB

            elif state == self.ST_DYNLIB:
                if words[0:1] == ['name']:
                    path = words[1]
                    all_dylibs.append( path )
                    state = self.ST_IDLE

        return all_dylibs

if __name__ == '__main__':
    sys.exit( FixInstallRPath().main() )
