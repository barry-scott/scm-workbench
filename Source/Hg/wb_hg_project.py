'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_project.py

'''
import pathlib
import sys

import hglib
import hglib.util
import hglib.client

HgCommandError = hglib.error.CommandError

def hgInit( wc_path ):
    hglib.init( str(wc_path).encode('utf-8') )

def hgClone( url, wc_path ):
    hglib.clone( str(url).encode('utf-8'), str(wc_path).encode('utf-8') )

def HgVersion():
    args = hglib.util.cmdbuilder( 'version' )
    args.insert( 0, hglib.HGPATH )

    proc = hglib.util.popen( args )
    out, err = proc.communicate()
    if proc.returncode:
        raise hglib.error.CommandError( args, proc.returncode, out, err )

    # assume first line is has the critical version info
    return out.decode( 'utf-8' ).split('\n')[0]

class HgProject:
    def __init__( self, app, prefs_project, ui_components ):
        self.app = app
        self.ui_components = ui_components

        self._debug = self.app._debug_options._debugHgProject
        self._debugTree = self.app._debug_options._debugHgUpdateTree
        self._traceProtocol = self.app._debug_options._debugHgProtocolTrace

        self.prefs_project = prefs_project
        self.repo = hglib.open( str( prefs_project.path ) )

        self.tree = HgProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )
        self.flat_tree = HgProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        self.all_file_state = {}

        self.__num_modified_files = 0

    def enableProtocolTrace( self, state ):
        if self._traceProtocol.isEnabled():
            # setprotocoltrace is not in older version of hglib
            if hasattr( self.repo, 'setprotocoltrace' ):
                if state:
                    self.repo.setprotocoltrace( self.traceHgProtocol )
                else:
                    self.repo.setprotocoltrace( None )

    def traceHgProtocol( self, channel, data ):
        self._traceProtocol( 'ch: %r, data: %r' % (channel, data) )

    def scmType( self ):
        return 'hg'

    def getBranchName( self ):
        return '-- TBD --' # QQQ missing code

    # return a new HgProject that can be used in another thread
    def newInstance( self ):
        return HgProject( self.app, self.prefs_project, self.ui_components )

    def isNotEqual( self, other ):
        return self.prefs_project.name != other.prefs_project.name

    def __repr__( self ):
        return '<HgProject: %s>' % (self.prefs_project.name,)

    def projectName( self ):
        return self.prefs_project.name

    def projectPath( self ):
        return self.prefs_project.path

    def headRefName( self ):
        return 'unknown'

    def numModifiedFiles( self ):
        return self.__num_modified_files

    def updateState( self ):
        # rebuild the tree
        self.tree = HgProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )
        self.flat_tree = HgProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )

        if not self.projectPath().exists():
            self.app.log.error( T_('Project %(name)s folder %(folder)s has been deleted') %
                            {'name': self.projectName()
                            ,'folder': self.projectPath()} )

            self.all_file_state = {}

        else:
            self.__calculateStatus()


        for path in self.all_file_state:
            self.__updateTree( path )

        self.dumpTree()

    def __calculateStatus( self ):
        self.all_file_state = {}

        repo_root = self.projectPath()

        hg_dir = repo_root / '.hg'

        all_folders = set( [repo_root] )
        while len(all_folders) > 0:
            folder = all_folders.pop()

            for filename in folder.iterdir():
                abs_path = folder / filename

                repo_relative = abs_path.relative_to( repo_root )

                if abs_path.is_dir():
                    if abs_path != hg_dir:
                        all_folders.add( abs_path )

                        self.all_file_state[ repo_relative ] = WbHgFileState( self, repo_relative )
                        self.all_file_state[ repo_relative ].setIsDir()

                else:
                    self.all_file_state[ repo_relative ] = WbHgFileState( self, repo_relative )

        for nodeid, permission, executable, symlink, filepath in self.repo.manifest():
            filepath = self.pathForWb( filepath )
            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbHgFileState( self, filepath )

            self.all_file_state[ filepath ].setManifest( nodeid, permission, executable, symlink )

        for state, filepath in self.repo.status( all=True, ignored=True ):
            state = state.decode( 'utf-8' )

            filepath = self.pathForWb( filepath )
            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbHgFileState( self, filepath )

            self.all_file_state[ filepath ].setState( state )

            if state in ('A', 'M', 'R'):
                self.__num_modified_files += 1

    def __updateTree( self, path ):
        self._debugTree( '__updateTree path %r' % (path,) )
        node = self.tree

        self._debugTree( '__updateTree path.parts %r' % (path.parts,) )

        for index, name in enumerate( path.parts[0:-1] ):
            self._debugTree( '__updateTree name %r at node %r' % (name,node) )

            if not node.hasFolder( name ):
                node.addFolder( name, HgProjectTreeNode( self, name, pathlib.Path( *path.parts[0:index+1] ) ) )

            node = node.getFolder( name )

        self._debugTree( '__updateTree addFile %r to node %r' % (path, node) )
        node.addFileByName( path )
        self.flat_tree.addFileByPath( path )

    def dumpTree( self ):
        if self._debugTree.isEnabled():
            self.tree._dumpTree( 0 )

    #------------------------------------------------------------
    #
    # functions to retrive interesting info from the repo
    #
    #------------------------------------------------------------
    def hasFileState( self, filename ):
        assert isinstance( filename, pathlib.Path )
        return filename in self.all_file_state

    def getFileState( self, filename ):
        assert isinstance( filename, pathlib.Path )
        # status only has enties for none CURRENT status files
        return self.all_file_state[ filename ]

    def getReportModifiedFiles( self ):
        all_moddified_files = []
        for filename, file_state in self.all_file_state.items():
            if file_state.isAdded():
                all_moddified_files.append( (T_('New file'), filename) )

            elif file_state.isModified():
                all_moddified_files.append( (T_('Modified'), filename) )

            elif file_state.isDeleted():
                all_moddified_files.append( (T_('Deleted'), filename) )

        return all_moddified_files

    def getReportUntrackedFiles( self ):
        all_untracked_files = []
        for filename, file_state in self.all_file_state.items():
            if file_state.isUncontrolled():
                all_untracked_files.append( (T_('New file'), filename) )

        return all_untracked_files

    def canPush( self ):
        print( 'qqq need canPush' )
        return True

        for commit in self.repo.iter_commits( None, max_count=1 ):
            commit_id = commit.hexsha

            for remote in self.repo.remotes:
                for ref in remote.refs:
                    remote_id = ref.commit.hexsha

                    return commit_id != remote_id

        return False

    def getUnpushedCommits( self ):
        print( 'qqq need getUnpushedCommits' )
        return []

        last_pushed_commit_id = ''
        for remote in self.repo.remotes:
            for ref in remote.refs:
                last_pushed_commit_id = ref.commit.hexsha

        all_unpushed_commits = []
        for commit in self.repo.iter_commits( None ):
            commit_id = commit.hexsha

            if last_pushed_commit_id == commit_id:
                break

            all_unpushed_commits.append( commit )

        return all_unpushed_commits

    #------------------------------------------------------------
    #
    # all functions starting with "cmd" are like the hg <cmd> in behavior
    #
    #------------------------------------------------------------
    def pathForHg( self, path ):
        assert isinstance( path, pathlib.Path ), 'path %r' % (path,)
        # return abs path
        return str( self.projectPath() / path ).encode( sys.getfilesystemencoding() )

    def pathForWb( self, bytes_path ):
        assert type( bytes_path ) == bytes
        return pathlib.Path( bytes_path.decode( sys.getfilesystemencoding() ) )

    def getTextLinesForRevision( self, filepath, rev ):
        if type( rev ) == int:
            rev = '%d' % (rev,)
        # else its a string like 'tip'

        text = self.cmdCat( filepath, rev=rev )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

    def cmdCat( self, filename, rev=None ):
        byte_result = self.repo.cat( [self.pathForHg( filename )], rev=rev )
        return byte_result.decode( 'utf-8' )

    def cmdAdd( self, filename ):
        self.repo.add( self.pathForHg( filename ) )

    def cmdRevert( self, filename ):
        self.repo.revert( self.pathForHg( filename ) )

    def cmdDelete( self, filename ):
        self.repo.delete( self.pathForHg( filename ) )

    def cmdDiffFolder( self, folder ):
        text = self.repo.diff( [self.pathForHg( folder )] )
        return text.decode( 'utf-8' )

    def cmdDiffWorkingVsCommit( self, filename, commit ):
        text = self.repo.diff( [self.pathForHg( filename )], revs='%d' % (commit,) )
        return text.decode( 'utf-8' )

    def cmdDiffCommitVsCommit( self, filename, old_commit, new_commit ):
        text = self.repo.diff( [self.pathForHg( filename )], revs='%d:%d' % (old_commit, new_commit) )
        return text.decode( 'utf-8' )

    def cmdCommit( self, message ):
        return self.repo.commit( message )

    def cmdCommitLogForRepository( self, limit=None, since=None, until=None ):
        if since is not None and until is not None:
            date = '%s to %s' % (since, until)

        elif since is not None:
            date = '>%s' % (since,)

        elif until is not None:
            date = '<%s' % (until,)

        else:
            date = None

        all_logs = [WbHgLog( data, self.repo ) for data in self.repo.log( limit=limit, date=date )]

        return all_logs

    def cmdCommitLogForFile( self, filename, limit=None, since=None, until=None ):
        if since is not None and until is not None:
            date = '%s to %s' % (since, until)

        elif since is not None:
            date = '>%s' % (since,)

        elif until is not None:
            date = '<%s' % (until,)

        else:
            date = None

        all_logs = [WbHgLog( data, self.repo )
                    for data in self.repo.log( files=[self.pathForHg( filename )], limit=limit, date=date )]

        return all_logs

    def __addCommitChangeInformation( self, all_commit_logs ):
        # now calculate what was added, deleted and modified in each commit
        for offset in range( len(all_commit_logs) ):
            new_tree = all_commit_logs[ offset ].commitTree()
            old_tree = all_commit_logs[ offset ].commitPreviousTree()

            all_new = {}
            self.__treeToDict( new_tree, all_new )
            new_set = set(all_new)

            if old_tree is None:
                all_commit_logs[ offset ]._addChanges( new_set, set(), [], set() )

            else:
                all_old = {}
                self.__treeToDict( old_tree, all_old )

                old_set = set(all_old)

                all_added = new_set - old_set
                all_deleted = old_set - new_set

                all_renamed = []

                if len(all_added) > 0:
                    all_old_id_to_name = {}
                    for name, id_ in all_old.items():
                        all_old_id_to_name[ id_ ] = name

                    for name in list(all_added):
                        id_ = all_new[ name ]

                        if id_ in all_old_id_to_name:
                            all_added.remove( name )
                            all_deleted.remove( all_old_id_to_name[ id_ ] )
                            all_renamed.append( (name, all_old_id_to_name[ id_ ]) )

                all_modified = set()

                for key in all_new:
                    if( key in all_old
                    and all_new[ key ] != all_old[ key ] ):
                        all_modified.add( key )

                all_commit_logs[ offset ]._addChanges( all_added, all_deleted, all_renamed, all_modified )

    def __treeToDict( self, tree, all_entries ):
        for blob in tree:
            if blob.type == 'blob':
                all_entries[ blob.path ] = blob.hexsha

        for child in tree.trees:
            self.__treeToDict( child, all_entries )

    def cmdPull( self, progress, info ):
        self._debug( 'cmdPull()' )
        self.enableProtocolTrace( True )
        try:
            self.repo.pull( update=True, prompt=self.promptHandler )

        finally:
            self.enableProtocolTrace( False )

    def cmdPush( self, progress, info ):
        self._debug( 'cmdPush()' )

        self.enableProtocolTrace( True )
        try:
            self.repo.push()

        finally:
            self.enableProtocolTrace( False )

    def promptHandler( self, max_response_size, output ):
        self._debug( 'promptHandler( %r, %r )' % (max_response_size, output) )
        return b''

class WbHgLog:
    def __init__( self, data, repo ):
        self.rev =      int(data.rev.decode('utf-8'))
        self.node =     data.node.decode('utf-8')
        self.all_tags = data.tags.decode('utf-8').split(' ')
        self.branch =   data.branch.decode('utf-8')
        self.author =   data.author.decode('utf-8')
        self.message =  data.desc.decode('utf-8')
        self.date =     data.date

        if self.rev == 0:
            rev= '0'
        else:
            rev = '%d:%d' % (self.rev-1, self.rev)

        self.all_changed_files = [(state.decode('utf-8'), path.decode('utf-8')) for state, path in repo.status( rev=rev )]

class WbHgFileState:
    def __init__( self, project, filepath ):
        self.__project = project
        self.__filepath = filepath

        self.__is_dir = False

        self.__state = ''

        self.__nodeid = None
        self.__permission = None
        self.__executable = None
        self.__symlink = None

    def setState( self, state ):
        self.__state = state.decode('utf-8')

    def __repr__( self ):
        return ('<WbHgFileState: %s %s %s>' %
                (self.__filepath, self.__state, self.__nodeid))

    def setIsDir( self ):
        self.__is_dir = True

    def isDir( self ):
        return self.__is_dir

    def setManifest( self, nodeid, permission, executable, symlink ):
        self.__nodeid = nodeid.decode('utf-8')
        self.__permission = permission
        self.__executable = executable
        self.__symlink = symlink

    def setState( self, state ):
        self.__state = state

    def getAbbreviatedStatus( self ):
        if self.__state in ('C', '?'):
            return ''
        else:
            return self.__state

    def getStagedAbbreviatedStatus( self ):
        # QQQ here for Git compat - bad OO design here
        return ''

    def getUnstagedAbbreviatedStatus( self ):
        # QQQ here for Git compat - bad OO design here
        return self.getAbbreviatedStatus()

    # ------------------------------------------------------------
    def isControlled( self ):
        return self.__nodeid is not None

    def isUncontrolled( self ):
        return self.__state == '?'

    def isIgnored( self ):
        return self.__state == 'I'

    # ------------------------------------------------------------
    def isAdded( self ):
        return self.__state == 'A'

    def isModified( self ):
        return self.__state == 'M'

    def isDeleted( self ):
        return self.__state == 'R'

    # ------------------------------------------------------------
    def canCommit( self ):
        return  self.isAdded() or self.isModified() or self.isDeleted()

    def canAdd( self ):
        return self.isUncontrolled()

    def canRevert( self ):
        return self.isAdded() or self.isModified() or self.isDeleted()

    # ------------------------------------------------------------
    def canDiffHeadVsWorking( self ):
        return self.isModified()

    def getTextLinesWorking( self ):
        path = pathlib.Path( self.__project.projectPath() ) / self.__filepath
        with path.open( encoding='utf-8' ) as f:
            all_lines = f.read().split( '\n' )
            if all_lines[-1] == '':
                return all_lines[:-1]
            else:
                return all_lines

    def getTextLinesHead( self ):
        return self.getTextLinesForRevision( 'tip' )
        text = self.__project.cmdCat( self.__filepath )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

    def getTextLinesForRevision( self, rev ):
        if type( rev ) == int:
            rev = '%d' % (rev,)
        # else its a string like 'tip'

        text = self.__project.cmdCat( self.__filepath, rev=rev )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

class HgCommitLogNode:
    def __init__( self, commit ):
        self.__commit = commit
        self.__all_changes = []

    def _addChanges( self, all_added, all_deleted, all_renamed, all_modified ):
        for name in all_added:
            self.__all_changes.append( ('A', name, '' ) )

        for name in all_deleted:
            self.__all_changes.append( ('D', name, '' ) )

        for name, old_name in all_renamed:
            self.__all_changes.append( ('R', name, old_name ) )

        for name in all_modified:
            self.__all_changes.append( ('M', name, '' ) )

    def commitTree( self ):
        return self.__commit.tree

    def commitPreviousTree( self ):
        if len(self.__commit.parents) == 0:
            return None

        previous_commit = self.__commit.parents[0]
        return previous_commit.tree

    def commitTreeDict( self ):
        all_entries = {}
        self.__treeToDict( self.commitTree(), all_entries )
        return all_entries

    def commitPreviousTreeDict( self ):
        all_entries = {}

        tree = self.commitPreviousTree()
        if tree is not None:
            self.__treeToDict( tree, all_entries )

        return all_entries

    def commitIdString( self ):
        return self.__commit.hexsha

    def commitAuthor( self ):
        return self.__commit.author.name

    def commitAuthorEmail( self ):
        return self.__commit.author.email

    def commitDate( self ):
        return self.__commit.committed_datetime

    def commitMessage( self ):
        return self.__commit.message

    def commitFileChanges( self ):
        return self.__all_changes

class HgProjectTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.is_by_path = False
        self.__path = path
        self.__all_folders = {}
        self.__all_files = {}

    def __repr__( self ):
        return '<HgProjectTreeNode: project %r, path %s>' % (self.project, self.__path)

    def isByPath( self ):
        return self.is_by_path

    def addFileByName( self, path ):
        assert path.name != ''
        self.__all_files[ path.name ] = path

    def addFileByPath( self, path ):
        assert path.name != ''
        self.is_by_path = True
        path = path
        self.__all_files[ path ] = path

    def getAllFileNames( self ):
        return self.__all_files.keys()

    def addFolder( self, name, node ):
        assert type(name) == str and name != '', 'name %r, node %r' % (name, node)
        assert isinstance( node, HgProjectTreeNode )
        self.__all_folders[ name ] = node

    def getFolder( self, name ):
        assert type(name) == str
        return self.__all_folders[ name ]

    def getAllFolderNodes( self ):
        return self.__all_folders.values()

    def getAllFolderNames( self ):
        return self.__all_folders.keys()

    def hasFolder( self, name ):
        assert type(name) == str
        return name in self.__all_folders

    def _dumpTree( self, indent ):
        self.project._debugTree( 'dump: %*s%r' % (indent, '', self) )

        for file in sorted( self.__all_files ):
            self.project._debugTree( 'dump %*s   file: %r' % (indent, '', file) )

        for folder in sorted( self.__all_folders ):
            self.__all_folders[ folder ]._dumpTree( indent+4 )

    def isNotEqual( self, other ):
        return (self.relativePath() != other.relativePath()
            or self.project.isNotEqual( other.project ))

    def __lt__( self, other ):
        return self.name < other.name

    def relativePath( self ):
        return self.__path

    def absolutePath( self ):
        return self.project.projectPath() / self.__path

    def getStatusEntry( self, name ):
        path = self.__all_files[ name ]

        if path in self.project.all_file_state:
            entry = self.project.all_file_state[ path ]

        else:
            entry = WbHgFileState( self.project, None )

        return entry
