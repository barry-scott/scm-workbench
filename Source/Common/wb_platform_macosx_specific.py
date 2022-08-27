'''

 ====================================================================
 Copyright (c) 2004-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_macosx_specific.py

'''
import os
import pathlib
import zoneinfo

__all__ = ('setupPlatformSpecific', 'getAppDir', 'getPreferencesDir'
          ,'getLocalePath', 'getDocUserGuide', 'getNullDevice'
          ,'getHomeFolder', 'getDefaultExecutableFolder', 'isInvalidFilename'
          ,'getTimezoneName')

__all_name_parts = None
app_dir = None

def setupPlatformSpecific( all_name_parts, argv0 ):
    #pylint disable=global-statement
    global __all_name_parts
    __all_name_parts = all_name_parts

    global app_dir

    if argv0.startswith( '/' ):
        app_dir = pathlib.Path( argv0 ).parent.parent / 'Resources'

    elif '/' in argv0:
        app_dir = pathlib.Path( argv0 ).resolve().parent

    else:
        for folder in [pathlib.Path( p.strip() ) for p in ['.'] + os.environ.get( 'PATH', '' ).split( ':' )]:
            app_path = (folder / argv0).resolve()
            if app_path.exists():
                app_dir = app_path.parent
                break

    assert app_dir is not None

def getAppDir():
    assert app_dir is not None, 'call setupPlatformSpecific_() first'
    return app_dir

def getPreferencesDir():
    name = '-'.join( [part.lower() for part in __all_name_parts] )
    folder = 'Library/Preferences/org.barrys-emacs.%s' % (name,)

    return getHomeFolder() / folder

def getLocalePath():
    return pathlib.Path( os.environ.get( 'PYTHONHOME', getAppDir() ) ) / 'locale'

def getDocUserGuide():
    return app_dir / 'Documentation/scm-workbench.html'

def getNullDevice():
    return pathlib.Path( '/dev/null' )

def getHomeFolder():
    return pathlib.Path( os.environ['HOME'] )

def getDefaultExecutableFolder():
    return pathlib.Path( '/usr/bin' )

__filename_bad_chars_set = set( '/\000' )
def isInvalidFilename( filename ):
    name_set = set( filename )

    if len( name_set.intersection( __filename_bad_chars_set ) ) != 0:
        return True

    return False

def getTimezoneName():
    if 'TZ' in os.environ:
        try:
            zone_name = os.environ['TZ']
            zoneinfo.ZoneInfo( zone_name )
            return zone_name

        except zoneinfo.ZoneInfoNotFoundError:
            pass

    tz_path = os.path.join( '/etc/localtime' )

    if os.path.exists( tz_path ) and os.path.islink( tz_path ):
        tz_parts = os.path.realpath( tz_path ).split( '/' )
        # see if the last two parts are know then try the last part
        for num_parts in range( 2, 0, -1 ):
            try:
                zone_name = '/'.join( tz_parts[-num_parts:] )
                zoneinfo.ZoneInfo( zone_name )
                return zone_name

            except zoneinfo.ZoneInfoNotFoundError:
                pass

    else:
        return 'UTC'

