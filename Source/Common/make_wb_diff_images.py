#!/usr/bin/env python3
'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    make_wb_images.py

'''
import sys

data_slice = 32

argv = [
        sys.argv[0],
        'wb_diff_images.py',

        '../wb.png',

        '../toolbar_images/blank.png',

        '../toolbar_images/include.png',
        '../toolbar_images/exclude.png',
        ]

def main( argv ):
    with open( argv[1], 'w' ) as f:
        f.write( header )

        for filename in argv[2:]:
            if filename.startswith( '../' ):
                image_name = filename[len('../'):]
            else:
                image_name = filename

            f.write( 'images_by_filename["%s"] = (\n' % (image_name,) )
            with open( filename, 'rb' ) as image:
                data = image.read()

            for offset in range( 0, len(data), data_slice ):
                f.write( '    %r\n' % data[offset:offset+data_slice] )
            f.write( '    )\n' )

        f.write( footer )

header = '''# made by make_wb_diff_image.py
#pylint disable=too-many-lines

from PyQt6 import QtGui

def getQImage( name ):
    image = QtGui.QImage()
    image.loadFromData( images_by_filename[ name ] )
    return image

def getQPixmap( name ):
    return QtGui.QPixmap( getQImage( name ) )

def getQIcon( name ):
    return QtGui.QIcon( getQPixmap( name ) )

images_by_filename = {}
'''

footer = '''
# end
'''

if __name__ == '__main__':
    sys.exit( main( argv ) )
