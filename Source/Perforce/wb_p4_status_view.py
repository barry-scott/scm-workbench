'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_status_view.py

'''
from PyQt5 import QtWidgets

import wb_tracked_qwidget
import wb_table_base
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
                [wb_table_base.TableColumnDict( U_('Change List'),  10, 'r', 'change' )
                ,wb_table_base.TableColumnDict( U_('Description'),  50, 'l', 'desc', '1line' )] )

        self.changes_pending.setSelectionChangedCallback( self.changeListChanged )

        self.label_changes_shelved = QtWidgets.QLabel( T_('Shelved changes ') )
        self.changes_shelved = wb_table_base.WbTableView(
                [wb_table_base.TableColumnDict( U_('Change List'),  10, 'r', 'change' )
                ,wb_table_base.TableColumnDict( U_('Description'),  50, 'l', 'desc', '1line' )
                ,wb_table_base.TableColumnDict( U_('Client'),       10, 'l', 'client' )] )

        self.label_opened_files = QtWidgets.QLabel( T_('Opened files') )
        self.opened_files = wb_table_base.WbTableView(
                [wb_table_base.TableColumnDict( U_('Change List'),  10, 'r', 'change' )
                ,wb_table_base.TableColumnDict( U_('Action'),       10, 'l', 'action' )
                ,wb_table_base.TableColumnDict( U_('File'),         50, 'l', 'clientFile' )] )
        self.opened_files.setSelectionChangedCallback( self.fileSelected )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.label_changes_pending )
        self.layout.addWidget( self.changes_pending )

        self.layout.addWidget( self.label_changes_shelved )
        self.layout.addWidget( self.changes_shelved )

        self.layout.addWidget( self.label_opened_files )
        self.layout.addWidget( self.opened_files )

        self.setLayout( self.layout )

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 100*em, 50*ex )

    def changeListChanged( self, change ):
        self.opened_files.loadRows( self.all_change_list_files[ change[ 'change' ] ] )

    def fileSelected( self, opened_file ):
        print( 'QQQ %r' % (opened_file,) )
        filename = pathlib.Path( opened_file[ 'clientFile' ] )
        project, rel_path = self.app.prefs.getProjectContainingPath( filename )
        if project is None:
            return

        print( 'QQQ project %r' % (project,) )
        print( 'QQQ rel_path %r' % (rel_path,) )

        #self.app.main_window.gotoProjectAndFile( project, rel_path )

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
            self.opened_files.loadRows( self.all_change_list_files[ all_changes_pending[0] ] )
