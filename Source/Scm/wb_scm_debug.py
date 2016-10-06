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
        self._debugGitProject = self.addDebugOption( 'GIT PROJECT' )
        self._debugGitUpdateTree = self.addDebugOption( 'GIT TREE' )
        self._debugHgProject = self.addDebugOption( 'HG PROJECT' )
        self._debugHgUpdateTree = self.addDebugOption( 'HG TREE' )
        self._debugHgProtocolTrace = self.addDebugOption( 'HG TRACE' )
        self._debugSvnProject = self.addDebugOption( 'SVN PROJECT' )
        self._debugSvnUpdateTree = self.addDebugOption( 'SVN TREE' )

        self._debugGitUi = self.addDebugOption( 'GIT UI' )
        self._debugHgUi = self.addDebugOption( 'HG UI' )
        self._debugSvnUi = self.addDebugOption( 'SVN UI' )

        self._debugLogHistory = self.addDebugOption( 'LOG HISTORY' )
        self._debugAnnotate = self.addDebugOption( 'ANNOTATE' )
