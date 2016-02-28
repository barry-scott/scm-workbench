'''
 ====================================================================
 Copyright (c) 2003-2006 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    make_wb_images.py

'''
import sys

data_slice = 32

argv = [
        sys.argv[0],
        'wb_images.py',
	'toolbar_images/add.png',
	'toolbar_images/checkin.png',
	'toolbar_images/delete.png',
	'toolbar_images/diff.png',
	'toolbar_images/edit.png',
	'toolbar_images/editcopy.png',
	'toolbar_images/editcut.png',
	'toolbar_images/editpaste.png',
	'toolbar_images/exclude.png',
	'toolbar_images/file_browser.png',
	'toolbar_images/history.png',
	'toolbar_images/include.png',
	'toolbar_images/info.png',
	'toolbar_images/lock.png',
	'toolbar_images/open.png',
	'toolbar_images/property.png',
	'toolbar_images/revert.png',
	'toolbar_images/terminal.png',
	'toolbar_images/unlock.png',
	'toolbar_images/update.png',
        'toolbar_images/flatview.png',
        'toolbar_images/onlychanges.png',
	'wb.png',
        ]

def main( argv ):
    f = open( argv[1], 'w' )
    f.write( header )
    for filename in argv[2:]:
        f.write( 'images_by_filename["%s"] = (\n' % filename )
        i = open( filename, 'rb' )
        data = i.read()
        i.close()

        for offset in range( 0, len(data), data_slice ):
            f.write( '    %r\n' % data[offset:offset+data_slice] )
        f.write( '    )\n' )
    f.write( footer )
    f.close()

header = '''
import wx
import cStringIO

def getBitmap( name, size=None ):
    return wx.BitmapFromImage( getImage( name, size ) )

def getImage( name, size=None ):
    stream = cStringIO.StringIO( images_by_filename[ name ] )
    image = wx.ImageFromStream( stream )
    if size is not None:
        w, h = size
        if image.GetWidth() != w or image.GetHeight() != h:
            image.Rescale( w, h )
    return image

def getIcon( name, size=None ):
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap( getBitmap( name, size ) )
    return icon

images_by_filename = {}
'''

footer = '''
'''

if __name__ == '__main__':
    sys.exit( main( argv ) )
