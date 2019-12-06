import sys

from PyQt5 import QtWidgets
from PyQt5 import QtCore

app = QtWidgets.QApplication(sys.argv)

#app.setStyle('fusion')

palette = app.palette()

print( 'desktopSettingsAware: %r' % (app.desktopSettingsAware(),) )

def colorAsString( brush ):
    color = brush.color()
    grey = (color.redF() * 0.3) + (color.greenF() * 0.59) + (color.blueF() * 0.11)
    return '%.2f,%.2f,%.2f,%.2f %.2f %.2f' % (color.redF(), color.greenF(), color.blueF(), color.alphaF(), grey, color.lightnessF())

for arg in ('text', 'window', 'windowText', 'base', 'alternateBase', 'highlight', 'highlightedText'):
    print( '%20s: %r' % (arg, colorAsString( getattr( palette, arg )() ), ) )
