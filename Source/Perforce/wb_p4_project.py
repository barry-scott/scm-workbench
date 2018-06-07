'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_project.py

'''
from typing import List
import pathlib
import sys
import os
import pytz
import datetime

import wb_background_thread
import wb_annotate_node

import P4

_p4_version = 'P4 from PyPI'

def P4Version():
    return  _p4_version

class P4Project:
    def __init__( self, app, prefs_project, ui_components ):
        self.app = app
        self.ui_components = ui_components

        self.debugLog = self.app.debug_options.debugLogP4Project
        self.debugLogTree = self.app.debug_options.debugLogP4UpdateTree

        self.prefs_project = prefs_project
        if self.prefs_project is not None:
            # repo will be setup on demand - this speeds up start up especically on macOS
            self.__repo = None
            self.tree = P4ProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )
            self.flat_tree = P4ProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        else:
            self.__repo = P4.P4()
            self.__repo.connect()
            self.tree = None
            self.flat_tree = None

        self.all_file_state = {}

        self.__num_modified_files = 0

    def repo( self ):
        # setup repo on demand
        if self.__repo is None:
            self.__repo = P4.P4()
            self.__repo.connect()
            global _p4_version
            _p4_version = self.__repo.identify().split('\n')[-2]

        return self.__repo

    def scmType( self ):
        return 'p4'

    def switchToBranch( self, branch ):
        pass

    def getBranchName( self ):
        return '-TBD-'

    def getAllBranchNames( self ):
        return [self.getBranchName()]

    def getClientName( self ):
        all_clients = self.repo().run_client( '-o' )
        return all_clients[0]['Client']

    # return a new P4Project that can be used in another thread
    def newInstance( self ):
        raise NotImplementedError('newInstance')

    def isNotEqual( self, other ):
        return self.prefs_project.name != other.prefs_project.name

    def __repr__( self ):
        return '<P4Project: %s>' % (self.prefs_project.name,)

    def projectName( self ):
        return self.prefs_project.name

    def projectPath( self ):
        return self.prefs_project.path

    def headRefName( self ):
        return 'unknown'

    def numModifiedFiles( self ):
        return self.__num_modified_files

    def updateState( self, tree_leaf ):
        self.debugLog( '-'*80 )
        self.debugLog( 'updateState( %r ) repo=%s' % (tree_leaf, self.projectPath()) )

        # rebuild the tree
        self.tree = P4ProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )
        self.flat_tree = P4ProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )

        if not self.projectPath().exists():
            self.app.log.error( T_('Project %(name)s folder %(folder)s has been deleted') %
                            {'name': self.projectName()
                            ,'folder': self.projectPath()} )

            self.all_file_state = {}

        else:
            self.__calculateStatus( tree_leaf )

        for path, file_state in self.all_file_state.items():
            self.__updateTree( path, file_state )

        self.dumpTree()
        self.debugLog( '-'*80 )

    def updateTreeNodeState( self, tree_node ):
        # incrementally update the file state
        self.debugLogTree( 'updateTreeNodeState( %r )' % (tree_node,) )

        self.__calculateFolderStatus( tree_node.absolutePath() )

        for path, file_state in self.all_file_state.items():
            self.__updateTree( path, file_state )

    def __calculateStatus( self, tree_leaf ):
        self.debugLogTree( '__calculateStatus( %s ) ' % (tree_leaf,) )
        self.all_file_state = {}

        repo_root = self.projectPath()

        all_folders = set( [repo_root] )
        abs_path = repo_root / tree_leaf

        while abs_path != repo_root:
            all_folders.add( abs_path )
            abs_path = abs_path.parent

        self.debugLogTree( '__calculateStatus() all_folders %r' % (all_folders,) )

        while len(all_folders) > 0:
            folder = all_folders.pop()
            self.debugLogTree( '__calculateStatus() folder %s' % (folder,) )

            self.__calculateFolderStatus( folder )

    def __calculateFolderStatus( self, folder ):
        self.debugLogTree( '__calculateFolderStatus( %s )' % (folder,) )
        repo_root = self.projectPath()

        # files all the files in the folder
        for filename in folder.iterdir():
            abs_path = folder / filename
            self.debugLogTree( '__calculateFolderStatus() abs_path %s' % (abs_path,) )

            repo_relative = abs_path.relative_to( repo_root )

            if abs_path.is_dir():
                self.all_file_state[ repo_relative ] = WbP4FileState( self, repo_relative )
                self.all_file_state[ repo_relative ].setIsDir()


            else:
                if repo_relative not in self.all_file_state:
                    self.all_file_state[ repo_relative ] = WbP4FileState( self, repo_relative )

        # get the p4 file status for all the files in this folder
        try:
            for fstat in self.repo().run_fstat('-Rc', '%s/*' % (self.pathForP4( folder ),) ):
                # not interested in delete files
                if fstat.get( 'headAction', '' ) in ('delete', 'move/delete'):
                    continue

                abs_path = self.pathForWb( fstat['clientFile'] )
                repo_relative = abs_path.relative_to( repo_root )

                if repo_relative not in self.all_file_state:
                    # filepath has been deleted
                    self.all_file_state[ repo_relative ] = WbP4FileState( self, repo_relative )

                self.all_file_state[ repo_relative ].setFStat( fstat )

        except P4.P4Exception as e:
            self.debugLogTree( '__calculateFolderStatus() fstat error %r' % (e,) )

    def __updateTree( self, path, file_state ):
        self.debugLogTree( '__updateTree( %r, %r )' % (path, file_state) )
        node = self.tree

        self.debugLogTree( '__updateTree path.parts %r' % (path.parts,) )

        for index, name in enumerate( path.parts[0:-1] ):
            self.debugLogTree( '__updateTree name %r at node %r' % (name, node) )

            if not node.hasFolder( name ):
                self.debugLogTree( '__updateTree addFolder 1 %r to node %r' % (name, node) )
                node.addFolder( name, P4ProjectTreeNode( self, name, pathlib.Path( *path.parts[0:index+1] ) ) )

            node = node.getFolder( name )

        if file_state.isDir():
            name = file_state.relativePath().name
            if not node.hasFolder( name ):
                self.debugLogTree( '__updateTree addFolder 2 %r to node %r' % (name, node) )
                node.addFolder( name, P4ProjectTreeNode( self, name, file_state.relativePath() ) )

        self.debugLogTree( '__updateTree addFile %r to node %r' % (path, node) )
        node.addFileByName( path )
        self.flat_tree.addFileByPath( path )

    def dumpTree( self ):
        if self.debugLogTree.isEnabled():
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

            elif file_state.isOpened():
                all_moddified_files.append( (T_('Opened'), filename) )

            elif file_state.isDeleted():
                all_moddified_files.append( (T_('Deleted'), filename) )

        return all_moddified_files

    def getReportUntrackedFiles( self ):
        all_untracked_files = []
        for filename, file_state in self.all_file_state.items():
            if file_state.isUncontrolled():
                all_untracked_files.append( (T_('New file'), filename) )

        return all_untracked_files

    #------------------------------------------------------------
    #
    # all functions starting with "cmd" are like the p4 <cmd> in behavior
    #
    #------------------------------------------------------------
    def dateRevForP4( self, date ):
        return date.strftime('@%Y/%m/%d:%H:%M:%S')

    def pathForP4( self, path ):
        assert isinstance( path, pathlib.Path ), 'path %r' % (path,)
        # return abs path
        if path.is_absolute():
            return str( path )
        else:
            return str( self.projectPath() / path )

    def pathForWb( self, path ):
        assert type( path ) == str
        return pathlib.Path( path )

    def getTextLinesForRevision( self, filepath, rev ):
        if type( rev ) == int:
            rev = '@%d' % (rev,)
        # else its a string like '#head'

        stat, text = self.cmdPrint( filepath, rev=rev )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

    def cmdPrint( self, filename, rev=None ):
        self.debugLog( 'cmdPrint( %r, rev=%r )' % (filename, rev) )
        p4_filepath = self.pathForP4( filename )
        if rev is not None:
            p4_filepath += rev
        stats, text = self.repo().run_print( p4_filepath )
        return stats, text

    def cmdEdit( self, filename ):
        self.repo().run_edit( self.pathForP4( filename ) )

    def cmdAdd( self, filename ):
        self.repo().run_add( self.pathForP4( filename ) )

    def cmdRevert( self, filename ):
        self.repo().run_revert( self.pathForP4( filename ) )

    def cmdDelete( self, filename ):
        self.repo().run_delete( self.pathForP4( filename ) )

    def cmdDiffFolder( self, folder ):
        self.debugLog( 'cmdDiffFolder( %r )' % (folder,) )
        text = self.repo().run_diff( '-du', '%s/...' % (self.pathForP4( folder ),) )
        return text

    def cmdDiffWorkingVsChange( self, folder, change_old ):
        self.debugLog( 'cmdDiffFolder( %r )' % (folder,) )
        diff_list = self.repo().run_diff( '-du', '%s/...@%d' % (self.pathForP4( folder ), change_old) )
        return diff_list

    def cmdDiffChangeVsChange( self, folder, change_old, change_new ):
        self.debugLog( 'cmdDiffFolder( %r )' % (folder,) )
        # diff2 is known to *not* return diff lines ony file diff info
        # run in tagged=False to see the line diffs
        text_list = self.repo().run_diff2( '-du', '%s/...@%d' % (self.pathForP4( folder ), change_old), '%s/...@%d' % (self.pathForP4( folder ), change_new), tagged=False )

        text = []
        for line in text_list:
            if line.startswith('==== ') and line.endswith(' identical'):
                continue

            if '\n' in line:
                text.extend( line.rstrip().split('\n') )
            else:
                text.append( line.rstrip() )


        print( 'text %r' % (text,) )
        return text

    def cmdCommit( self, message ):
        return self.repo().commit( message )

    def cmdAnnotationForFile( self, filename, rev=None ):
        if rev is None:
            rev = '#head'

        all_annotate_nodes = []

        # annotate returns a list that starts with the file info.
        # which we skip. 
        line_num = -1
        for line_info in self.repo().run_annotate( '-c', self.pathForP4( filename ) + rev ):
            line_num += 1
            if line_num == 0:
                continue

            all_annotate_nodes.append(
                wb_annotate_node.AnnotateNode( line_num, line_info['data'], line_info['lower'] ) )

        return all_annotate_nodes

    def cmdChangeLogForAnnotateFile( self, filename, all_revs ):
        all_change_logs = {}

        for desc in self.repo().run_describe( '-s', *all_revs ):
            all_change_logs[ desc['change'] ] = WbP4LogBasic( desc, self.repo() )

        return all_change_logs

    def cmdChangeLogForFolder( self, folder, limit=None, since=None, until=None ):
        repo_root = self.projectPath()

        if since is not None and until is not None:
            cmd = ['%s/...%s,%s' % (folder, self.dateRevForP4( since ), self.dateRevForP4( until ))]

        elif limit is not None:
            cmd = ['-m', limit, '%s/...' % (folder,)]

        else:
            cmd = ['%s/...' % (folder,)]

        try:
            all_logs = [WbP4LogFull( data, self.repo() )
                            for data in self.repo().run_changes( cmd )]
            return all_logs

        except P4.P4Exception as e:
            self.app.log.error( 'p4 changes for %s failed: %r' % (folder, e) )
            return []

    def cmdChangeLogForFile( self, filename, limit=None, since=None, until=None ):
        repo_root = self.projectPath()

        if since is not None and until is not None:
            cmd = ['%s%s,%s' % (self.pathForP4( filename ), self.dateRevForP4( since ), self.dateRevForP4( until ))]

        elif limit is not None:
            cmd = ['-m', limit, self.pathForP4( filename )]

        else:
            cmd = [self.pathForP4( filename )]

        try:
            all_logs = [WbP4LogFull( data, self.repo() )
                            for data in self.repo().run_changes( cmd )]
            return all_logs

        except P4.P4Exception as e:
            self.app.log.error( 'p4 changes for %s failed: %r' % (filename, e) )
            return []

    def cmdTagsForRepository( self ):
        return {}

    def __addChangeChangeInformation( self, all_change_logs ):
        # now calculate what was added, deleted and modified in each change
        for change_log in all_change_logs:
            new_tree = change_log.changeTree()
            old_tree = change_log.changePreviousTree()

            all_new = {}
            self.__treeToDict( new_tree, all_new )
            new_set = set(all_new)

            if old_tree is None:
                change_log._addChanges( new_set, set(), [], set() )

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

                change_log._addChanges( all_added, all_deleted, all_renamed, all_modified )

    # QQQ Is this needed in P4 world? QQQ
    def canPush( self ) -> bool:
        return False

    def cmdOpenedFiles( self ):
        return self.repo().run_opened()

    def cmdChangesPending( self ):
        cmd = ['-u', os.getlogin(), '-s', 'pending', '-c', self.getClientName()]
        return self.repo().run_changes( cmd )

    def cmdChangesShelved( self ):
        cmd = ['-u', os.getlogin(), '-s', 'shelved', '-c', self.getClientName()]
        return self.repo().run_changes( cmd )

class WbP4LogBasic:
    def __init__( self, data, repo ):
        self.change =   int(data['change'])
        self.author =   data['user']
        self.message =  data['desc']
        self.date =     datetime.datetime.fromtimestamp( int(data['time']), tz=pytz.utc )

    def commitMessage( self ):
        return self.message

    def messageFirstLine( self ):
        return self.message.split('\n')[0]

    def commitDate( self ):
        return self.date

    def commitAuthor( self ):
        return self.author

    def commitIdString( self ):
        return '%d' % (self.change,)

class WbP4LogFull(WbP4LogBasic):
    def __init__( self, data, repo ):
        super().__init__( data, repo )

        self.all_changed_files = []
        for data in repo.run_describe( '-s', self.change ):
            action = ','.join( data['action'] )
            for filename in data['depotFile']:
                self.all_changed_files.append( (action, filename) )

class WbP4FileState:
    map_p4_action_to_state = {
        'edit': 'O',
        'add': 'A',
        'delete': 'D',
        '': ''
        }

    def __init__( self, project : P4Project, filepath : 'pathlib.Path' ) -> None:
        project.debugLog('WbP4FileState.__init__( %r )' % (filepath,) )
        self.__project = project
        self.__filepath = filepath
        self.__fstat = {}

        self.__is_dir = False
        self.__is_ignored = project.repo().is_ignored( project.pathForP4( self.__filepath ) )

        if self.__is_ignored:
            self.__state = 'I'          # type: str

        else:
            self.__state = ''           # type: str

    def __repr__( self ) -> str:
        return ('<WbP4FileState: P: %r S: %r P4: %r>' %
                (self.__filepath, self.__state, len(self.__fstat)))

    def setIsDir( self ) -> None:
        self.__is_dir = True

    def isDir( self ) -> bool:
        return self.__is_dir

    def setFStat( self, fstat ) -> None:
        self.__project.debugLog('WbP4FileState.setFStat() %r: fstat: %r' % (self.__filepath, fstat) )
        self.__fstat = fstat
        self.__is_ignored = False
        self.__state = self.map_p4_action_to_state.get( self.__fstat.get( 'action', '' ), '?' )
        self.__project.debugLog('WbP4FileState.setFStat() isControlled %r state %r' % (self.isControlled(), self.__state) )

    def setState( self, state : str ):
        self.__state = state

    def getAbbreviatedStatus( self ) -> str:
        return self.__state

    def getStagedAbbreviatedStatus( self ) -> str:
        # QQQ here for Git compat - bad OO design here
        return ''

    def getUnstagedAbbreviatedStatus( self ) -> str:
        # QQQ here for Git compat - bad OO design here
        return self.getAbbreviatedStatus()

    def absolutePath( self ) -> pathlib.Path:
        return self.__project.projectPath() / self.__filepath

    def relativePath( self ):
        return self.__filepath

    # ------------------------------------------------------------
    def isControlled( self ) -> bool:
        return 'depotFile' in self.__fstat

    def isUncontrolled( self ) -> bool:
        return 'depotFile' not in self.__fstat
        return self.__state == '?'

    def isIgnored( self ) -> bool:
        return self.__state == 'I'

    # ------------------------------------------------------------
    def isAdded( self ) -> bool:
        return self.__state == 'A'

    def isOpened( self ) -> bool:
        return self.__state == 'O'

    def isDeleted( self ) -> bool:
        return self.__state == 'R'

    # ------------------------------------------------------------
    def canCommit( self ) -> bool:
        return  self.isAdded() or self.isOpened() or self.isDeleted()

    def canEdit( self ) -> bool:
        return self.isControlled() and not self.isOpened()

    def canAdd( self ) -> bool:
        return not self.isControlled()

    def canRevert( self ) -> bool:
        return self.isAdded() or self.isOpened() or self.isDeleted()

    # ------------------------------------------------------------
    def canDiffHeadVsWorking( self ) -> bool:
        return self.isOpened()

    def getTextLinesWorking( self ) -> List[str]:
        path = pathlib.Path( self.__project.projectPath() ) / self.__filepath
        with path.open( encoding='utf-8' ) as f:
            all_lines = f.read().split( '\n' )
            if all_lines[-1] == '':
                return all_lines[:-1]
            else:
                return all_lines

    def getTextLinesHead( self ) -> List[str]:
        return self.getTextLinesForRevision( '#head' )

    def getTextLinesForRevision( self, rev ) -> List[str]:
        if type( rev ) == int:
            rev = '%d' % (rev,)
        # else its a string like 'tip'

        stats, text = self.__project.cmdPrint( self.__filepath, rev=rev )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

class P4ChangeLogNode:
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

    def commitMessageHeadline( self ):
        return self.__commit.message.split('\n')[0]

    def commitFileChanges( self ):
        return self.__all_changes

class P4ProjectTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.is_by_path = False
        self.__path = path
        self.__all_folders = {}
        self.__all_files = {}

    def __repr__( self ):
        return '<P4ProjectTreeNode: project %r, path %s>' % (self.project, self.__path)

    def updateTreeNode( self ):
        self.project.updateTreeNodeState( self )

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
        assert isinstance( node, P4ProjectTreeNode )
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
        self.project.debugLogTree( 'dump: %*s%r' % (indent, '', self) )

        for file in sorted( self.__all_files ):
            self.project.debugLogTree( 'dump %*s   file: %r status: %r' % (indent, '', file, self.getStatusEntry( file )) )

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
            entry = WbP4FileState( self.project, None )

        return entry
