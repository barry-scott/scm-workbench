'''

 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_pick_path_dialogs.py

'''
import pathlib

import wb_platform_specific

from PyQt6 import QtWidgets
from PyQt6 import QtCore

def pickExecutable( parent, executable ):
    file_browser = QtWidgets.QFileDialog( parent )
    file_browser.setFileMode( file_browser.FileMode.ExistingFile )
    file_browser.setOption( file_browser.Option.ReadOnly, True )
    file_browser.setOption( file_browser.Option.DontResolveSymlinks, True )
    file_browser.setViewMode( file_browser.ViewMode.Detail )
    # Without Readable will not return a Executable image
    file_browser.setFilter( QtCore.QDir.Filter.Files|QtCore.QDir.Filter.Executable|QtCore.QDir.Filter.Readable )

    if executable is not None and executable.name != '':
        file_browser.setDirectory( str( executable.parent ) )
        file_browser.selectFile( str( executable.name ) )

    else:
        file_browser.setDirectory( str(wb_platform_specific.getDefaultExecutableFolder()) )

    if file_browser.exec():
        all_files = file_browser.selectedFiles()
        assert len(all_files) == 1
        return all_files[0]

    else:
        return None

def pickFolder( parent, orig_folder ):
    if orig_folder is None or orig_folder == '.':
        orig_folder = wb_platform_specific.getHomeFolder()

    folder = orig_folder

    if folder.exists():
        if not folder.is_dir():
            folder = folder.parent

    else:
        while not orig_folder.exists():
            orig_folder = orig_folder.parent

    file_browser = QtWidgets.QFileDialog( parent )
    file_browser.setFileMode( file_browser.FileMode.Directory )

    #
    # When ShowDirsOnly is True QFileDialog show a number of
    # bugs:
    # 1. folder double click edits folder name
    # 2. setDirectory does not work, always starts in $HOME
    #
    file_browser.setOption( file_browser.Option.ShowDirsOnly, False )
    file_browser.setOption( file_browser.Option.ReadOnly, True )
    file_browser.setViewMode( file_browser.ViewMode.Detail )
    file_browser.setFilter( QtCore.QDir.Filter.Hidden | QtCore.QDir.Filter.Dirs )

    file_browser.setDirectory( str( folder ) )
    file_browser.selectFile( str( orig_folder ) )

    if file_browser.exec():
        all_directories = file_browser.selectedFiles()
        assert len(all_directories) == 1
        return pathlib.Path( all_directories[0] )

    return None

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication( ['foo'] )

    exe = None
    if len(sys.argv) > 1:
        exe = pathlib.Path( sys.argv[1] )

    print( ' in: %r' % (exe,) )
    exe = pickExecutable( None, exe )
    print( 'out: %r' % (exe,) )
    del app
