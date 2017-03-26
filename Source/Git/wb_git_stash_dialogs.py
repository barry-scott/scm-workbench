'''
 ====================================================================
 Copyright (c) 2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_stash_dialogs.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_table_view

def U_( s: str ) -> str:
    return s

class WbGitStashPick(QtWidgets.QDialog):
    def __init__( self, app, main_window, all_stashes ):
        super().__init__( main_window )

        self.app = app
        self.stash_id = None

        em = self.fontMetrics().width( 'M' )
        self.resize( 70*em, 30*em )

        self.setWindowTitle( T_('Git Stash list - %s') % (' '.join( app.app_name_parts ),) )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.ok_button.setText( T_('Stash Pop') )
        self.buttons.addButton( self.buttons.Cancel )

        self.stashes_model = WbGitStashesModel( app )
        self.stashes_model.loadStashInfo( all_stashes )

        self.stashes_table = WbStashesTableView( self, main_window, self.stashes_model )
        self.stashes_table.setSelectionBehavior( self.stashes_table.SelectRows )
        self.stashes_table.setSelectionMode( self.stashes_table.SingleSelection )

        self.vert_layout = QtWidgets.QVBoxLayout()

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.vert_layout.addWidget( self.stashes_table )
        self.vert_layout.addWidget( self.buttons )

        self.setLayout( self.vert_layout )

    def setStashId( self, stash_id ):
        self.stash_id = stash_id

        self.ok_button.setEnabled( self.stash_id is not None )

    def getStashId( self ):
        return self.stash_id

class WbStashesTableView(wb_table_view.WbTableView):
    def __init__( self, pick_dialog, main_window, stashes_model ):
        self.pick_dialog = pick_dialog
        self.main_window = main_window

        super().__init__()

        self._debug = self.main_window._debug

        self.setShowGrid( False )

        self.selected_row = None

        self.setModel( stashes_model )

        # size columns
        em = self.fontMetrics().width( 'm' )
        self.setColumnWidth( WbGitStashesModel.col_id, em*10 )
        self.setColumnWidth( WbGitStashesModel.col_branch, em*10 )
        self.setColumnWidth( WbGitStashesModel.col_message, em*50 )

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbStashesTableView.selectionChanged()' )

        stash_id = None
        for index in selected.indexes():
            if index.column() == 0:
                stash_info = self.model().stashInfo( index.row() )
                stash_id = stash_info.stash_id
                break

        self.pick_dialog.setStashId( stash_id )

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

class WbGitStashesModel(QtCore.QAbstractTableModel):
    col_id = 0
    col_branch = 1
    col_message = 2

    column_titles = (U_('Stash ID'), U_('Branch'), U_('Message'))

    def __init__( self, app ):
        self.app = app

        super().__init__()

        self.all_stashes  = []

    def loadStashInfo( self, all_stashes ):
        self.beginResetModel()
        self.all_stashes = all_stashes
        self.endResetModel()

    def rowCount( self, parent ):
        return len( self.all_stashes )

    def columnCount( self, parent ):
        return len( self.column_titles )

    def headerData( self, section, orientation, role ):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return T_( self.column_titles[section] )

            if orientation == QtCore.Qt.Vertical:
                return ''

        elif role == QtCore.Qt.TextAlignmentRole and orientation == QtCore.Qt.Horizontal:
            return QtCore.Qt.AlignLeft

        return None

    def stashInfo( self, row ):
        return self.all_stashes[ row ]

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            info = self.all_stashes[ index.row() ]

            col = index.column()

            if col == self.col_id:
                return info.stash_id

            elif col == self.col_branch:
                return info.stash_branch

            elif col == self.col_message:
                return info.stash_message

            assert False

        return None
