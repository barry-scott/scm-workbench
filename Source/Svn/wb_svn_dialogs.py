'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtCore

import wb_dialog_bases
import pysvn

class WbSvnDepthWidget(QtWidgets.QComboBox):
    def __init__( self, parent=None, include_empty=True, default=pysvn.depth.empty ):
        super().__init__( parent )

        self.setEditable( False )

        self.all_depths = []
        if include_empty:
            self.all_depths.append( (pysvn.depth.empty,  T_('Empty - only the FOLDER')) )

        self.all_depths.append( (pysvn.depth.files,      T_('Files - the folder and its files')) )
        self.all_depths.append( (pysvn.depth.immediates, T_('Immediates - the folder and its immediate file and folders')) )
        self.all_depths.append( (pysvn.depth.infinity,   T_('Infinity - the folder and all files and folders within it')) )

        default_index = None

        for depth, text in self.all_depths:
            if depth == default:
                default_index = self.count()

            self.addItem( text )

        assert default_index is not None, 'default is not a known depth: %r' % (default,)

        self.setCurrentIndex( default_index )

    def getDepth( self ):
        return self.all_depths[ self.currentIndex() ][0]

class WbAddFolderDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, folder_name ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Add Folder') )

        self.depth = WbSvnDepthWidget( include_empty=True, default=pysvn.depth.empty )

        self.force = QtWidgets.QCheckBox( T_('force files to be added') )
        self.force.setCheckState( QtCore.Qt.CheckState.Unchecked )

        self.addRow( T_('Folder'), folder_name )
        self.addRow( T_('Depth'), self.depth )
        self.addRow( T_('Force'), self.force )
        self.addButtons()

    def getDepth( self ):
        return self.depth.getDepth()

    def getForce( self ):
        return self.force.checkState() == QtCore.Qt.CheckState.Checked

class WbRevertFolderDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, folder ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Revert Folder') )

        self.depth = WbSvnDepthWidget( include_empty=False, default=pysvn.depth.infinity )

        self.addRow( T_('Folder'), folder )
        self.addRow( T_('Depth'), self.depth )
        self.addButtons()

    def getDepth( self ):
        return self.depth.getDepth()

class WbLockFileDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Lock files') )

        self.details = QtWidgets.QPlainTextEdit( '' )
        self.message = QtWidgets.QPlainTextEdit( '' )

        self.force = QtWidgets.QCheckBox( T_('force files to be locked') )
        self.force.setCheckState( QtCore.Qt.CheckState.Unchecked )

        em = self.fontMetrics().width( 'M' )

        self.addNamedDivider( 'Files to Lock' )
        self.addRow( None, self.details, min_width=60*em )
        self.addNamedDivider( 'Lock Message' )
        self.addRow( None, self.message )
        self.addRow( T_('Force'), self.force )
        self.addButtons()

    def setAllFilenames( self, all_filenames ):
        self.details.setPlainText( '\n'.join( str(f) for f in all_filenames ) )

    def getMessage( self ):
        return self.message.toPlainText()

    def getForce( self ):
        return self.force.checkState() == QtCore.Qt.CheckState.Checked

class WbUnlockFileDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('UnLock files') )

        self.details = QtWidgets.QPlainTextEdit( '' )
        self.force = QtWidgets.QCheckBox( T_('force files to be unlocked') )
        self.force.setCheckState( QtCore.Qt.CheckState.Unchecked )

        em = self.fontMetrics().width( 'M' )

        self.addNamedDivider( 'Files to Unlock' )
        self.addRow( None, self.details, min_width=60*em )
        self.addRow( T_('Force'), self.force )
        self.addButtons()

    def setAllFilenames( self, all_filenames ):
        self.details.setPlainText( '\n'.join( str(f) for f in all_filenames ) )

    def getForce( self ):
        return self.force.checkState() == QtCore.Qt.CheckState.Checked
