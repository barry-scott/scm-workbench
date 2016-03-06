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
        'wb_git_images.py',

	'wb.png',

	'toolbar_images/editcopy.png',
	'toolbar_images/editcut.png',
	'toolbar_images/editpaste.png',

	'toolbar_images/terminal.png',
	'toolbar_images/file_browser.png',

	'toolbar_images/edit.png',
	'toolbar_images/open.png',

	'toolbar_images/include.png',
	'toolbar_images/exclude.png',

	'toolbar_images/revert.png',

	'toolbar_images/diff.png',
	'toolbar_images/history.png',

        ]

def main( argv ):
    with open( argv[1], 'w' ) as f:
        f.write( header )

        for filename in argv[2:]:
            f.write( 'images_by_filename["%s"] = (\n' % (filename,) )
            with open( filename, 'rb' ) as image:
                data = image.read()

            for offset in range( 0, len(data), data_slice ):
                f.write( '    %r\n' % data[offset:offset+data_slice] )
            f.write( '    )\n' )

        f.write( footer )

header = '''
from PyQt5 import QtGui

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
'''

if __name__ == '__main__':
    sys.exit( main( argv ) )
