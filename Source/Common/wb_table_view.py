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
    def __init__( self, spacing_scale=1.4, alternate_row_shading=True ):
        super().__init__()

        self.setAlternatingRowColors( alternate_row_shading )
        self.setShowGrid( False )

        # make text in cells be elided not wraped to multiple lines
        self.setWordWrap( False )

        vh = self.verticalHeader()
        vh.sectionResizeMode( vh.Fixed )
        line_spacing = self.fontMetrics().lineSpacing()
        vh.setDefaultSectionSize( int( line_spacing * spacing_scale ) )
