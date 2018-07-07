'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_change_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtCore

import wb_main_window
import wb_tracked_qwidget
import wb_ui_components

import wb_scm_table_view


#
#   add tool bars and menu for use in the change window
#
class P4ChangeWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        super().__init__( 'p4', factory )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), act.tableActionP4DiffHeadVsWorking, act.enablerP4DiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('P4 Actions') )
        addMenu( m, T_('Add'), act.tableActionP4Add_Bg, act.enablerP4FilesAdd, 'toolbar_images/include.png' )
        m.addSeparator()
        addMenu( m, T_('Revert'), act.tableActionP4Revert_Bg, act.enablerP4FilesRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), act.tableActionP4Delete_Bg, act.main_window.table_view.enablerTableFilesExists )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('p4 logo'), style='font-size: 20pt; width: 40px; color: #cc0000' )
        self.all_toolbars.append( t )

        addTool( t, 'P4', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        act = self.ui_actions

        # ----------------------------------------
        t = addToolBar( T_('p4 info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), act.tableActionP4DiffSmart, act.enablerP4DiffSmart, 'toolbar_images/diff.png' )
        addTool( t, T_('Change History'), act.tableActionP4LogHistory_Bg, act.enablerP4LogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('p4 state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), act.tableActionP4Add_Bg, act.enablerP4FilesAdd, 'toolbar_images/include.png' )
        addTool( t, T_('Revert'), act.tableActionP4Revert_Bg, act.enablerP4FilesRevert, 'toolbar_images/revert.png' )

class WbP4ChangeDialog(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    changeAccepted = QtCore.pyqtSignal()
    changeClosed = QtCore.pyqtSignal()

    def __init__( self, app, p4_project, changespec=None ):
        self.__pyqt_bug_already_closed_why_call_close_event_again = False

        if changespec is not None:
            self.changespec = changespec
        else:
            self.changespec = p4_project.cmdFetchChange()

        self.app = app
        self.p4_project = p4_project
        self.table_view = None

        super().__init__( app, app.debug_options.debugLogMainWindow )
        wb_tracked_qwidget.WbTrackedModeless.__init__( self )

        self.ui_component = P4ChangeWindowComponents( self.app.getScmFactory( 'p4' ) )

        self.setWindowTitle( T_('Change %(project_name)s - %(app_name)s') %
                                {'project_name': p4_project.projectName()
                                ,'app_name': ' '.join( app.app_name_parts )} )
        self.setWindowIcon( self.app.getAppQIcon() )

        # on Qt on macOS table will trigger selectionChanged that needs table_model
        self.table_view = wb_scm_table_view.WbScmTableView( self.app, self )

        self.all_included_files = set()
        self.table_view.setIncludedFilesSet( self.all_included_files )

        # unchanged files should not be interesting for a change
        self.table_view.setShowControlledAndNotChangedFiles( False )

        self.ui_component.setTopWindow( self.app.top_window )
        self.ui_component.setMainWindow( self, self.table_view )

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.__setupTableContextMenu()

        # ----------------------------------------
        self.filter_text = QtWidgets.QLineEdit()
        self.filter_text.setClearButtonEnabled( True )
        self.filter_text.setMaxLength( 256 )
        self.filter_text.setPlaceholderText( T_('Filter by name') )

        self.filter_text.textChanged.connect( self.table_view.table_sortfilter.setFilterText )

        self.h_filter_layout = QtWidgets.QHBoxLayout()
        self.h_filter_widget = QtWidgets.QWidget()
        self.h_filter_widget.setLayout( self.h_filter_layout )

        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Filter:') ), 0 )
        self.h_filter_layout.addWidget( self.filter_text, 1 )

        self.v_table_layout = QtWidgets.QVBoxLayout()
        self.v_table_layout.addWidget( self.h_filter_widget )
        self.v_table_layout.addWidget( self.table_view )

        self.v_table_widget = QtWidgets.QWidget()
        self.v_table_widget.setLayout( self.v_table_layout )

        self.label_message = QtWidgets.QLabel( T_('Change Log Message') )
        self.message = QtWidgets.QPlainTextEdit( self.changespec['Description'] )

        self.v_message_layout = QtWidgets.QVBoxLayout()
        self.v_message_layout.addWidget( self.label_message )
        self.v_message_layout.addWidget( self.message )
        self.v_message_widget = QtWidgets.QWidget()
        self.v_message_widget.setLayout( self.v_message_layout )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        # ----------------------------------------
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )
        self.v_split.addWidget( self.v_message_widget )
        self.v_split.addWidget( self.v_table_widget )

        # ----------------------------------------
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.v_split )
        self.layout.addWidget( self.buttons )

        # ----------------------------------------
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout( self.layout )

        self.setCentralWidget( self.widget )

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 100*em, 50*ex )

        self.ok_button.setEnabled( False )

        # connections
        self.buttons.accepted.connect( self.handleAccepted )
        self.buttons.rejected.connect( self.close )

        self.message.textChanged.connect( self.enableOkButton )

    def completeInit( self ):
        self.debugLog( 'completeInit()' )

        # set focus
        self.message.setFocus()

        self.updateTableView()

        # Qt has a habit of resetting the column widths
        # completeInit will set to the designed width
        self.table_view.completeInit()

        # set splitter position
        table_size_ratio = 0.3
        height = sum( self.v_split.sizes() )
        table_height = int( height * table_size_ratio )
        message_height = height - table_height
        self.v_split.setSizes( [table_height, message_height] )

        self.updateActionEnabledStates()

    def setupMenuBar( self, mb ):
        m = mb.addMenu( T_('&View') )
        tv = self.table_view
        self._addMenu( m, T_('Show Controlled and Changed files'), tv.setShowControlledAndChangedFiles, checker=tv.checkerShowControlledAndChangedFiles )
        self._addMenu( m, T_('Show Controlled and Not Changed files'), tv.setShowControlledAndNotChangedFiles, checker=tv.checkerShowControlledAndNotChangedFiles )
        self._addMenu( m, T_('Show Uncontrolled files'), tv.setShowUncontrolledFiles, checker=tv.checkerShowUncontrolledFiles )
        self._addMenu( m, T_('Show Ignored files'), tv.setShowIgnoredFiles, checker=tv.checkerShowIgnoredFiles )

        m = mb.addMenu( T_('File &Actions') )
        self._addMenu( m, T_('Edit'), self.table_view.tableActionEdit, self.table_view.enablerTableFilesExists, 'toolbar_images/edit.png' )
        self._addMenu( m, T_('Open'), self.table_view.tableActionOpen, self.table_view.enablerTableFilesExists, 'toolbar_images/open.png' )

        self.ui_component.setupMenuBar( mb, self._addMenu )

    def __setupTableContextMenu( self ):
        self.debugLog( '__setupTableContextMenu' )

        # --- setup scm_type specific menu

        m = QtWidgets.QMenu( self )

        m.addSection( T_('File Actions') )
        self._addMenu( m, T_('Edit'), self.table_view.tableActionEdit, self.table_view.enablerTableFilesExists, 'toolbar_images/edit.png' )
        self._addMenu( m, T_('Open'), self.table_view.tableActionOpen, self.table_view.enablerTableFilesExists, 'toolbar_images/open.png' )

        self.ui_component.setupTableContextMenu( m, self._addMenu )

    def setupToolBar( self ):
        # --- setup common toolbars
        t = self.tool_bar_table = self._addToolBar( T_('table') )
        self._addTool( t, T_('Edit'), self.table_view.tableActionEdit, self.table_view.enablerTableFilesExists, 'toolbar_images/edit.png' )
        self._addTool( t, T_('Open'), self.table_view.tableActionOpen, self.table_view.enablerTableFilesExists, 'toolbar_images/open.png' )

        # --- setup scm_type specific tool bars
        self.ui_component.setupToolBarAtRight( self._addToolBar, self._addTool )

    def closeEvent( self, event ):
        super().closeEvent( event )

        if self.__pyqt_bug_already_closed_why_call_close_event_again:
            return

        self.__pyqt_bug_already_closed_why_call_close_event_again = True

        self.changeClosed.emit()

    def handleAccepted( self ):
        self.changespec['Description'] = self.getMessage()
        self.changeAccepted.emit()

    def enableOkButton( self ):
        text = self.message.toPlainText()
        self.ok_button.setEnabled( text.strip() != '' )

    def getMessage( self ):
        return self.message.toPlainText().strip()

    def getChangeSpec( self ):
        return self.changespec

    def updateSingleton( self ):
        self.updateTableView()

    def updateTableView( self ):
        # caller will have updated the p4 project state already
        self.table_view.setScmProjectTreeNode( self.p4_project.flat_tree )

    def isScmTypeActive( self, scm_type ):
        return scm_type == 'p4'

    def updateActionEnabledStates( self ):
        # can be called during __init__ on macOS version
        if self.table_view is None or self.table_view.table_model is None:
            return

        self.updateEnableStates()
        self.enableOkButton()
