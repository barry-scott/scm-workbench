#
#   getfont.py   
#
import sys

from PyQt6 import QtWidgets
from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6 import Qt

app = QtWidgets.QApplication( sys.argv )

print( 'Python %r' % (sys.version_info,) )
print( 'PyQt %s, Qt %s' % (Qt.PYQT_VERSION_STR, QtCore.QT_VERSION_STR) )

code_face = 'Monaco'
code_point_size = 13


print( 'QQQ code_face %r code_point_size %r' % (code_face, code_point_size) )
font = QtGui.QFont( code_face, code_point_size )
print( 'QQQ FontTab.onSelectFontCode() font in %r %r %r' % (font, font.family(), font.pointSize()) )
r = QtWidgets.QFontDialog.getFont( font, None, 'Choose code font', QtWidgets.QFontDialog.FontDialogOption.MonospacedFonts )

print( 'QQQ ok %r' % (r,) )

font, ok = r
print( 'QQQ FontTab.onSelectFontCode() font out %r %r %r' % (font, font.family(), font.pointSize()) )

if ok:
    code_face = font.family()
    code_point_size = font.pointSize()

    print( 'QQQ code_face = %r %r' % (font.family(), font.pointSize()) )
