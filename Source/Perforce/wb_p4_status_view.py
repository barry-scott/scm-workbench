'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_status_view.py

'''
from PyQt6 import QtWidgets
from PyQt6 import QtCore

from wb_background_thread import thread_switcher

import wb_tracked_qwidget
import wb_table_base
import wb_preferences
import pathlib

class WbP4StatusView(wb_tracked_qwidget.WbTrackedModelessQWidget):
    def __init__( self, app, title ):
        self.app = app

        super().__init__()

        self.all_change_list_files = {}

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

        self.label_changes_pending = QtWidgets.QLabel( T_('Pending Changes ') )
        self.changes_pending = wb_table_base.WbTableView(
                self.app,
                [wb_table_base.TableColumn( U_('Change List'),  10, 'R', 'change' )
                ,wb_table_base.TableColumn( U_('Description'),  50, 'L', 'desc', '1line' )] )

        self.changes_pending.setSelectionChangedCallback( self.changeListChanged )

        self.label_changes_shelved = QtWidgets.QLabel( T_('Shelved changes ') )
        self.changes_shelved = wb_table_base.WbTableView(
                self.app,
                [wb_table_base.TableColumn( U_('Change List'),  10, 'R', 'change' )
                ,wb_table_base.TableColumn( U_('Description'),  50, 'L', 'desc', '1line' )
                ,wb_table_base.TableColumn( U_('Client'),       10, 'L', 'client' )] )

        self.label_opened_files = QtWidgets.QLabel( T_('Opened files') )
        self.opened_files = wb_table_base.WbTableView(
                self.app,
                [wb_table_base.TableColumn( U_('Change List'),  10, 'R', 'change' )
                ,wb_table_base.TableColumn( U_('Action'),       10, 'L', 'action' )
                ,wb_table_base.TableColumn( U_('File'),         50, 'L', 'clientFile' )] )
        self.opened_files.setSelectionChangedCallback( self.fileSelected_Bg )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.label_changes_pending )
        self.layout.addWidget( self.changes_pending )

        self.layout.addWidget( self.label_changes_shelved )
        self.layout.addWidget( self.changes_shelved )

        self.layout.addWidget( self.label_opened_files )
        self.layout.addWidget( self.opened_files )

        self.setLayout( self.layout )

        em, ex = self.app.defaultFontEmEx( 'm' )
        self.resize( 100*em, 50*ex )

    def changeListChanged( self, change ):
        change_id =  change[ 'change' ]
        if change_id in self.all_change_list_files:
            # load the files
            self.opened_files.loadRows( self.all_change_list_files[ change_id ] )

        else:
            # the change has no files in the work space
            self.opened_files.loadRows( [] )

    @thread_switcher
    def fileSelected_Bg( self, opened_file ):
        filename = pathlib.Path( opened_file[ 'clientFile' ] )
        project, rel_path = self.app.prefs.getProjectContainingPath( filename )
        if project is None:
            return

        favorite = wb_preferences.Favorite( menu='_', project_path=project.path, path=rel_path.parent )
        yield from self.app.main_window.gotoFavorite_bg( favorite )

        model = self.app.main_window.table_view.table_sortfilter
        src_model = self.app.main_window.table_view.table_model
        all_indices = src_model.indexListFromNameList( [rel_path.name] )
        if len(all_indices) == 0:
            return

        selection_model = self.app.main_window.table_view.selectionModel()

        # need a QItemSelection for this to work
        left = all_indices[0]
        right = left.model().createIndex( left.row(), 3, QtCore.QModelIndex() )

        # must convert to source model indices
        # and in this exact way otherwise SEGV on the select call
        sort_left = model.mapFromSource( left )
        sort_right = model.mapFromSource( right )

        cell = QtCore.QItemSelection( sort_left, sort_right )
        selection_model.select( cell, QtCore.QItemSelectionModel.SelectionFlag.Select )

    def setStatus( self, all_opened_files, all_changes_pending, all_changes_shelved ):
        self.all_change_list_files = {}

        for change in all_opened_files:
            self.all_change_list_files.setdefault( change[ 'change' ], [] ).append( change )

        if 'default' in self.all_change_list_files:
            all_changes_pending.append( {'change': 'default', 'desc': ''} )

        self.changes_pending.loadRows( all_changes_pending )
        self.changes_shelved.loadRows( all_changes_shelved )

        if 'default' in self.all_change_list_files:
            self.opened_files.loadRows( self.all_change_list_files[ 'default' ] )

        elif len(self.all_change_list_files) > 0:
            self.changeListChanged( all_changes_pending[0] )
