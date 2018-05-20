'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_annotate.py

'''
import wb_annotate_view
import wb_ui_components

#------------------------------------------------------------
#
#   WbP4AnnotateView - show that annotation of a file
#
#------------------------------------------------------------

#
#   add tool bars and menu for use in the log history window
#
class P4AnnotateWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        super().__init__( 'p4', factory )

class WbP4AnnotateView(wb_annotate_view.WbAnnotateView):
    def __init__( self, app, title ):
        ui_components = P4AnnotateWindowComponents( app.getScmFactory( 'p4' ) )
        super().__init__( app, ui_components, title )
