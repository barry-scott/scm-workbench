#!/usr/bin/python3
import sys
import os
import subprocess

class FixInstallRPath:
    def __init__( self ):
        BUILDER_QTDIR = os.environ[ 'BUILDER_QTDIR' ]
        executable_frameworks = '@executable_path/../Frameworks'

        self.all_replacements = [(  ['%s/clang_64/lib' % (BUILDER_QTDIR,)
                                    ,'@loader_path/Qt/lib'
                                    ,'@loader_path/../../lib'],
                                    executable_frameworks)]

    def main( self ):
        cmd = sys.argv[1]
        for filename in sys.argv[2:]:
            if cmd == 'show':
                self.showRPath( filename )

            elif cmd == 'fix':
                self.fixRPath( filename )
                self.showRPath( filename )

        return 0

    def showRPath( self, filename ):
        print( 'Showing RPATH in: %s' % (filename,) )
        for rpath in self.getRPaths( filename ):
            print( '    %s' % (rpath,) )

        print( '  Dylibs:' )
        for name in self.getDylibs( filename ):
            print( '    %s' % (name,) )

    def fixRPath( self, filename ):
        all_rpaths = self.getRPaths( filename )

        all_replacements = []
        print( 'Checking RPATH for', filename )
        for rpath in all_rpaths:
            print( '    Looking at RPATH %s' % (rpath,) )
            for all_orig_rpaths, replacement in self.all_replacements:
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
