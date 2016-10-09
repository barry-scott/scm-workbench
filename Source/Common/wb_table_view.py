'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_table_view.py

'''
from PyQt5 import QtWidgets

#
#   wbTableView
#   standardize the way tables look with workbench.
#
#   no grid lines
#   close up the spacing
#
class WbTableView(QtWidgets.QTableView):
    def __init__( self ):
        super().__init__()

        self.setShowGrid( False )

        vh = self.verticalHeader()
        vh.sectionResizeMode( vh.Fixed )
        spacing = self.fontMetrics().lineSpacing()
        vh.setDefaultSectionSize( int( spacing * 1.4 ) )
