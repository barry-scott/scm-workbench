#!/usr/bin/python3
'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_factory_abc.py

'''
from typing import List, Tuple, Sequence

from abc import ABCMeta, abstractmethod

class WbScmFactoryABC(metaclass=ABCMeta):
    def __init__( self ):
        pass

    @abstractmethod
    def scmName( self ) -> str:
        pass

    @abstractmethod
    def scmPresentationShortName( self ) -> str:
        pass

    @abstractmethod
    def scmPresentationLongName( self ) -> str:
        pass

    @abstractmethod
    def uiComponents( self ) -> 'WbScmUiComponentsABC':
        pass

    @abstractmethod
    def uiActions( self ) -> 'WbScmUiActionsABC':
        pass

    @abstractmethod
    def projectSettingsDialog( self, app, main_window :'WbMainWindow', prefs_project, scm_project ) -> 'wb_scm_project_dialogs.ProjectSettingsDialog':
        pass

    @abstractmethod
    def projectDialogClonePages( self, wizard:'WbScmAddProjectWizard' ) -> List['QtWidgets.QWizardPage']:
        pass

    @abstractmethod
    def projectDialogInitPages( self, wizard:'WbScmAddProjectWizard' ) -> List['QtWidgets.QWizardPage']:
        pass

    @abstractmethod
    def folderDetection( self ) -> List[Tuple[str,str]]:
        pass

    @abstractmethod
    def logHistoryView( self, app:'WbApp', title:str ) -> 'wb_main_window.WbMainWindow':
        pass
