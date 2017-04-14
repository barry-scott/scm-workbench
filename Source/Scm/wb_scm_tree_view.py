'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_tree_view.py

'''
from PyQt5 import QtWidgets

class WbScmTreeView(QtWidgets.QTreeView):
    def __init__( self, app, main_window ):
        self.app = app
        self.main_window = main_window

        self.debugLog = main_window.debugLog

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self.debugLog( 'WbScmTreeView.selectionChanged()' )

        # allow the tree to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

        # have the sort filter convert the indexes
        sortfilter = self.model()
        sortfilter.selectionChanged( selected, deselected )

    def focusInEvent( self, event ):
        super().focusInEvent( event )

        self.main_window.setFocusIsIn( 'tree' )
