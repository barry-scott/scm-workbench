'''
 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_properties_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtCore

def warningMessage( name ):
    #QQQ: need a parent?
    box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Information,
            T_('Warning'),
            T_('Enter a value for %s') % (name,),
            QtWidgets.QMessageBox.Close,
            parent=None )
    box.exec_()


class SingleProperty:
    def __init__( self, dialog, name, present ):
        self.dialog = dialog
        self.name = name
        self.was_present = present
        self.starting_value = ''
        self.value_ctrl = None

        self.checkbox = QtWidgets.QCheckBox( name )
        self.checkbox.setCheckState( QtCore.Qt.Checked if present else QtCore.Qt.Unchecked )

    def setValueCtrl( self, value_ctrl, value ):
        self.starting_value = value
        self.value_ctrl = value_ctrl

        self.value_ctrl.setEnabled( self.was_present )

        self.dialog.addRow( self.checkbox, self.value_ctrl )

        self.checkbox.stateChanged.connect( self.value_ctrl.setEnabled )

    def isValid( self ):
        return True

    def isModified( self ):
        if self.was_present ^ self.isPresent():
            return True

        return self.isPresent() and self.starting_value != self.getValue()

    def isPresent( self ):
        return self.checkbox.checkState() == QtCore.Qt.Checked

    def getName( self ):
        return self.name

    def getValue( self ):
        return ''

class SinglePropertyText(SingleProperty):
    def __init__( self, dialog, name, present, value ):
        super().__init__( dialog, name, present )

        value_ctrl = QtWidgets.QLineEdit()
        value_ctrl.setText( value )
        self.setValueCtrl( value_ctrl, value )

    def isValid( self ):
        if not self.isPresent():
            return True

        text = self.value_ctrl.text()
        if text.strip() == '':
            warningMessage( self.name )
            return False

        return True

    def getValue( self ):
        return self.value_ctrl.text()

class SinglePropertyMultiLine(SingleProperty):
    def __init__( self, dialog, name, present, value ):
        super().__init__( dialog, name, present )

        value_ctrl = QtWidgets.QPlainTextEdit()
        value_ctrl.setPlainText( value )
        value_ctrl.setMinimumWidth( 400 )
        value_ctrl.setMinimumHeight( 200 )

        self.setValueCtrl( value_ctrl, value )

    def isValid( self ):
        if not self.isPresent():
            return True

        text = self.value_ctrl.toPlainText()
        if text.strip() == '':
            warningMessage( self.name )
            return False

        return True

    def getValue( self ):
        return self.value_ctrl.toPlainText()

class SinglePropertyChoice(SingleProperty):
    def __init__( self, dialog, name, present, value, all_choices ):
        super().__init__( dialog, name, present )

        value_ctrl = QtWidgets.QComboBox()
        value_ctrl.addItems( all_choices )

        if self.was_present:
            value_ctrl.setCurrentText( value )

        else:
            value_ctrl.setCurrentIndex( 0 )

        self.setValueCtrl( value_ctrl, value )

    def getValue( self ):
        return self.value_ctrl.toPlainText()

class SinglePropertyNoValue(SingleProperty):
    def __init__( self, dialog, name, present ):
        super().__init__( dialog, name, present )

        self.setValueCtrl( QtWidgets.QLabel( '' ), '' )

class PropertiesDialogBase(QtWidgets.QDialog):
    def __init__( self, app, parent, path, prop_dict ):
        super().__init__( parent )

        self.path = path
        self.prop_dict = prop_dict

        self.grid = QtWidgets.QGridLayout()
        self.grid.setColumnStretch( 1, 1 )

        self.property_ctrls = {}

        self.initKnownProperties()

        for prop in sorted( self.prop_dict ):
            if( prop not in self.known_properties_names
            and prop not in self.ignore_properties_names ):
                self.property_ctrls[ prop ] = SinglePropertyText( self, prop, True, self.prop_dict[ prop ] )

        self.new_name_ctrl  = QtWidgets.QLineEdit( '' )
        self.new_value_ctrl = QtWidgets.QLineEdit( '' )

        self.addRow( self.new_name_ctrl, self.new_value_ctrl )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.grid.addWidget( self.buttons, self.grid.rowCount(), 0, 2, 1 )

        self.setLayout( self.grid )

    def addRow( self, checkbox, value_ctrl ):
        row = self.grid.rowCount()

        self.grid.addWidget( checkbox, row, 0 )
        self.grid.addWidget( value_ctrl, row, 1 )

    def accept( self ):
        for prop_ctrl in self.property_ctrls.values():
            if not prop_ctrl.isValid():
                return

        super().accept()

    def getModifiedProperties( self ):
        modified_properties = []
        for prop_ctrl in self.property_ctrls.values():
            if prop_ctrl.isModified():
                modified_properties.append(
                    (prop_ctrl.isPresent()
                    ,prop_ctrl.getName()
                    ,prop_ctrl.getValue()) )

        new_name = self.new_name_ctrl.text()
        new_value = self.new_value_ctrl.text()

        if new_name.strip() != '':
            modified_properties.append( (True, new_name.strip(), new_value.strip()) )

        return modified_properties

class FilePropertiesDialog(PropertiesDialogBase):
    def __init__( self, app, parent, path, prop_dict ):
        self.known_properties_names = set( ['svn:eol-style'
                                           ,'svn:executable'
                                           ,'svn:mime-type'
                                           ,'svn:needs-lock'
                                           ,'svn:keywords'
                                           ,'svn:special'] )
        self.ignore_properties_names = set( ['svn:mergeinfo'] )

        super().__init__( app, parent, path, prop_dict )

    def initKnownProperties( self ):
        prop = 'svn:needs-lock'
        self.property_ctrls[ prop ] = SinglePropertyNoValue( self, prop, prop in self.prop_dict )

        prop = 'svn:executable'
        self.property_ctrls[ prop ] = SinglePropertyNoValue( self, prop, prop in self.prop_dict )

        # special is managed by SVN only the user must not change it
        prop = 'svn:special'
        self.property_ctrls[ prop ] = SinglePropertyNoValue( self, prop, prop in self.prop_dict )
        self.property_ctrls[ prop ].checkbox.setEnabled( False )

        prop = 'svn:eol-style'
        self.property_ctrls[ prop ] = SinglePropertyChoice( self, prop, prop in self.prop_dict,
                                        self.prop_dict.get( prop, 'native' ), ['native','CRLF','LF','CR'] )
        prop = 'svn:mime-type'
        self.property_ctrls[ prop ] = SinglePropertyText( self, prop, prop in self.prop_dict,
                                        self.prop_dict.get( prop, '' ) )

        prop = 'svn:keywords'
        self.property_ctrls[ prop ] = SinglePropertyText( self, prop, prop in self.prop_dict,
                                        self.prop_dict.get( prop, '' ) )

class FolderPropertiesDialog(PropertiesDialogBase):
    def __init__( self, app, parent, path, prop_dict ):
        self.known_properties_names = set( ['svn:ignore', 'svn:externals', 'svn:global-ignores'] )
        self.ignore_properties_names = set( ['svn:mergeinfo'] )

        super().__init__( app, parent, path, prop_dict )

    def initKnownProperties( self ):
        prop = 'svn:global-ignores'
        self.property_ctrls[ prop ] = SinglePropertyMultiLine( self, prop, prop in self.prop_dict,
                                        self.prop_dict.get( prop, '' ) )
        prop = 'svn:ignore'
        self.property_ctrls[ prop ] = SinglePropertyMultiLine( self, prop, prop in self.prop_dict,
                                        self.prop_dict.get( prop, '' ) )
        prop = 'svn:externals'
        self.property_ctrls[ prop ] = SinglePropertyMultiLine( self, prop, prop in self.prop_dict,
                                        self.prop_dict.get( prop, '' ) )
