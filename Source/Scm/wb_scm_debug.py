'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_debug.py

'''
import wb_debug

class WbScmDebug(wb_debug.WbDebug):
    def __init__( self, log ):
        super().__init__( log )

        # assumes derived class sets self.log
        self.debugLogGitProject = self.addDebugOption( 'GIT PROJECT' )
        self.debugLogGitUpdateTree = self.addDebugOption( 'GIT TREE' )
        self.debugLogHgProject = self.addDebugOption( 'HG PROJECT' )
        self.debugLogHgUpdateTree = self.addDebugOption( 'HG TREE' )
        self.debugLogHgProtocolTrace = self.addDebugOption( 'HG TRACE' )
        self.debugLogSvnProject = self.addDebugOption( 'SVN PROJECT' )
        self.debugLogSvnUpdateTree = self.addDebugOption( 'SVN TREE' )

        self.debugLogGitUi = self.addDebugOption( 'GIT UI' )
        self.debugLogHgUi = self.addDebugOption( 'HG UI' )
        self.debugLogSvnUi = self.addDebugOption( 'SVN UI' )

        self.debugLogLogHistory = self.addDebugOption( 'LOG HISTORY' )
        self.debugLogAnnotate = self.addDebugOption( 'ANNOTATE' )
