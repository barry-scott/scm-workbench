'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_annotate.py

'''
import time

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_tracked_qwidget
import wb_config
import wb_main_window

import wb_scm_images

import wb_svn_ui_actions


#------------------------------------------------------------
#
#   WbSvnLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------

#
#   add tool bars and menu for use in the log history window
#
class SvnAnnotateWindowComponents(wb_svn_ui_actions.SvnMainWindowActions):
    def __init__( self ):
        super().__init__()

class WbSvnAnnotateView(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    def __init__( self, app, title, icon ):
        self.app = app
        self._debug = self.app._debugAnnotate

        super().__init__( app, wb_scm_images, app._debugMainWindow )

        self.current_commit_selections = []
        self.current_file_selection = []

        self.filename = None
        self.svn_project = None

        self.ui_component = SvnAnnotateWindowComponents()

        self.annatate_model = WbSvnAnnotateModel( self.app )

        self.setWindowTitle( title )
        self.setWindowIcon( icon )

        self.font = QtGui.QFont( wb_config.face, wb_config.point_size )

        #----------------------------------------
        self.annotate_table = WbAnnotateTableView( self )
        self.annotate_table.setSelectionBehavior( self.annotate_table.SelectRows )
        self.annotate_table.setSelectionMode( self.annotate_table.ExtendedSelection )
        self.annotate_table.setModel( self.annatate_model )

        # size columns
        em = self.app.fontMetrics().width( 'm' )
        self.annotate_table.setColumnWidth( self.annatate_model.col_revision, em*5 )
        self.annotate_table.setColumnWidth( self.annatate_model.col_author, em*10 )
        self.annotate_table.setColumnWidth( self.annatate_model.col_date, em*16 )
        self.annotate_table.setColumnWidth( self.annatate_model.col_line_num, em*5 )
        self.annotate_table.setColumnWidth( self.annatate_model.col_line_text, em*255 )

        #----------------------------------------
        self.commit_message = QtWidgets.QPlainTextEdit()
        self.commit_message.setFont( self.font )
        h = self.commit_message.fontMetrics().lineSpacing()
        self.commit_message.setFixedHeight( h*4 )
        self.commit_message.setReadOnly( True )

        #----------------------------------------
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.annotate_table )
        self.layout.addWidget( QtWidgets.QLabel( T_('Commit Message') ) )
        self.layout.addWidget( self.commit_message )

        #----------------------------------------
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout( self.layout )

        self.setCentralWidget( self.widget )

        self.resize( 1000, 600 )

        self.ui_component.setTopWindow( self.app.top_window )
        self.ui_component.setMainWindow( self, None )

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.__setupTableContextMenu()

        # The rest of init has to be done after the widgets are rendered
        self.timer_init = QtCore.QTimer()
        self.timer_init.timeout.connect( self.completeStatupInitialisation )
        self.timer_init.setSingleShot( True )
        self.timer_init.start( 0 )

    def scmFocusWidget( self ):
        return 'table'

    def completeStatupInitialisation( self ):
        self._debug( 'completeStatupInitialisation()' )

        # set focus
        self.annotate_table.setFocus()

        self.timer_init = None

    def setupMenuBar( self, mb ):
        self.ui_component.setupMenuBar( mb, self._addMenu )

    def __setupTableContextMenu( self ):
        self._debug( '__setupTableContextMenu' )

        # --- setup scm_type specific menu

        m = QtWidgets.QMenu( self )

        self.ui_component.setupTableContextMenu( m, self._addMenu )

    def setupToolBar( self ):
        # --- setup scm_type specific tool bars
        self.ui_component.setupToolBarAtRight( self._addToolBar, self._addTool )

    def isScmTypeActive( self, scm_type ):
        return scm_type == 'svn'

    def showAnnotationForFile( self, svn_project, filename ):
        self.filename = filename
        self.svn_project = svn_project

        self.annatate_model.loadAnnotationForFile( svn_project, filename )
        self.updateEnableStates()

    def selectionChangedAnnotation( self ):
        self.current_annotations = [index.row() for index in self.annotate_table.selectedIndexes() if index.column() == 0]

        if len(self.current_annotations) == 0:
            self.updateEnableStates()
            return

        self.current_annotations.sort()

        node = self.annatate_model.annotationNode( self.current_annotations[0] )

        self.commit_message.clear()
        self.commit_message.insertPlainText( 'TBD - need the commit message for %d\n2\n3\n4\n' % (node['revision'].number,) )

        self.updateEnableStates()

class WbAnnotateTableView(QtWidgets.QTableView):
    def __init__( self, main_window ):
        self.main_window = main_window

        self._debug = main_window._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbLogTableView.selectionChanged()' )

        self.main_window.selectionChangedAnnotation()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )


class WbSvnAnnotateModel(QtCore.QAbstractTableModel):
    col_revision = 0
    col_author = 1
    col_date = 2
    col_line_num = 3
    col_line_text = 4

    column_titles = (U_('Revision'), U_('Author'), U_('Date'), U_('Line'), U_('Text'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debugAnnotate

        super().__init__()

        self.all_annotation_nodes  = []

    def loadAnnotationForFile( self, svn_project, filename ):
        self.beginResetModel()
        self.all_annotation_nodes = svn_project.cmdAnnotationForFile( filename )
        self.endResetModel()

    def rowCount( self, parent ):
        return len( self.all_annotation_nodes )

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

    def annotationNode( self, row ):
        return self.all_annotation_nodes[ row ]

    def revForRow( self, row ):
        return self.all_annotation_nodes[ row ].revision

    def data( self, index, role ):
        if role == QtCore.Qt.UserRole:
            return self.all_annotation_nodes[ index.row() ]

        if role == QtCore.Qt.DisplayRole:
            node = self.all_annotation_nodes[ index.row() ]

            col = index.column()

            if col == self.col_revision:
                return '%d' % (node['revision'].number,)

            elif col == self.col_author:
                return node['author']

            elif col == self.col_date:
                return node['date']
                #time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( node['date'] ) )

            elif col == self.col_line_num:
                return '%d' % (node['number']+1,)

            elif col == self.col_line_text:
                return node['line']

            assert False, 'col == %r' % (col,)

        elif role == QtCore.Qt.TextAlignmentRole:
            if index.column() == self.col_line_num:
                return QtCore.Qt.AlignRight

            else:
                return QtCore.Qt.AlignLeft

        return None
