#!/usr/bin/python3
'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_date.py

'''
#
#   pytz using pkg_resource but pkg_resource is not working
#   from py2app built application for macOS.
#
#   This hack works around the problem.
#
import datetime
import zoneinfo
import tzlocal

try:
    # implicit import of tzdata to make sure its included by packaging tools
    import tzdata

except ImportError:
    pass


def utcDatetime( timestamp ):
    return datetime.datetime.fromtimestamp( timestamp, datetime.timezone.utc )

def localDatetime( datetime_or_timestamp ):
    if type(datetime_or_timestamp) in (int, float):
        dt = utcDatetime( datetime_or_timestamp )
    else:
        dt = datetime_or_timestamp

    local_timezone = zoneinfo.ZoneInfo( tzlocal.get_localzone_name() )
    local_dt = dt.astimezone( local_timezone )
    return local_dt

if __name__ == '__main__':
    import time

    t = time.time()

    utc = utcDatetime( t )
    print( '   UTC: repr %r' % (utc,) )
    print( '   UTC:  str %s' % (utc,) )

    local = localDatetime( utc )
    print( 'Local1: repr %r' % (local,) )
    print( 'Local1:  str %s' % (local,) )

    local = localDatetime( t )
    print( 'Local2: repr %r' % (local,) )
    print( 'Local2:  str %s' % (local,) )
