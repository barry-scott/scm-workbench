'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_table_base.py

'''
from PyQt6 import QtCore

import types

import wb_table_view

_alignment_map = {
    'L':    QtCore.Qt.AlignmentFlag.AlignLeft,
    'R':    QtCore.Qt.AlignmentFlag.AlignRight,
    'C':    QtCore.Qt.AlignmentFlag.AlignCenter,
    }

class TableColumn:
    def __init__( self, header, em_width, alignment, field, formater=None ):
        self.header = header
        self.em_width = em_width
        self.alignment = _alignment_map[ alignment ]
        self.field = field
        self.formater = formater

    def formatData( self, data ):
        if self.formater == '1line':
            return data.split( '\n', 1 )[0]

        else:
            return str( data )

class ViewModelMap:
    def __init__( self, all_columns ):
        self.all_columns = all_columns

    def numColumns( self ):
        return len(self.all_columns)

    def header( self, column_index ):
        return T_( self.all_columns[ column_index ].header )

    def emWidth( self, column_index ):
        return self.all_columns[ column_index ].em_width

    def alignment( self, column_index ):
        return self.all_columns[ column_index ].alignment

    # expects to be have a dict() or an instance of a class with
    # fields or accessor functions
    # use type info to figure which is which and get the field
    # if the value is a callable method, call it
    def data( self, column_index, container ):
        field = self.all_columns[ column_index ].field

        if isinstance( container, dict ):
            value = container[ field ]

        else:
            value = getattr( container, field )
            if type(value) == types.MethodType:
                value = value()

        return value

class WbTableView(wb_table_view.WbTableView):
    def __init__( self, app, all_columns ):
        super().__init__()
        self.app = app
        self.selection_changed_callback = None

        self.view_model_map = ViewModelMap( all_columns )

        self.model = WbTableModel( self.view_model_map )

        self.setShowGrid( False )

        self.setModel( self.model )

        # size columns
        em = self.fontMetrics().horizontalAdvance( 'm' )

        for index in range( self.view_model_map.numColumns() ):
            self.setColumnWidth( index, em*self.view_model_map.emWidth( index ) )

    def setSelectionChangedCallback( self, selection_changed_callback ):
        self.selection_changed_callback = self.app.wrapWithThreadSwitcher( selection_changed_callback, 'table_base_set_selection_changed' )

    def loadRows( self, all_rows ):
        self.model.loadRows( all_rows )

    def selectionChanged( self, selected, deselected ):
        for index in selected.indexes():
            if index.column() == 0:
                if self.selection_changed_callback is not None:
                    self.selection_changed_callback( self.model.rowInfo( index.row() ) )
                break

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

class WbTableModel(QtCore.QAbstractTableModel):
    def __init__( self, view_model_map ):
        self.view_model_map = view_model_map

        super().__init__()

        self.all_rows = []

    def loadRows( self, all_rows ):
        self.beginResetModel()
        self.all_rows = all_rows
        self.endResetModel()

    def rowCount( self, parent ):
        return len( self.all_rows )

    def columnCount( self, parent ):
        return self.view_model_map.numColumns()

    def headerData( self, section, orientation, role ):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self.view_model_map.header( section )

            if orientation == QtCore.Qt.Orientation.Vertical:
                return ''

        elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return self.view_model_map.alignment( section )
        return None

    def rowInfo( self, row ):
        return self.all_rows[ row ]

    def data( self, index, role ):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.view_model_map.data( index.column(), self.all_rows[ index.row() ] )

        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            return self.view_model_map.alignment( index.column() )

        return None
