import wb_scintilla
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

app =QtWidgets.QApplication( sys.argv )

class MySintilla(wb_scintilla.WbScintilla):
    def __init__( self ):
        super().__init__( None )

    def keyPressEvent( self, event ):
        if event.text() == 'Q':
            self.close()

        else:
            super().keyPressEvent( event )

scintilla = MySintilla()

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

scintilla.setReadOnly( True )

scintilla.show()
app.exec_()
