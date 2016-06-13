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
    def __init__( self ):
        # assumes derived class sets self.log
        self._debug_git_project = False
        self._debug_hg_project = False
        self._debug_svn_project = False
        self._debug_log_history = False

        super().__init__()

    def _debugHgProject( self, msg ):
        if self._debug_hg_project:
            self.log.debug( 'HG-PROJECT %s' % (msg,) )

    def _debugGitProject( self, msg ):
        if self._debug_git_project:
            self.log.debug( 'GIT-PROJECT %s' % (msg,) )

    def _debugSvnProject( self, msg ):
        if self._debug_svn_project:
            self.log.debug( 'SVN-PROJECT %s' % (msg,) )

    def _debugLogHistory( self, msg ):
        if self._debug_log_history:
            self.log.debug( 'LOG-HISTORY %s' % (msg,) )
