import wb_git_project
import sys

import logging

logging.basicConfig(filename='experiment.log',level=logging.DEBUG)

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

print( 'Root: folders %r' % (proj.tree.getAllFolderNames(),) )

def printText( title, all_lines ):
    print( '            %s' % (title,) )
    print( '            %s' % ('-'* len(title),) )
    for index, line in enumerate( all_lines ):
        print( '            %-2d: %s' % (index+1, line) )

for folder_name in sorted( proj.tree.getAllFolderNames() ):
    print( 'Folder: %s' % (folder_name,) )

    folder = proj.tree.getFolder( folder_name )
    for filename in sorted( folder.getAllFileNames() ):
        print( '    ----: ----------------------------------------' )
        print( '    File: %s' % (filename,) )
        file_state = folder.getStatusEntry( filename )
        print( '                          ----: -----' )
        print( '                 Staged status: %r' % (file_state.getStagedAbbreviatedStatus(),) )
        print( '               Unstaged status: %r' % (file_state.getUnstagedAbbreviatedStatus(),) )
        print( '                   IsUntracked: %r' % (file_state.isUntracked(),) )
        print( '                          ----: -----' )
        print( '           canDiffHeadVsStaged: %r' % (file_state.canDiffHeadVsStaged(),) )
        print( '        canDiffStagedVsWorking: %r' % (file_state.canDiffStagedVsWorking(),) )
        print( '          canDiffHeadVsWorking: %r' % (file_state.canDiffHeadVsWorking(),) )
        print( '                          ----: -----' )
        print( '                      HeadBlob: %r' % (file_state.getHeadBlob(),) )
        print( '                    StagedBlob: %r' % (file_state.getStagedBlob(),) )

        if file_state.canDiffHeadVsWorking():
            print( '                          ----: -----' )
            printText( 'Old HEAD', file_state.getTextLinesHead() )
            printText( 'New Working', file_state.getTextLinesWorking() )

        if file_state.canDiffStagedVsWorking():
            print( '                          ----: -----' )
            printText( 'Old Staged', file_state.getTextLinesStaged() )
            printText( 'New Working', file_state.getTextLinesWorking() )

        if file_state.canDiffHeadVsStaged():
            print( '                          ----: -----' )
            printText( 'Old HEAD', file_state.getTextLinesHead() )
            printText( 'New Staged', file_state.getTextLinesStaged() )

