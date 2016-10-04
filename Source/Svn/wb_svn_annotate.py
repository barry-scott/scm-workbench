'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_annotate.py

'''
import wb_annotate_view
import wb_svn_ui_actions


#------------------------------------------------------------
#
#   WbSvnAnnotateView - show that annotation of a file
#
#------------------------------------------------------------

#
#   add tool bars and menu for use in the log history window
#
class SvnAnnotateWindowComponents(wb_svn_ui_actions.SvnMainWindowActions):
    def __init__( self, factory ):
        super().__init__( factory )

class WbSvnAnnotateView(wb_annotate_view.WbAnnotateView):
    def __init__( self, app, title ):
        super().__init__( app, SvnAnnotateWindowComponents(), title )
