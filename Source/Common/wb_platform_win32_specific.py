'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_win32_specific.py

'''
import os
import pathlib
import zoneinfo
import winreg

import ctypes
import ctypes.wintypes

__all__ = ('setupPlatformSpecific', 'getAppDir', 'getPreferencesDir'
          ,'getLocalePath', 'getDocUserGuide', 'getNullDevice'
          ,'getHomeFolder', 'getDefaultExecutableFolder', 'isInvalidFilename'
          ,'getTimezoneName')

CSIDL_APPDATA = 0x1a        # Application Data
CSIDL_WINDOWS = 0x24        # windows folder
CSIDL_PROGRAM_FILES = 0x26  # program files folder

SHGFP_TYPE_CURRENT = 0  # Want current, not default value
SHGFP_TYPE_DEFAULT = 1

app_dir = None

__all_name_parts = None

def setupPlatformSpecific( all_name_parts, argv0 ):
    global __all_name_parts
    __all_name_parts = all_name_parts

    global app_dir

    if argv0[1:3] ==':\\':
        app_dir = pathlib.Path( argv0 ).parent

    elif '\\' in argv0:
        app_dir = pathlib.Path( argv0 ).resolve().parent

    else:
        for folder in [os.getcwd()] + [p.strip() for p in os.environ.get( 'PATH', '' ).split( ';' )]:
            app_path = pathlib.Path( folder ) / argv0
            if app_path.exists():
                app_dir = app_path.parent
                break

def getAppDir():
    assert app_dir is not None, 'call setupPlatformSpecific() first'
    return app_dir

def getPreferencesDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_APPDATA, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getWindowsDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_WINDOWS, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getProgramFilesDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_PROGRAM_FILES, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getLocalePath():
    return getAppDir() / 'locale'

def getDocUserGuide():
    return app_dir / 'Documentation' / 'scm-workbench.html'

def getNullDevice():
    return pathlib.Path( 'NUL' )

def getHomeFolder():
    return pathlib.Path( os.environ['USERPROFILE'] )

def getDefaultExecutableFolder():
    return getProgramFilesDir()

__filename_bad_chars_set = set( '\\:/\000?<>*|"' )
__filename_reserved_names = set( ['nul', 'con', 'aux', 'prn',
    'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
    'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
    ] )

def isInvalidFilename( filename ):
    name_set = set( filename )

    if len( name_set.intersection( __filename_bad_chars_set ) ) != 0:
        return True

    name = filename.split( '.' )[0]
    if name.lower() in __filename_reserved_names:
        return True

    return False

def getTimezoneName():
    h = winreg.ConnectRegistry( None, winreg.HKEY_LOCAL_MACHINE )

    key = r'SYSTEM\CurrentControlSet\Control\TimeZoneInformation'
    tz_key = winreg.OpenKey( h, key )

    tz_info = {}
    for index in range( winreg.QueryInfoKey( tz_key )[1] ):
        key, value, _ = winreg.EnumValue( tz_key, index )
        tz_info[ key ] = value

    tz_key.Close()

    try:
        windows_tz_name = tz_info[ 'TimeZoneKeyName' ]
        return windows_tz_to_unix_tz_name[ windows_tz_name ]

    except KeyError:
        return 'UTC'

windows_tz_to_unix_tz_name = {
    'AUS Central Standard Time':        'Australia/Darwin',
    'AUS Eastern Standard Time':        'Australia/Sydney',
    'Afghanistan Standard Time':        'Asia/Kabul',
    'Alaskan Standard Time':            'America/Anchorage',
    'Aleutian Standard Time':           'America/Adak',
    'Altai Standard Time':              'Asia/Barnaul',
    'Arab Standard Time':               'Asia/Riyadh',
    'Arabian Standard Time':            'Asia/Dubai',
    'Arabic Standard Time':             'Asia/Baghdad',
    'Argentina Standard Time':          'America/Buenos_Aires',
    'Astrakhan Standard Time':          'Europe/Astrakhan',
    'Atlantic Standard Time':           'America/Halifax',
    'Aus Central W. Standard Time':     'Australia/Eucla',
    'Azerbaijan Standard Time':         'Asia/Baku',
    'Azores Standard Time':             'Atlantic/Azores',
    'Bahia Standard Time':              'America/Bahia',
    'Bangladesh Standard Time':         'Asia/Dhaka',
    'Belarus Standard Time':            'Europe/Minsk',
    'Bougainville Standard Time':       'Pacific/Bougainville',
    'Canada Central Standard Time':     'America/Regina',
    'Cape Verde Standard Time':         'Atlantic/Cape_Verde',
    'Caucasus Standard Time':           'Asia/Yerevan',
    'Cen. Australia Standard Time':     'Australia/Adelaide',
    'Central America Standard Time':    'America/Guatemala',
    'Central Asia Standard Time':       'Asia/Almaty',
    'Central Brazilian Standard Time':  'America/Cuiaba',
    'Central Europe Standard Time':     'Europe/Budapest',
    'Central European Standard Time':   'Europe/Warsaw',
    'Central Pacific Standard Time':    'Pacific/Guadalcanal',
    'Central Standard Time':            'America/Chicago',
    'Central Standard Time (Mexico)':   'America/Mexico_City',
    'Chatham Islands Standard Time':    'Pacific/Chatham',
    'China Standard Time':              'Asia/Shanghai',
    'Cuba Standard Time':               'America/Havana',
    'Dateline Standard Time':           'Etc/GMT+12',
    'E. Africa Standard Time':          'Africa/Nairobi',
    'E. Australia Standard Time':       'Australia/Brisbane',
    'E. Europe Standard Time':          'Europe/Chisinau',
    'E. South America Standard Time':   'America/Sao_Paulo',
    'Easter Island Standard Time':      'Pacific/Easter',
    'Eastern Standard Time':            'America/New_York',
    'Eastern Standard Time (Mexico)':   'America/Cancun',
    'Egypt Standard Time':              'Africa/Cairo',
    'Ekaterinburg Standard Time':       'Asia/Yekaterinburg',
    'FLE Standard Time':                'Europe/Kiev',
    'Fiji Standard Time':               'Pacific/Fiji',
    'GMT Standard Time':                'Europe/London',
    'GTB Standard Time':                'Europe/Bucharest',
    'Georgian Standard Time':           'Asia/Tbilisi',
    'Greenland Standard Time':          'America/Godthab',
    'Greenwich Standard Time':          'Atlantic/Reykjavik',
    'Haiti Standard Time':              'America/Port-au-Prince',
    'Hawaiian Standard Time':           'Pacific/Honolulu',
    'India Standard Time':              'Asia/Calcutta',
    'Iran Standard Time':               'Asia/Tehran',
    'Israel Standard Time':             'Asia/Jerusalem',
    'Jordan Standard Time':             'Asia/Amman',
    'Kaliningrad Standard Time':        'Europe/Kaliningrad',
    'Korea Standard Time':              'Asia/Seoul',
    'Libya Standard Time':              'Africa/Tripoli',
    'Line Islands Standard Time':       'Pacific/Kiritimati',
    'Lord Howe Standard Time':          'Australia/Lord_Howe',
    'Magadan Standard Time':            'Asia/Magadan',
    'Magallanes Standard Time':         'America/Punta_Arenas',
    'Marquesas Standard Time':          'Pacific/Marquesas',
    'Mauritius Standard Time':          'Indian/Mauritius',
    'Middle East Standard Time':        'Asia/Beirut',
    'Montevideo Standard Time':         'America/Montevideo',
    'Morocco Standard Time':            'Africa/Casablanca',
    'Mountain Standard Time':           'America/Denver',
    'Mountain Standard Time (Mexico)':  'America/Chihuahua',
    'Myanmar Standard Time':            'Asia/Rangoon',
    'N. Central Asia Standard Time':    'Asia/Novosibirsk',
    'Namibia Standard Time':            'Africa/Windhoek',
    'Nepal Standard Time':              'Asia/Katmandu',
    'New Zealand Standard Time':        'Pacific/Auckland',
    'Newfoundland Standard Time':       'America/St_Johns',
    'Norfolk Standard Time':            'Pacific/Norfolk',
    'North Asia East Standard Time':    'Asia/Irkutsk',
    'North Asia Standard Time':         'Asia/Krasnoyarsk',
    'North Korea Standard Time':        'Asia/Pyongyang',
    'Omsk Standard Time':               'Asia/Omsk',
    'Pacific SA Standard Time':         'America/Santiago',
    'Pacific Standard Time':            'America/Los_Angeles',
    'Pacific Standard Time (Mexico)':   'America/Tijuana',
    'Pakistan Standard Time':           'Asia/Karachi',
    'Paraguay Standard Time':           'America/Asuncion',
    'Qyzylorda Standard Time':          'Asia/Qyzylorda',
    'Romance Standard Time':            'Europe/Paris',
    'Russia Time Zone 10':              'Asia/Srednekolymsk',
    'Russia Time Zone 11':              'Asia/Kamchatka',
    'Russia Time Zone 3':               'Europe/Samara',
    'Russian Standard Time':            'Europe/Moscow',
    'SA Eastern Standard Time':         'America/Cayenne',
    'SA Pacific Standard Time':         'America/Bogota',
    'SA Western Standard Time':         'America/La_Paz',
    'SE Asia Standard Time':            'Asia/Bangkok',
    'Saint Pierre Standard Time':       'America/Miquelon',
    'Sakhalin Standard Time':           'Asia/Sakhalin',
    'Samoa Standard Time':              'Pacific/Apia',
    'Sao Tome Standard Time':           'Africa/Sao_Tome',
    'Saratov Standard Time':            'Europe/Saratov',
    'Singapore Standard Time':          'Asia/Singapore',
    'South Africa Standard Time':       'Africa/Johannesburg',
    'South Sudan Standard Time':        'Africa/Juba',
    'Sri Lanka Standard Time':          'Asia/Colombo',
    'Sudan Standard Time':              'Africa/Khartoum',
    'Syria Standard Time':              'Asia/Damascus',
    'Taipei Standard Time':             'Asia/Taipei',
    'Tasmania Standard Time':           'Australia/Hobart',
    'Tocantins Standard Time':          'America/Araguaina',
    'Tokyo Standard Time':              'Asia/Tokyo',
    'Tomsk Standard Time':              'Asia/Tomsk',
    'Tonga Standard Time':              'Pacific/Tongatapu',
    'Transbaikal Standard Time':        'Asia/Chita',
    'Turkey Standard Time':             'Europe/Istanbul',
    'Turks And Caicos Standard Time':   'America/Grand_Turk',
    'US Eastern Standard Time':         'America/Indianapolis',
    'US Mountain Standard Time':        'America/Phoenix',
    'UTC':                              'Etc/UTC',
    'UTC+12':                           'Etc/GMT-12',
    'UTC+13':                           'Etc/GMT-13',
    'UTC-02':                           'Etc/GMT+2',
    'UTC-08':                           'Etc/GMT+8',
    'UTC-09':                           'Etc/GMT+9',
    'UTC-11':                           'Etc/GMT+11',
    'Ulaanbaatar Standard Time':        'Asia/Ulaanbaatar',
    'Venezuela Standard Time':          'America/Caracas',
    'Vladivostok Standard Time':        'Asia/Vladivostok',
    'Volgograd Standard Time':          'Europe/Volgograd',
    'W. Australia Standard Time':       'Australia/Perth',
    'W. Central Africa Standard Time':  'Africa/Lagos',
    'W. Europe Standard Time':          'Europe/Berlin',
    'W. Mongolia Standard Time':        'Asia/Hovd',
    'West Asia Standard Time':          'Asia/Tashkent',
    'West Bank Standard Time':          'Asia/Hebron',
    'West Pacific Standard Time':       'Pacific/Port_Moresby',
    'Yakutsk Standard Time':            'Asia/Yakutsk',
    'Yukon Standard Time':              'America/Whitehorse'
    }

if __name__ == '__main__':
    print( getPreferencesDir() )
