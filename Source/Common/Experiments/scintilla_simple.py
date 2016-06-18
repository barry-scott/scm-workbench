import wb_scintilla
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

app =QtWidgets.QApplication( sys.argv )

scintilla = wb_scintilla.WbScintilla( None )
for name in sorted( dir(scintilla) ):
    if name[0] != '_':
        print( name )

scintilla.insertText( 0, 'line 1\n' )
scintilla.insertText( len('line 1\n'), 'line 2\n' )


scintilla.show()
app.exec_()
