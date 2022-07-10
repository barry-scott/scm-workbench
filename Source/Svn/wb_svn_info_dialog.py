'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_info_dialog.py

'''
from PyQt6 import QtWidgets
from PyQt6 import QtCore

import pysvn

class InfoDialog(QtWidgets.QDialog):
    def __init__( self, app, parent, rel_path, abs_path, info ):
        super().__init__( parent )

        self.app = app

        self.setWindowTitle( T_('Svn Info for %s') % (rel_path,) )

        self.v_layout = QtWidgets.QVBoxLayout()

        self.group = None
        self.grid = None

        self.addGroup( T_('Entry') )
        self.addRow( T_('Path:'), abs_path )

        self.initFromInfo( info )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton( self.buttons.Close )

        self.buttons.rejected.connect( self.close )

        self.v_layout.addWidget( self.buttons )

        self.setLayout( self.v_layout )

    def initFromInfo( self, info ):
        if info.URL:
            self.addRow( T_('URL:'), info.URL )

        if info.repos_root_URL:
            self.addRow( T_('Repository root URL:'), info.repos_root_URL )

        if info.repos_UUID:
            self.addRow( T_('Repository UUID:'), info.repos_UUID )

        if info.rev.kind == pysvn.opt_revision_kind.number:
            self.addRow( T_('Revision:'), info.rev.number )

        if info.kind == pysvn.node_kind.file:
            self.addRow( T_('Node kind:'), T_('file') )

        elif info.kind == pysvn.node_kind.dir:
            self.addRow( T_('Node kind:'), T_('directory') )

        elif info.kind == pysvn.node_kind.none:
            self.addRow( T_('Node kind:'), T_('none') )

        else:
            self.addRow( T_('Node kind:'), T_('unknown') )

        if info.last_changed_author:
            self.addRow( T_('Last Changed Author:'), info.last_changed_author )

        if info.last_changed_rev.number > 0:
            self.addRow( T_('Last Changed Revision:'), info.last_changed_rev.number )

        if info.last_changed_date:
            self.addRow( T_('Last Changed Date:'), self.app.formatDatetime( info.last_changed_date ) )

        self.addGroup( T_('Lock') )
        lock_info = info.lock
        if lock_info is not None:
            self.addRow( T_('Lock Owner:'), lock_info.owner )
            self.addRow( T_('Lock Creation Date:'), self.app.formatDatetime( lock_info.creation_date ) )
            if lock_info.expiration_date is not None:
                self.addRow( T_('Lock Expiration Date:'), self.app.formatDatetime( lock_info.expiration_date ) )
            self.addRow( T_('Lock Token:'), lock_info.token )
            self.addRow( T_('Lock Comment:'), lock_info.comment )
        else:
            self.addRow( T_('Lock Token:'), '' )

        wc_info = info.wc_info
        if wc_info is None:
            return

        self.addGroup( T_('Working copy') )
        if wc_info['schedule'] == pysvn.wc_schedule.normal:
            self.addRow( T_('Schedule:'), T_('normal') )

        elif wc_info['schedule'] == pysvn.wc_schedule.add:
            self.addRow( T_('Schedule:'), T_('add') )

        elif wc_info['schedule'] == pysvn.wc_schedule.delete:
            self.addRow( T_('Schedule:'), T_('delete') )

        elif wc_info['schedule'] == pysvn.wc_schedule.replace:
            self.addRow( T_('Schedule:'), T_('replace') )

        else:
            #QQQ: is str needed?
            self.addRow( T_('Schedule:'), str(wc_info['schedule']))

        if wc_info['copyfrom_url']:
            self.addRow( T_('Copied From URL:'), wc_info['copyfrom_url'] )
            if wc_info['copyfrom_rev'].number:
                self.addRow( T_('Copied From Revision:'), wc_info['copyfrom_rev'].number )

        if wc_info['text_time']:
            self.addRow( T_('Text Last Updated:'), self.app.formatDatetime( wc_info['text_time'] ) )

        if wc_info['prop_time']:
            self.addRow( T_('Properties Last Updated:'), self.app.formatDatetime( wc_info['prop_time'] ) )

        if wc_info['checksum']:
            self.addRow( T_('Checksum:'), wc_info['checksum'] )

    def addGroup( self, label ):
        self.group = QtWidgets.QGroupBox( label )
        self.v_layout.addWidget( self.group )

        self.grid = QtWidgets.QGridLayout()
        self.grid.setColumnStretch( 1, 1 )

        self.group.setLayout( self.grid )

    def addRow( self, label, value ):
        value = str(value)

        label_ctrl = QtWidgets.QLabel( label )
        label_ctrl.setAlignment( QtCore.Qt.AlignmentFlag.AlignRight )

        if '\n' in value:
            value_ctrl = QtWidgets.QPlainTextEdit()

        else:
            value_ctrl = QtWidgets.QLineEdit()


        value_ctrl.setMinimumWidth( 600 )
        value_ctrl.setReadOnly( True )
        value_ctrl.setText( value )

        row = self.grid.rowCount()
        self.grid.addWidget( label_ctrl, row, 0 )
        self.grid.addWidget( value_ctrl, row, 1 )
