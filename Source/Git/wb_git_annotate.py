'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_annotate.py

'''
import wb_annotate_view
import wb_git_ui_actions


#------------------------------------------------------------
#
#   WbGitAnnotateView - show that annotation of a file
#
#------------------------------------------------------------

#
#   add tool bars and menu for use in the log history window
#
class GitAnnotateWindowComponents(wb_git_ui_actions.GitMainWindowActions):
    def __init__( self, factory ):
        super().__init__( factory )

class WbGitAnnotateView(wb_annotate_view.WbAnnotateView):
    def __init__( self, app, title ):
        super().__init__( app, GitAnnotateWindowComponents(), title )
