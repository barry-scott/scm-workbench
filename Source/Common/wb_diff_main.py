'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_diff_main.py

'''
VERSION_STRING = "Uncontrolled"

import sys

import wb_main
import wb_app

import wb_diff_side_by_side_view
import wb_platform_specific
import wb_debug
import wb_preferences
import wb_diff_images

import xml_preferences

def noTranslation( msg ):
    return msg

def noPluralTranslation( singlar, plural, n ):
    if n == 1:
        return singlar

    else:
        return plural

import builtins
# T_( 'non plural' )
builtins.__dict__['T_'] = noTranslation
# S_( 'singular', 'plural', n )
builtins.__dict__['S_'] = noPluralTranslation
# U_( 'static string' )
# already setup in wb_main

class WbDiff_App(wb_app.WbApp):
    def __init__( self, argv ):
        self.debugLogDiffEnabled = True

        self.log = self
        self.file1 = None
        self.file2 = None
        self.size = (1000, 800)

        super().__init__( ('Wb', 'Diff'), argv, wb_debug.WbDebug )

        if len(self.all_positional_args) != 2:
            print( 'Error: expecting 2 filename arguments' )
            sys.exit( 1 )

        # self is log and app
        self.main_window.resize( *self.size )

    def optionParse( self, args ):
        if args[1].startswith('--size='):
            size = args[1][len('--size='):]
            try:
                size = [int(x.strip()) for x in size.split(',')]
                if len(size) != 2:
                    raise ValueError('must be two')
            except ValueError:
                print( 'Error: expecting --size=<width>,<height>' )
                sys.exit( 1 )

            width, height = size

            if( width < 200 or width > 3840
            or height < 200 or height > 2100 ):
                print( 'Error: width between 200 and 3840, height between 200 and 2100' )
                sys.exit( 1 )

            self.size = (width, height)
            del args[ 1 ]
            return True

        return False

    def getAppQIcon( self ):
        wb_diff_images.getQIcon( 'wb.png' )

    def createPreferencesManager( self ):
        return PreferencesManager(
                    self.log,
                    wb_platform_specific.getPreferencesFilename() )

    def createMainWindow( self ):
        if len(self.all_positional_args) == 2:
            self.file1 = self.all_positional_args[0]
            self.file2 = self.all_positional_args[1]

        else:
            self.file1 = '/dev/null'
            self.file2 = '/dev/null'

        return wb_diff_side_by_side_view.DiffSideBySideView( self, None, 'wb-diff', self.file1, self.file1, self.file2, self.file2 )


preferences_scheme = (
    xml_preferences.Scheme(
        wb_preferences.scheme_nodes
    )
)


class PreferencesManager(wb_preferences.PreferencesManager):
    def __init__( self, log, filename ):
        super().__init__( log, filename, preferences_scheme, wb_preferences.Preferences )

def createDiffApp( argv ):
    return WbDiff_App( argv )

if __name__ == '__main__':
    sys.exit( wb_main.main( createDiffApp, sys.argv ) )
