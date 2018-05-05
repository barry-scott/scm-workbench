#!/usr/bin/env python3
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

def U_(s):
    return s

def T_(s):
    return s

def main( argv ):
    app = App( argv )

    app.main_window.show()

    rc = app.exec_()

    return rc

class App(QtWidgets.QApplication):
    def __init__( self, argv ):
        QtWidgets.QApplication.__init__( self, [sys.argv[0]] )

        self.opt_sort = '--sort' in argv
        self.opt_dynamic = '--dynamic' in argv

        self.main_window = MainWindow( self )

class MainWindow(QtWidgets.QMainWindow):
    def __init__( self, app, parent=None ):
        super().__init__( parent )
        self.app = app

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 100*em, 50*ex )

        self.table_view = TableView( self.app )

        self.filter_text = QtWidgets.QLineEdit()
        self.filter_text.setClearButtonEnabled( True )
        self.filter_text.setMaxLength( 256 )
        self.filter_text.setPlaceholderText( T_('Filter by name') )

        if self.app.opt_sort:
            self.filter_text.textChanged.connect( self.table_view.table_sortfilter.setFilterText )
        else:
            self.filter_text.textChanged.connect( self.table_view.setFilterText )

        # layout widgets in window
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )

        self.setCentralWidget( self.v_split )

        self.v_split_table = QtWidgets.QSplitter()
        self.v_split_table.setOrientation( QtCore.Qt.Vertical )

        self.h_filter_widget = QtWidgets.QWidget( self.v_split )
        self.h_filter_layout = QtWidgets.QGridLayout()

        row = 0
        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Filter:') ), row, 0 )
        self.h_filter_layout.addWidget( self.filter_text, row, 1, 1, 3 )

        self.h_filter_widget.setLayout( self.h_filter_layout )

        self.v_table_widget = QtWidgets.QWidget( self.v_split )
        self.v_table_layout = QtWidgets.QVBoxLayout()
        self.v_table_layout.addWidget( self.h_filter_widget )
        self.v_table_layout.addWidget( self.table_view )

        self.v_table_widget.setLayout( self.v_table_layout )

        self.v_split.addWidget( self.v_table_widget )

class TableView(QtWidgets.QTableView):
    def __init__( self, app, spacing_scale=1.4, alternate_row_shading=True ):
        self.app = app
        super().__init__()

        self.setAlternatingRowColors( alternate_row_shading )
        self.setShowGrid( False )

        vh = self.verticalHeader()
        vh.sectionResizeMode( vh.Fixed )
        line_spacing = self.fontMetrics().lineSpacing()
        vh.setDefaultSectionSize( int( line_spacing * spacing_scale ) )

        self.table_model = TableModel( self.app )

        self.table_sortfilter = TableSortFilter( self.app )
        self.table_sortfilter.setSourceModel( self.table_model )
        self.table_sortfilter.setDynamicSortFilter( self.app.opt_dynamic )

        self.table_sort_column = self.table_model.col_name
        self.table_sort_order = QtCore.Qt.AscendingOrder

        # setModel triggers a selectionChanged event
        if self.app.opt_sort:
            self.setModel( self.table_sortfilter )
        else:
            self.setModel( self.table_model )

        # size columns
        em = self.fontMetrics().width( 'm' )
        self.setColumnWidth( self.table_model.col_status, em*4 )
        self.setColumnWidth( self.table_model.col_name, em*32 )
        self.setColumnWidth( self.table_model.col_date, em*12 )

    def setFilterText( self, text ):
        print( 'TableView.setFilterText( %r )' % (text,) )

class TableSortFilter(QtCore.QSortFilterProxyModel):
    def __init__( self, app, parent=None ):
        self.app = app
        super().__init__( parent )

        self.filter_text = ''

    # ------------------------------------------------------------
    def setFilterText( self, text ):
        print( 'TableSortFilter.setFilterText( %r )' % (text,) )

        self.filter_text = text
        # invalidateFilter is documented to update the view with the
        # filter conditions are changed but it does not work
        # when filter puts more items into the result
        self.invalidateFilter()

    # ------------------------------------------------------------
    def filterAcceptsRow( self, source_row, source_parent ):
        model = self.sourceModel()
        index = model.createIndex( source_row, TableModel.col_name )

        entry = model.data( index, QtCore.Qt.UserRole )


        if self.filter_text != '':
            accept = self.filter_text.lower() in str(entry.name).lower()
        else:
            accept = True

        print( 'TableSortFilter.filterAcceptsRow() accept %r entry %r' % (accept, entry) )

        return accept

    def lessThan( self, source_left, source_right ):
        print( 'TableSortFilter.lessThan()' )
        model = self.sourceModel()
        left_ent = model.entry( source_left )
        right_ent = model.entry( source_right )
        column = source_left.column()

        return left_ent.name < right_ent.name

    def indexListFromNameList( self, all_names ):
        if len(all_names) == 0:
            return []

        model = self.sourceModel()

        all_indices = []
        for row in range( self.rowCount( QtCore.QModelIndex() ) ):
            index = self.createIndex( row, 0 )
            entry = model.data( index, QtCore.Qt.UserRole )
            if entry.name in all_names:
                all_indices.append( index )

        return all_indices

class TableModel(QtCore.QAbstractTableModel):
    col_status = 0
    col_name = 1
    col_date = 2
    col_num_columns = 3

    column_titles = (U_('Status'), U_('Name'), U_('Date'))

    def __init__( self, app ):
        self.app = app

        super().__init__()

        self.scm_project_tree_node = None

        self.all_files = [
            TableEntry( app, 'a-file.h' ),
            TableEntry( app, 'b-file.h' ),
            TableEntry( app, 'c-file.h' ),
            TableEntry( app, 'a-file.cpp' ),
            TableEntry( app, 'b-file.cpp' ),
            TableEntry( app, 'c-file.cpp' ),
            ]

        self.__brush_is_uncontrolled = QtGui.QBrush( QtGui.QColor( 0, 128, 0 ) )

    def debugLog( self, msg ):
        print( 'Debug TableModel: %s' % (msg,) )

    def isByPath( self ):
        return self.scm_project_tree_node is not None and self.scm_project_tree_node.isByPath()

    def rowCount( self, parent ):
        return len( self.all_files )

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

    def entry( self, index ):
        return self.all_files[ index.row() ]

    def data( self, index, role ):
        if role == QtCore.Qt.UserRole:
            return self.all_files[ index.row() ]

        if role == QtCore.Qt.DisplayRole:
            entry = self.all_files[ index.row() ]

            col = index.column()

            if col == self.col_status:
                return 'st'

            elif col == self.col_name:
                # entry.name maybe a pathlib.Path object
                name = str(entry.name)

                # name can be a
                return name

            elif col == self.col_date:
                return '2018-05-01'

            assert False

        elif role == QtCore.Qt.ForegroundRole:
            entry = self.all_files[ index.row() ]
            return self.__brush_is_uncontrolled

        return None

class TableEntry:
    def __init__( self, app, name ):
        self.app = app
        self.name = name

    def __repr__( self ):
        return '<TableEntry: n: %r>' % (self.name,)

    def isNotEqual( self, other ):
        return (self.name != other.name)

    def __lt__( self, other ):
        return self.name < other.name

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )
