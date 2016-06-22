import wb_scintilla
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

app =QtWidgets.QApplication( sys.argv )

scintilla = wb_scintilla.WbScintilla( None )

if False:
    for name in sorted( dir(scintilla) ):
        if name[0] != '_':
            print( name )

scintilla.insertText( 0, 'line one is here\n' )
scintilla.insertText( len('line one is here\n'), 'line Two is here\n' )

scintilla.indicSetStyle( 0, scintilla.INDIC_STRIKE )
scintilla.setIndicatorValue( 0 )
scintilla.indicatorFillRange( 5, 4 )

scintilla.resize( 400, 300 )
scintilla.show()
app.exec_()
