'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_commit_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_main_window
import wb_tracked_qwidget

import wb_scm_table_view
import wb_scm_images

class WbGitCommitDialog(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    commitAccepted = QtCore.pyqtSignal()
    commitClosed = QtCore.pyqtSignal()

    def __init__( self, app, git_project ):
        self.app = app
        self.git_project = git_project

        super().__init__( app, wb_scm_images, app._debugDiff )
        wb_tracked_qwidget.WbTrackedModeless.__init__( self )

        self.setWindowTitle( T_('Commit %s') % (git_project.projectName(),) )
        self.setWindowIcon( wb_scm_images.getQIcon( 'wb.png' ) )

        # on Qt on macOS table will trigger selectionChanged that needs tree_model
        self.table_view = wb_scm_table_view.WbScmTableView( self.app, self )

        self.filter_text = QtWidgets.QLineEdit()
        self.filter_text.setClearButtonEnabled( True )
        self.filter_text.setMaxLength( 256 )
        self.filter_text.setPlaceholderText( T_('Filter  by name') )

        self.filter_text.textChanged.connect( self.table_view.table_sortfilter.setFilterText )

        self.h_filter_layout = QtWidgets.QHBoxLayout()
        self.h_filter_widget = QtWidgets.QWidget()
        self.h_filter_widget.setLayout( self.h_filter_layout )

        row = 0
        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Filter:') ), 0 )
        self.h_filter_layout.addWidget( self.filter_text, 1 )

        self.v_table_layout = QtWidgets.QVBoxLayout()
        self.v_table_layout.addWidget( self.h_filter_widget )
        self.v_table_layout.addWidget( self.table_view )

        self.v_table_widget = QtWidgets.QWidget()
        self.v_table_widget.setLayout( self.v_table_layout )

        self.label_message = QtWidgets.QLabel( T_('Commit Log Message') )
        self.message = QtWidgets.QPlainTextEdit( '' )

        self.v_message_layout = QtWidgets.QVBoxLayout()
        self.v_message_layout.addWidget( self.label_message )
        self.v_message_layout.addWidget( self.message )
        self.v_message_widget = QtWidgets.QWidget()
        self.v_message_widget.setLayout( self.v_message_layout )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        # ----------------------------------------
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )
        self.v_split.addWidget( self.v_table_widget )
        self.v_split.addWidget( self.v_message_widget )

        # ----------------------------------------
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.v_split )
        self.layout.addWidget( self.buttons )

        # ----------------------------------------
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout( self.layout )

        self.setCentralWidget( self.widget )

        self.resize( 800, 600 )

        self.ok_button.setEnabled( False )

        # connections
        self.buttons.accepted.connect( self.handleAccepted )
        self.buttons.rejected.connect( self.close )

        self.message.textChanged.connect( self.enableOkButton )

        # set focus
        self.message.setFocus()

        self.updateTableView()

    def closeEvent( self, event ):
        super().closeEvent( event )

        self.commitClosed.emit()

    def handleAccepted( self ):
        self.commitAccepted.emit()

    def enableOkButton( self ):
        text = self.message.toPlainText()
        self.ok_button.setEnabled( text.strip() != '' )

    def getMessage( self ):
        return self.message.toPlainText().strip()

    def updateTableView( self ):
        # call will have updated the git project state already
        self.table_view.setScmProjectTreeNode( self.git_project.flat_tree )

    def updateActionEnabledStates( self ):
        print( 'qqq WbGitCommitDialog.updateActionEnabledStates' )
