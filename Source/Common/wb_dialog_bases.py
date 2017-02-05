'''
 ====================================================================
 Copyright (c) 2016-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_common_dialogs.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

class WbDialog(QtWidgets.QDialog):
    def __init__( self, parent=None ):
        super().__init__( parent )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setAlignment( QtCore.Qt.AlignTop )

        self.setLayout( self.grid_layout )

        # Often the rest of init has to be done after the widgets are rendered
        # for example to set focus on a widget
        self.__timer_init = QtCore.QTimer()
        self.__timer_init.timeout.connect( self.__completeInit )
        self.__timer_init.setSingleShot( True )
        self.__timer_init.start( 0 )

    def __completeInit( self ):
        self.__timer_init = None
        self.completeInit()

    def completeInit( self ):
        pass

    def addNamedDivider( self, name ):
        if not isinstance( name, QtWidgets.QWidget ):
            name = QtWidgets.QLabel( '<b>%s</b>' % (name,) )

        row = self.nextRow()

        self.grid_layout.addWidget( name, row, 0, 1, 2 )

    def addRow( self, label, value, min_width=None ):
        if not isinstance( label, QtWidgets.QWidget ):
            label = QtWidgets.QLabel( label )

        if not isinstance( value, QtWidgets.QWidget ):
            value = QtWidgets.QLineEdit( str(value) )
            value.setReadOnly( True )

        if min_width is not None:
            value.setMinimumWidth( min_width )

        row = self.nextRow()

        self.grid_layout.addWidget( label, row, 0 )
        self.grid_layout.addWidget( value, row, 1 )

    def addButtons( self ):
        self.grid_layout.addWidget( self.buttons, self.nextRow(), 0, 1, 2 )

    def nextRow( self ):
        return self.grid_layout.rowCount()

class WbTabbedDialog(QtWidgets.QDialog):
    def __init__( self, parent=None, size=None ):
        super().__init__( parent )

        self.tabs = QtWidgets.QTabWidget()

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        # must add the tabs at this stage or that will not display
        self.completeTabsInit()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.tabs )
        self.layout.addWidget( self.buttons )

        self.setLayout( self.layout )

        if size is not None:
            em = self.app.fontMetrics().width( 'm' )
            ex = self.app.fontMetrics().lineSpacing()
            self.resize( size[0]*em, size[1]*ex )

    def completeTabsInit( self ):
        raise NotImplementedError( 'completeTabsInit required'  )

    def addTab( self, tab ):
        self.tabs.addTab( tab, tab.name() )

#
#   WbTabBase supports 3 columns
#       lable, value, button
#   if button is not require value stretched in the 3rd column
#
class WbTabBase(QtWidgets.QWidget):
    def __init__( self, app, name ):
        super().__init__()

        self.app = app
        self.__name = name

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setAlignment( QtCore.Qt.AlignTop )
        self.grid_layout.setColumnStretch( 1, 2 )

        self.setLayout( self.grid_layout )

    def name( self ):
        return self.__name

    def __lt__( self, other ):
        return self.name() < other.name()

    def addNamedDivider( self, name ):
        if not isinstance( name, QtWidgets.QWidget ):
            name = QtWidgets.QLabel( '<b>%s</b>' % (name,) )

        row = self.nextRow()

        self.grid_layout.addWidget( name, row, 0, 1, 3 )

    def addRow( self, label, value, button=None, min_width=None ):
        if not isinstance( label, QtWidgets.QWidget ):
            label = QtWidgets.QLabel( label )

        if not isinstance( value, QtWidgets.QWidget ):
            value = QtWidgets.QLineEdit( str(value) )
            value.setReadOnly( True )

        if min_width is not None:
            value.setMinimumWidth( min_width )

        row = self.nextRow()

        self.grid_layout.addWidget( label, row, 0 )
        if button is None:
            self.grid_layout.addWidget( value, row, 1, 1, 2 )

        else:
            self.grid_layout.addWidget( value, row, 1 )
            self.grid_layout.addWidget( button, row, 2 )

    def nextRow( self ):
        return self.grid_layout.rowCount()

class WbLineEdit(QtWidgets.QLineEdit):
    def __init__( self, value, case_blind=False, strip=True ):
        super().__init__( value )
        self.strip = strip
        self.case_blind = case_blind

        if strip:
            value = value.strip()
        if case_blind:
            value = value.lower()

        self.initial_value = value

    def hasChanged( self ):
        value = self.text()
        if self.strip:
            value = value.strip()
        if self.case_blind:
            value = value.lower()

        return self.initial_value != value

class WbCheckBox(QtWidgets.QCheckBox):
    def __init__( self, title, value ):
        super().__init__( title )
        self.setChecked( value )

        self.initial_value = value

    def hasChanged( self ):
        return self.initial_value != self.isChecked()
