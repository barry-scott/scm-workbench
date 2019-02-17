'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_annotate_view.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtCore

import wb_tracked_qwidget
import wb_main_window
import wb_table_view

def U_( s: str ) -> str:
    return s

#------------------------------------------------------------
#
#   WbAnnotateView - show that annotation of a file
#
#------------------------------------------------------------
class WbAnnotateView(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    def __init__( self, app, ui_component, title ):
        self.app = app
        self.debugLog = self.app.debug_options.debugLogAnnotate

        super().__init__( app, app.debug_options.debugLogMainWindow )

        self.current_commit_selections = []
        self.current_file_selection = []

        self.current_annotations = None

        self.ui_component = ui_component

        self.annotate_model = WbAnnotateModel( self.app )

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

        #----------------------------------------
        self.annotate_table = WbAnnotateTableView( self )
        self.annotate_table.setSelectionBehavior( self.annotate_table.SelectRows )
        self.annotate_table.setAutoScroll( False )

        self.annotate_table.setModel( self.annotate_model )

        # size columns
        em = self.fontMetrics().width( 'm' )
        self.annotate_table.setColumnWidth( self.annotate_model.col_revision, em*5 )
        self.annotate_table.setColumnWidth( self.annotate_model.col_author, em*10 )
        self.annotate_table.setColumnWidth( self.annotate_model.col_date, em*20 )
        self.annotate_table.setColumnWidth( self.annotate_model.col_line_num, em*5 )
        self.annotate_table.setColumnWidth( self.annotate_model.col_line_text, em*80 )

        #----------------------------------------
        self.commit_message = QtWidgets.QPlainTextEdit()
        self.commit_message.setFont( self.app.getCodeFont() )
        self.commit_message.setReadOnly( True )

        #----------------------------------------
        self.v_message_layout = QtWidgets.QVBoxLayout()
        self.v_message_layout.addWidget( QtWidgets.QLabel( T_('Commit Message') ) )
        self.v_message_layout.addWidget( self.commit_message )

        self.v_message_widget = QtWidgets.QWidget()
        self.v_message_widget.setLayout( self.v_message_layout )

        # ----------------------------------------
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )
        self.v_split.addWidget( self.annotate_table )
        self.v_split.addWidget( self.v_message_widget )

        self.setCentralWidget( self.v_split )

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 100*em, 45*ex )

        self.ui_component.setTopWindow( self.app.top_window )
        self.ui_component.setMainWindow( self, None )

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.__setupTableContextMenu()

    def completeInit( self ):
        self.debugLog( 'completeInit()' )

        # set focus
        self.annotate_table.setFocus()

        # set splitter position
        table_size_ratio = 0.8
        height = sum( self.v_split.sizes() )
        table_height = int( height * table_size_ratio )
        message_height = height - table_height
        self.v_split.setSizes( [table_height, message_height] )

    def setupMenuBar( self, mb ):
        self.ui_component.setupMenuBar( mb, self._addMenu )

    def __setupTableContextMenu( self ):
        self.debugLog( '__setupTableContextMenu' )

        # --- setup scm_type specific menu

        m = QtWidgets.QMenu( self )

        self.ui_component.setupTableContextMenu( m, self._addMenu )

    def setupToolBar( self ):
        # --- setup scm_type specific tool bars
        self.ui_component.setupToolBarAtRight( self._addToolBar, self._addTool )

    def isScmTypeActive( self, scm_type ):
        return scm_type == ''

    def showAnnotationForFile( self, all_annotation_nodes, all_commit_log_nodes ):
        self.annotate_model.loadAnnotationForFile( all_annotation_nodes, all_commit_log_nodes )

        self.annotate_table.resizeColumnToContents( self.annotate_model.col_date )
        self.annotate_table.resizeColumnToContents( self.annotate_model.col_line_num )

        self.updateEnableStates()

    def selectionChangedAnnotation( self ):
        self.current_annotations = [index.row() for index in self.annotate_table.selectedIndexes() if index.column() == 0]

        if len(self.current_annotations) == 0:
            self.updateEnableStates()
            return

        self.current_annotations.sort()

        node = self.annotate_model.annotationNode( self.current_annotations[0] )
        log = self.annotate_model.annotationLogNode( node.log_id )

        self.commit_message.clear()
        if log is not None:
            self.commit_message.insertPlainText( log.commitMessage() )

        self.updateEnableStates()

class WbAnnotateTableView(wb_table_view.WbTableView):
    def __init__( self, main_window ):
        self.main_window = main_window

        self.debugLog = main_window.debugLog

        super().__init__( spacing_scale=1.1, alternate_row_shading=False )

    def selectionChanged( self, selected, deselected ):
        self.debugLog( 'WbLogTableView.selectionChanged()' )

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

        current_annotations = [index for index in self.selectedIndexes() if index.column() == WbAnnotateModel.col_line_num]
        if len(current_annotations) > 0:
            self.scrollTo( current_annotations[0] )

        self.main_window.selectionChangedAnnotation()

class WbAnnotateModel(QtCore.QAbstractTableModel):
    col_revision = 0
    col_author = 1
    col_date = 2
    col_line_num = 3
    col_line_text = 4

    column_titles = (U_('Revision'), U_('Author'), U_('Date'), U_('Line'), U_('Text'))

    def __init__( self, app ):
        self.app = app

        self.debugLog = self.app.debug_options.debugLogAnnotate

        super().__init__()

        self.all_annotation_nodes  = []
        self.all_commit_log_nodes = {}

        self.fixed_font = self.app.getCodeFont()

    def loadAnnotationForFile( self, all_annotation_nodes, all_commit_log_nodes ):
        self.beginResetModel()
        self.all_annotation_nodes = all_annotation_nodes
        self.all_commit_log_nodes = all_commit_log_nodes
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

    def annotationLogNode( self, rev_num ):
        return self.all_commit_log_nodes.get( rev_num, None )

    def data( self, index, role ):
        if role == QtCore.Qt.UserRole:
            return self.all_annotation_nodes[ index.row() ]

        if role == QtCore.Qt.DisplayRole:
            node = self.all_annotation_nodes[ index.row() ]
            log_node = self.all_commit_log_nodes[ node.log_id ]

            col = index.column()

            if col == self.col_revision:
                return log_node.commitIdString()

            elif col == self.col_author:
                return log_node.commitAuthor()

            elif col == self.col_date:
                return self.app.formatDatetime( log_node.commitDate() )

            elif col == self.col_line_num:
                return '%d' % (node.line_num,)

            elif col == self.col_line_text:
                return node.line_text

            assert False, 'col == %r' % (col,)

        elif role == QtCore.Qt.TextAlignmentRole:
            if index.column() == self.col_line_num:
                return QtCore.Qt.AlignRight

            else:
                return QtCore.Qt.AlignLeft

        elif role == QtCore.Qt.FontRole:
            # use the fixed font for all the column otherwise it looks odd
            return self.fixed_font

        return None
