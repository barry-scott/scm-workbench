import sys

from PyQt5 import QtWidgets
from PyQt5 import QtCore

app = QtWidgets.QApplication(sys.argv)

palette = app.palette()

def colorAsString( brush ):
    color = brush.color()
    grey = (color.red()/256. * 0.3) + (color.green()/256. * 0.59) + (color.blue()/256. * 0.11)
    return '%3d,%3d,%3d,%3d %f' % (color.red(), color.green(), color.blue(), color.alpha(), grey)

for arg in ('text', 'window', 'windowText', 'base', 'alternateBase', 'highlight', 'highlightedText'):
    print( '%20s: %r' % (arg, colorAsString( getattr( palette, arg )() )) )
