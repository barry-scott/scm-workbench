#
#   progress.py
#
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

count = 0
total = 10


def main():
    app = QtWidgets.QApplication( ['fred'] )

    prog = QtWidgets.QProgressBar()
    prog.setMinimum( 0 )
    prog.setMaximum( total )
    prog.setTextVisible( False )
    prog.setMinimumHeight( 50 )

    prog.show()

    layout = QtWidgets.QHBoxLayout( prog )
    label = QtWidgets.QLabel()

    layout.addWidget( label )
    layout.setContentsMargins( 20, 0, 0, 0 )

    def inc():
        print( 'inc' )
        global count
        if count == total:
            timer.stop()

        else:
            count += 1
            prog.setValue( count )

    def setProgresLabel( self ):
        label.setText( '%3d%%' % (100 * count / total) )

    prog.valueChanged.connect( setProgresLabel )

    timer = QtCore.QTimer()
    timer.setInterval( 250 )
    timer.timeout.connect( inc )
    timer.start()

    app.exec_()

main()
