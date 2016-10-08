'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_annotate.py

'''
import wb_annotate_view
import wb_ui_components

#------------------------------------------------------------
#
#   WbGitAnnotateView - show that annotation of a file
#
#------------------------------------------------------------

#
#   add tool bars and menu for use in the log history window
#
class GitAnnotateWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        super().__init__( 'git', factory )

class WbGitAnnotateView(wb_annotate_view.WbAnnotateView):
    def __init__( self, app, title ):
        ui_components = GitAnnotateWindowComponents( app.getScmFactory( 'git' ) )
        super().__init__( app, ui_components, title )
