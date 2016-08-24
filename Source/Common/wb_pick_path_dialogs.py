'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_pick_path_dialogs.py

'''
import pathlib

import wb_platform_specific

from PyQt5 import QtWidgets
from PyQt5 import QtCore

def pickExecutable( parent, executable ):
    file_browser = QtWidgets.QFileDialog( parent )
    file_browser.setFileMode( file_browser.ExistingFile )
    file_browser.setOption( file_browser.ReadOnly, True )
    file_browser.setOption( file_browser.DontResolveSymlinks, True )
    file_browser.setViewMode( file_browser.Detail )
    # Without Readable will not return a Executable image
    file_browser.setFilter( QtCore.QDir.Files|QtCore.QDir.Executable|QtCore.QDir.Readable )

    if executable is not None and executable.name != '':
        file_browser.setDirectory( str( executable.parent ) )
        file_browser.selectFile( str( executable.name ) )

    else:
        file_browser.setDirectory( str(wb_platform_specific.getDefaultExecutableFolder()) )

    if file_browser.exec_():
        all_files = file_browser.selectedFiles()
        assert len(all_files) == 1
        return all_files[0]

    else:
        return None

def pickFolder( parent, folder ):
    if folder is None or folder == '.':
        folder = wb_platform_specific.getHomeFolder()

    if not folder.exists():
        folder = wb_platform_specific.getHomeFolder()

    if not folder.is_dir():
        folder = folder.parent

    file_browser = QtWidgets.QFileDialog( parent )
    file_browser.setFileMode( file_browser.Directory )

    #
    # When ShowDirsOnly is True QFileDialog show a number of
    # bugs:
    # 1. folder double click edits folder name
    # 2. setDirectory does not work, always starts in $HOME
    #
    file_browser.setOption( file_browser.ShowDirsOnly, False )
    file_browser.setOption( file_browser.ReadOnly, True )
    file_browser.setViewMode( file_browser.Detail )
    file_browser.setFilter( QtCore.QDir.Hidden | QtCore.QDir.Dirs )

    file_browser.setDirectory( str( folder ) )
    file_browser.selectFile( str( folder ) )

    if file_browser.exec_():
        all_directories = file_browser.selectedFiles()
        assert len(all_directories) == 1
        return pathlib.Path( all_directories[0] )

    return None

if __name__ == '__main__':
    import sys
    import pathlib

    app = QtWidgets.QApplication( ['foo'] )

    exe = None
    if len(sys.argv) > 1:
        exe = pathlib.Path( sys.argv[1] )

    print( ' in: %r' % (exe,) )
    exe = pickExecutable( None, exe )
    print( 'out: %r' % (exe,) )
    del app
