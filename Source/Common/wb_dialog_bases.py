'''
 ====================================================================
 Copyright (c) 2016-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_dialog_base.py

'''
import urllib.parse
import pathlib

from PyQt6 import QtWidgets
from PyQt6 import QtCore

class WbDialog(QtWidgets.QDialog):
    def __init__( self, parent=None, cancel=True ):
        super().__init__( parent )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( QtWidgets.QDialogButtonBox.StandardButton.Ok )
        if cancel:
            self.buttons.addButton( QtWidgets.QDialogButtonBox.StandardButton.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.grid_layout = WbFeedbackGridLayout()

        self.setLayout( self.grid_layout )

        # Often the rest of init has to be done after the widgets are rendered
        # for example to set focus on a widget
        self.__timer_init = QtCore.QTimer()
        self.__timer_init.timeout.connect( self.__completeInit )
        self.__timer_init.setSingleShot( True )
        self.__timer_init.start( 0 )

    def isValid( self ):
        return self.grid_layout.isValid()

    def __completeInit( self ):
        self.__timer_init = None
        self.completeInit()

    def completeInit( self ):
        pass

    def addNamedDivider( self, name ):
        self.grid_layout.addNamedDivider( name )

    def addRow( self, label, value, min_width=None ):
        self.grid_layout.addRow( label, value, min_width=min_width )

    def addFeedbackWidget( self ):
        self.grid_layout.addFeedbackWidget()

    def addButtons( self ):
        self.grid_layout.addButtons( self.buttons )

class WbTabbedDialog(QtWidgets.QDialog):
    def __init__( self, parent=None, size=None ):
        super().__init__( parent )

        self.tabs = QtWidgets.QTabWidget()

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( QtWidgets.QDialogButtonBox.StandardButton.Ok )
        self.buttons.addButton( QtWidgets.QDialogButtonBox.StandardButton.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        # must add the tabs at this stage or that will not display
        self.completeTabsInit()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.tabs )
        self.layout.addWidget( self.buttons )

        self.setLayout( self.layout )

        if size is not None:
            em, ex = self.app.defaultFontEmEx( 'm' )
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

        self.grid_layout = WbGridLayout()

        self.setLayout( self.grid_layout )

    def name( self ):
        return self.__name

    def __lt__( self, other ):
        return self.name() < other.name()

    def addNamedDivider( self, name ):
        self.grid_layout.addNamedDivider( name )

    def addRow( self, label, value, button=None, min_width=None ):
        self.grid_layout.addRow( label, value, button=button, min_width=min_width )

class WbGridLayout(QtWidgets.QGridLayout):
    def __init__( self ):
        super().__init__()

        self.setAlignment( QtCore.Qt.AlignmentFlag.AlignTop )
        self.setColumnStretch( 1, 2 )

    def addNamedDivider( self, name ):
        if not isinstance( name, QtWidgets.QWidget ):
            name = QtWidgets.QLabel( '<b>%s</b>' % (name,) )

        self.addWidget( name, self.rowCount(), 0, 1, 2 )

    def addRow( self, label, value, button=None, min_width=None ):
        if label is not None and not isinstance( label, QtWidgets.QWidget ):
            label = QtWidgets.QLabel( label )

        if not isinstance( value, QtWidgets.QWidget ):
            value = QtWidgets.QLineEdit( str(value) )
            value.setReadOnly( True )

        if min_width is not None:
            value.setMinimumWidth( min_width )

        row = self.rowCount()

        if label is not None:
            self.addWidget( label, row, 0 )
            col_start = 1
            col_span = 1

        else:
            col_start = 0
            col_span = 2

        if button is None:
            self.addWidget( value, row, col_start, 1, col_span )

        else:
            self.addWidget( value, row, 1 )
            self.addWidget( button, row, 2 )

    def addButtons( self, buttons ):
        self.addWidget( buttons, self.rowCount(), 0, 1, 2 )

class WbFeedbackGridLayout(WbGridLayout):
    def __init__( self ):
        super().__init__()

        self.feedback = WbFeedbackPlainTextEdit()

    def addFeedbackWidget( self ):
        self.addRow( '', self.feedback )

    #
    #   check validity of all widgets in the grid 2nd column
    #   and set the feedback to the first widget to provide feedback
    #
    def isValid( self ):
        valid = True
        feedback_set = False
        self.feedback.setPlainText( '' )

        for row in range( self.rowCount() ):
            widget_item = self.itemAtPosition( row, 1 )
            if widget_item is None:
                continue
            widget = widget_item.widget()
            if widget is not None and hasattr( widget, 'isValid' ):
                if not widget.isValid():
                    valid = False

                if not feedback_set:
                    message = widget.getFeedback()
                    if message is not None:
                        self.feedback.setPlainText( message )
                        feedback_set = True

        return valid

class WbValidateLineEditValue:
    def __init__( self ):
        self.feedback_message = None
        self.line_edit_ctrl = None

    def setLineEditCtrl( self, line_edit_ctrl ):
        self.line_edit_ctrl = line_edit_ctrl

    def setFeedback( self, message=None ):
        self.feedback_message = message

    def getFeedback( self ):
        return self.feedback_message

    def isValid( self ):
        raise NotImplementedError( 'isValid' )

class WbValidateUnique(WbValidateLineEditValue):
    def __init__( self, all_existing_values, empty_message ):
        super().__init__()

        self.all_existing_values = all_existing_values
        self.empty_message = empty_message

    def isValid( self ):
        self.setFeedback( None )
        value = self.line_edit_ctrl.compareValue()
        if value == '':
            self.setFeedback( self.empty_message )
            return False

        if value not in self.all_existing_values:
            return True

        else:
            self.setFeedback( self.empty_message )
            return False

class WbValidateUrl(WbValidateLineEditValue):
    def __init__( self, all_supported_schemes, empty_message ):
        super().__init__()

        self.empty_message = empty_message
        self.all_supported_schemes = all_supported_schemes

    def isValid( self ):
        self.setFeedback( None )

        # disabled controls are treated as valid
        if not self.line_edit_ctrl.isEnabled():
            return True

        url = self.line_edit_ctrl.value()
        if ':' not in url or '/' not in url:
            self.setFeedback( self.empty_message )
            return False

        result = urllib.parse.urlparse( url )
        scheme = result.scheme.lower()
        if scheme not in self.all_supported_schemes:
            self.setFeedback(
                    T_('Scheme %(scheme)s is not supported. Use one of %(all_supported_schemes)s') %
                        {'scheme': scheme
                        ,'all_supported_schemes': ', '.join( self.all_supported_schemes )} )
            return False

        if result.netloc == '' or result.path == '':
            self.setFeedback( self.empty_message )
            return False

        return True

class WbValidateUserName(WbValidateLineEditValue):
    def __init__( self, empty_message ):
        super().__init__()

        self.empty_message = empty_message

    def isValid( self ):
        self.setFeedback( None )

        # disabled controls are treated as valid
        if not self.line_edit_ctrl.isEnabled():
            return True

        username =  self.line_edit_ctrl.value()
        if username == '':
            self.setFeedback( self.empty_message )
            return False

        return True

class WbValidateUserEmail(WbValidateLineEditValue):
    def __init__( self, empty_message ):
        super().__init__()

        self.empty_message = empty_message

    def isValid( self ):
        self.setFeedback( None )

        # disabled controls are treated as valid
        if not self.line_edit_ctrl.isEnabled():
            return True

        email = self.line_edit_ctrl.compareValue()
        if email == '':
            self.setFeedback( self.empty_message )
            return False

        if email.count( '@' ) != 1:
            self.setFeedback( self.empty_message )
            return False

        user, domain = email.split( '@' )
        if user == '' or domain == '':
            return False

        return True

class WbValidateNewFolder(WbValidateLineEditValue):
    # T_('Fill in the project folder')
    def __init__( self, empty_message ):
        super().__init__()

        self.empty_message = empty_message

    def isValid( self ):
        self.setFeedback( None )

        path =  self.line_edit_ctrl.value()
        if path == '':
            self.setFeedback( self.empty_message )
            return False

        path = pathlib.Path( path )

        if path.exists():
            self.setFeedback( T_('%s already exists pick another folder name') % (path,) )
            return False

        else:
            if path.parent.exists():
                self.setFeedback( T_('%s will be created') % (path,) )
                return True

            else:
                self.setFeedback( T_('%s cannot be used as it does not exist') % (path.parent,) )
                return False

class WbLineEdit(QtWidgets.QLineEdit):
    def __init__( self, value, case_blind=False, strip=True, validator=None ):
        super().__init__( value )
        self.strip = strip
        self.case_blind = case_blind
        self.validator = validator
        if self.validator is not None:
            self.validator.setLineEditCtrl( self )

        if strip:
            value = value.strip()

        if case_blind:
            value = value.lower()

        self.initial_value = value

        self.setProperty( 'valid', True )

    def initialValue( self ):
        return self.initial_value

    # value that is used for has changed tests
    def compareValue( self ):
        if self.case_blind:
            return self.value().lower()
        else:
            return self.value()

    # value that is saved in preferences etc
    def value( self ):
        if self.strip:
            return self.text().strip()
        else:
            return self.text()

    def hasChanged( self ):
        return self.initial_value != self.compareValue()

    def setEnabled( self, enable ):
        super().setEnabled( enable )

        # update the valid state
        if not enable:
            self._setValidState( True )

    def getFeedback( self ):
        if self.validator is not None:
            return self.validator.getFeedback()

        else:
            return None

    def isValid( self ):
        if self.validator is None or not self.isEnabled():
            return self._setValidState( True )

        else:
            return self._setValidState( self.validator.isValid() )

    def _setValidState( self, valid ):
        self.setProperty( 'valid', valid )

        # force the stylesheet to be reapplied
        style = self.style()
        style.unpolish( self )
        style.polish( self )

        return valid

class WbCheckBox(QtWidgets.QCheckBox):
    def __init__( self, title, value ):
        super().__init__( title )
        self.setChecked( value )

        self.initial_value = value

    def hasChanged( self ):
        return self.initial_value != self.isChecked()

#
#   combine a WbCheckBox and WbLineEdit into a single control
#   [X] [line-edit]
#
#   implement the hasChanged(), value() and isChecked() methods
#
class WbCheckBoxLineEdit(QtWidgets.QWidget):
    def __init__( self, enabled, value, case_blind=False, strip=True, validator=None ):
        super().__init__()

        self.checkbox_ctrl = WbCheckBox( '', enabled )

        self.line_edit_ctrl = WbLineEdit( value, case_blind, strip, validator )
        self.line_edit_ctrl.setEnabled( enabled )

        layout = QtWidgets.QHBoxLayout()
        self.setLayout( layout )

        layout.addWidget( self.checkbox_ctrl )
        layout.addWidget( self.line_edit_ctrl )

        self.checkbox_ctrl.stateChanged.connect( self.line_edit_ctrl.setEnabled )

    def changedConnect( self, func ):
        self.checkbox_ctrl.stateChanged.connect( func )
        self.line_edit_ctrl.textChanged.connect( func )

    def isValid( self ):
        return self.line_edit_ctrl.isValid()

    def getFeedback( self ):
        return self.line_edit_ctrl.getFeedback()

    def hasChanged( self ):
        if self.checkbox_ctrl.hasChanged():
            return True

        if self.checkbox_ctrl.isChecked():
            return self.line_edit_ctrl.hasChanged()

        return False

    def value( self ):
        return self.line_edit_ctrl.value()

    def isChecked( self ):
        return self.checkbox_ctrl.isChecked()

#------------------------------------------------------------
class WbFeedbackPlainTextEdit(QtWidgets.QPlainTextEdit):
    def __init__( self, value='' ):
        super().__init__( value )

        self.setObjectName( 'feedback' )
        self.setReadOnly( True )
        line_spacing = self.fontMetrics().lineSpacing()
        # why do we need 4 times for 2 lines?
        self.setMinimumHeight( 4*line_spacing )
        self.setMaximumHeight( 4*line_spacing )
