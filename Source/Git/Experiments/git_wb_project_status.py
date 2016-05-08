import wb_git_project
import sys

class FakePrefs:
    def __init__( self ):
        self.name = 'TestRepo'
        self.path = sys.argv[1]

class FakeApp:
    def __init__( self ):
        pass

    def _debugGitProject( self, msg ):
        print( 'debug: %s' % (msg,) )


proj = wb_git_project.GitProject( FakeApp(), FakePrefs() )
proj.updateState()

print( 'Root: folders %r' % (proj.tree.all_folders.keys(),) )

for folder_name in sorted( proj.tree.all_folders.keys() ):
    print( 'Folder: %s' % (folder_name,) )

    folder = proj.tree.all_folders[ folder_name ]
    for filename in sorted( folder.all_files ):
        print( '--------: ----------------------------------------' )
        print( '    File: %s' % (filename,) )
        file_state = folder.getStatusEntry( filename )
        print( '                   index_entry: %r' % (file_state.index_entry,) )
        print( '                 unstaged_diff: %r' % (file_state.unstaged_diff,) )
        print( '                   staged_diff: %r' % (file_state.staged_diff,) )
        print( '                          ----: -----' )
        print( '                 Staged status: %r' % (file_state.getStagedAbbreviatedStatus(),) )
        print( '               Unstaged status: %r' % (file_state.getUnstagedAbbreviatedStatus(),) )
        print( '                   IsUntracked: %r' % (file_state.isUntracked(),) )
        print( '           canDiffHeadVsStaged: %r' % (file_state.canDiffHeadVsStaged(),) )
        print( '        canDiffStagedVsWorking: %r' % (file_state.canDiffStagedVsWorking(),) )
        print( '          canDiffHeadVsWorking: %r' % (file_state.canDiffHeadVsWorking(),) )
        print( '                      HeadBlob: %r' % (file_state.getHeadBlob(),) )
        print( '                    StagedBlob: %r' % (file_state.getStagedBlob(),) )
