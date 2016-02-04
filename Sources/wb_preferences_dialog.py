'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_preferences_dialog.py

'''
import wx
import wb_exceptions
import os
import wb_subversion_list_handler_common
import wb_shell_commands
import wb_dialogs
import wb_tree_panel
import wb_toolbars
import wb_platform_specific

class PreferencesDialog( wx.Dialog ):
    def __init__( self, parent, app ):
        wx.Dialog.__init__( self, parent, -1, T_('Preferences'), size=(400,200) )
        self.app = app
        self.v_sizer = None

        # useful for debugging new pages
        try:
            self.initControls()
        except:
            app.log.exception( T_('PreferencesDialog') )

        self.SetSizer( self.v_sizer )
        self.Layout()
        self.Fit()

        self.CentreOnParent()

    def initControls( self ):
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.notebook = wx.Notebook( self )

        self.v_sizer.Add( self.notebook, 0, wx.EXPAND|wx.ALL, 5 )

        self.pages = []
        self.pages.append( EditorPage( self.notebook, self.app ) )
        self.pages.append( DiffToolPage( self.notebook, self.app ) )
        self.pages.append( ShellPage( self.notebook, self.app ) )
        self.pages.append( ListColumnsPage( self.notebook, self.app ) )
        self.pages.append( LogHistoryPage( self.notebook, self.app ) )
        self.pages.append( ToolbarPage( self.notebook, self.app ) )
        # may want view page for editing the control file
        #self.pages.append( ViewPage( self.notebook, self.app ) )
        self.pages.append( AdvancedPage( self.notebook, self.app ) )


        self.button_ok = wx.Button( self, wx.ID_OK, T_(' OK ') )
        self.button_ok.SetDefault()
        self.button_cancel = wx.Button( self, wx.ID_CANCEL, T_(' Cancel ') )

        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer.Add( (1, 1), 1, wx.EXPAND )
        self.h_sizer.Add( self.button_ok, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer.Add( self.button_cancel, 0, wx.EXPAND|wx.EAST, 2 )

        self.v_sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.ALL, 5 )

        wx.EVT_BUTTON( self, wx.ID_OK, self.OnOk )
        wx.EVT_BUTTON( self, wx.ID_CANCEL, self.OnCancel )

    def OnOk( self, event ):
        for page in self.pages:
            if not page.validate():
                return

        for page in self.pages:
            page.savePreferences()

        self.EndModal( wx.ID_OK )

    def OnCancel( self, event ):
        self.EndModal( wx.ID_CANCEL )
    

class PagePanel(wx.Panel):
    def __init__( self, notebook, title ):
        wx.Panel.__init__( self, notebook, -1, style = wx.NO_BORDER )

        self.page_v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.page_v_sizer.Add( self.initControls(), 0, wx.EXPAND|wx.ALL, 5 )
        self.SetSizer( self.page_v_sizer )
        self.SetAutoLayout( True )
        self.page_v_sizer.Fit( self )
        self.Layout()

        notebook.AddPage( self, title )

    def initControls( self ):
        raise wb_exceptions.InternalError('must override initControls')

class EditorPage(PagePanel):
    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('Editor') )

    def initControls( self ):
        p = self.app.prefs.getEditor()

        self.static_text1 = wx.StaticText( self, -1, T_('Editor: '), style=wx.ALIGN_RIGHT)
        self.text_ctrl_editor = wx.TextCtrl( self, -1, p.editor_image, wx.DefaultPosition, wx.Size(415, -1) )

        self.static_text2 = wx.StaticText( self, -1, T_('Edit Arguments: '), style=wx.ALIGN_RIGHT)
        self.text_ctrl_edit_arg = wx.TextCtrl( self, -1, p.editor_options, wx.DefaultPosition, wx.Size(315, -1) )

        self.browse_button = wx.Button( self, -1, T_(' Browse... '))

        self.grid_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.grid_sizer.AddGrowableCol( 1 )

        self.grid_sizer.Add( self.static_text1, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.text_ctrl_editor, 0, wx.EXPAND|wx.ALL, 5 )
        self.grid_sizer.Add( self.browse_button, 0, wx.EXPAND )

        self.grid_sizer.Add( self.static_text2, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.text_ctrl_edit_arg, 0, wx.EXPAND|wx.ALL, 5 )
        self.grid_sizer.Add( (1, 1), 0, wx.EXPAND )

        wx.EVT_BUTTON( self, self.browse_button.GetId(), self.OnBrowseExe )

        return self.grid_sizer

    def savePreferences( self ):
        p = self.app.prefs.getEditor()

        p.editor_image = self.text_ctrl_editor.GetValue()
        p.editor_options = self.text_ctrl_edit_arg.GetValue()


    def OnBrowseExe( self, event ):
        if sys.platform == 'win32':
            file_type = T_('Executable files (*.exe)|*.exe')

        elif sys.platform == 'darwin':
            file_type = T_('Applications|*.app|Executable files|*')

        else:
            file_type = T_('Executable files|*')

        filename = self.text_ctrl_editor.GetValue()
        file_dialog = wx.FileDialog( 
            self,
            T_('Choose an Executable file'),
            os.path.dirname( filename ),
            os.path.basename( filename ),
            file_type,
            wx.OPEN )

        if file_dialog.ShowModal() == wx.ID_OK:
            self.text_ctrl_editor.SetValue( file_dialog.GetPath() )

        file_dialog.Destroy()

    def validate( self ):
        # allow no editor
        if len(self.text_ctrl_editor.GetValue()) == 0:
            return True

        # otherwise it must exist
        valid = False
        if sys.platform == 'darwin':
            valid = (os.access( self.text_ctrl_editor.GetValue(), os.X_OK )
                    or not os.path.isdir( self.text_ctrl_editor.GetValue() ) )

        elif sys.platform == 'win32':
            valid = (os.path.exists( self.text_ctrl_editor.GetValue() )
                    or not os.path.isdir( self.text_ctrl_editor.GetValue() ) )

        else:
            valid = (os.access( self.text_ctrl_editor.GetValue(), os.X_OK )
                    or not os.path.isdir( self.text_ctrl_editor.GetValue() ) )

        if not valid:
            wx.MessageBox(
                T_('You must enter a valid editor executable'),
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return False

        return True

class DiffToolPage(PagePanel):
    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('Diff Tool') )

    def initControls( self ):
        p = self.app.prefs.getDiffTool()
        
        self.mode_values = ['built-in', 'external-gui-diff', 'external-shell-diff', 'svn-diff']
        self.diff_tools = {'built-in': '', 'external-gui-diff': p.gui_diff_tool, 'external-shell-diff': p.shell_diff_tool, 'svn-diff': ''}
        self.options = {'built-in': '', 'external-gui-diff': p.gui_diff_tool_options, 'external-shell-diff': p.shell_diff_tool_options, 'svn-diff': ''}
        self.mode_choice_values = [T_('Work Bench Diff'), T_('External GUI Diff Command'), T_('External Text Diff'), T_('SVN diff')]
        self.mode_choice = wx.Choice( self, -1, choices = self.mode_choice_values )
        if p.diff_tool_mode not in self.mode_values:
            p.diff_tool_mode = 'built-in'
        self.mode = p.diff_tool_mode
        self.mode_choice.SetSelection( self.mode_values.index( p.diff_tool_mode ) )
        self.text_ctrl_diff_tool = wx.TextCtrl( self, -1, self.diff_tools[self.mode], wx.DefaultPosition, wx.Size(415, -1) )
        self.text_ctrl_options = wx.TextCtrl( self, -1, self.options[self.mode], wx.DefaultPosition, wx.Size(315, -1) )

        self.browse_button = wx.Button( self, -1, T_(' Browse... ') )

        self.grid_sizer = wx.FlexGridSizer( 0, 3, 0, 0 )
        self.grid_sizer.AddGrowableCol( 1 )

        self.grid_sizer.Add( wx.StaticText( self, -1, T_('Mode: '), style=wx.ALIGN_RIGHT), 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.mode_choice, 0, wx.ALIGN_LEFT, 5 )
        self.grid_sizer.Add( (1, 1), 0, wx.EXPAND )
        
        self.grid_sizer.Add( wx.StaticText( self, -1, T_('Diff Tool: '), style=wx.ALIGN_RIGHT), 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.text_ctrl_diff_tool, 0, wx.EXPAND|wx.ALL, 5 )
        self.grid_sizer.Add( self.browse_button, 0, wx.EXPAND )

        self.grid_sizer.Add( wx.StaticText( self, -1, T_('Tool Arguments: '), style=wx.ALIGN_RIGHT), 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.text_ctrl_options, 0, wx.EXPAND|wx.ALL, 5 )
        self.grid_sizer.Add( (1, 1), 0, wx.EXPAND )

        self.grid_sizer.Add( wx.StaticText( self, -1, T_('Use'), style=wx.ALIGN_RIGHT), 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( wx.StaticText( self, -1, T_('%nl for left file name, %nr for right file name,\n%tl for left title, %tr for right title'),
                                           style=wx.ALIGN_LEFT), 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( (1, 1), 0, wx.EXPAND )
        
        self.OnModeChange( None )

        wx.EVT_CHOICE( self, self.mode_choice.GetId(), self.OnModeChange )
        wx.EVT_BUTTON( self, self.browse_button.GetId(), self.OnBrowseExe )

        return self.grid_sizer

    def savePreferences( self ):
        self.OnModeChange( None )

        p = self.app.prefs.getDiffTool()
        p.gui_diff_tool = self.diff_tools['external-gui-diff']
        p.shell_diff_tool = self.diff_tools['external-shell-diff']
        p.gui_diff_tool_options = self.options['external-gui-diff']
        p.shell_diff_tool_options = self.options['external-shell-diff']
        p.diff_tool_mode = self.mode

        if p.diff_tool_mode == 'external-gui-diff' and p.gui_diff_tool == '':
            p.diff_tool_mode = 'built-in'
        if p.diff_tool_mode == 'external-shell-diff' and p.shell_diff_tool == '':
            p.diff_tool_mode = 'built-in'

    def OnModeChange( self, event ):
        self.diff_tools[self.mode] = self.text_ctrl_diff_tool.GetValue()
        self.options[self.mode] = self.text_ctrl_options.GetValue()
        self.mode = self.mode_values[self.mode_choice.GetSelection()]
        self.text_ctrl_diff_tool.SetValue( self.diff_tools[self.mode] )
        self.text_ctrl_options.SetValue( self.options[self.mode] )
        external_command = self.mode in ('external-gui-diff', 'external-shell-diff')
        self.text_ctrl_diff_tool.Enable( external_command )
        self.browse_button.Enable( external_command )
        self.text_ctrl_options.Enable( external_command )

    def OnBrowseExe( self, event ):
        if sys.platform == 'win32':
            file_type = T_('Executable files (*.exe)|*.exe')

        elif sys.platform == 'darwin':
            file_type = T_('Applications|*.app|Executable files|*')

        else:
            file_type = T_('Executable files|*')

        filename = self.text_ctrl_diff_tool.GetValue()
        file_dialog = wx.FileDialog(
            self,
            T_('Choose an Executable file'),
            os.path.dirname( filename ),
            os.path.basename( filename ),
            file_type,
            wx.OPEN )

        if file_dialog.ShowModal() == wx.ID_OK:
            self.text_ctrl_diff_tool.SetValue( file_dialog.GetPath() )

        file_dialog.Destroy()

    def validate( self ):
        return True

class ShellPage(PagePanel):
    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('Shell') )

    def initControls( self ):
        p = self.app.prefs.getShell()

        self.static_text1 = wx.StaticText( self, -1, T_('Terminal Init Command: '), style=wx.ALIGN_RIGHT)
        self.text_ctrl_shell_init_command = wx.TextCtrl( self, -1, p.shell_init_command, wx.DefaultPosition, wx.Size(300, -1) )

        self.grid_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.grid_sizer.AddGrowableCol( 1 )

        terminal_program_list = wb_shell_commands.getTerminalProgramList()
        if len(terminal_program_list) > 0:
            self.static_text2 = wx.StaticText( self, -1, T_('Terminal Program: '), style=wx.ALIGN_RIGHT)
            self.terminal_program_list_ctrl = wx.Choice( self, -1, choices=terminal_program_list, size=(150,-1) )
            if p.shell_terminal in terminal_program_list:
                self.terminal_program_list_ctrl.SetStringSelection( p.shell_terminal )
            else:
                self.terminal_program_list_ctrl.SetStringSelection( terminal_program_list[0] )
            self.grid_sizer.Add( self.static_text2, 1, wx.EXPAND|wx.ALL, 3 )
            self.grid_sizer.Add( self.terminal_program_list_ctrl, 0, wx.EXPAND|wx.ALL, 3 )
        else:
            self.terminal_program_list_ctrl = None

        self.grid_sizer.Add( self.static_text1, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.text_ctrl_shell_init_command, 0, wx.EXPAND|wx.ALL, 3 )

        file_browser_program_list = wb_shell_commands.getFileBrowserProgramList()

        if len(file_browser_program_list) > 0:
            self.static_text3 = wx.StaticText( self, -1, T_('File Browser Program: '), style=wx.ALIGN_RIGHT)
            self.file_browser_program_list_ctrl = wx.Choice( self, -1, choices=file_browser_program_list, size=(150,-1) )
            if p.shell_file_browser in file_browser_program_list:
                self.file_browser_program_list_ctrl.SetStringSelection( p.shell_file_browser )
            else:
                self.file_browser_program_list_ctrl.SetStringSelection( file_browser_program_list[0] )
            self.grid_sizer.Add( self.static_text3, 1, wx.EXPAND|wx.ALL, 3 )
            self.grid_sizer.Add( self.file_browser_program_list_ctrl, 0, wx.EXPAND|wx.ALL, 3 )
        else:
            self.file_browser_program_list_ctrl = None

        self.grid_sizer.Add( (1, 1), 0, wx.EXPAND )

        return self.grid_sizer

    def savePreferences( self ):
        p = self.app.prefs.getShell()

        p.shell_init_command = self.text_ctrl_shell_init_command.GetValue().encode('UTF-8')
        if self.file_browser_program_list_ctrl is not None:
            p.shell_file_browser = self.file_browser_program_list_ctrl.GetStringSelection().encode('UTF-8')
        if self.terminal_program_list_ctrl is not None:
            p.shell_terminal = self.terminal_program_list_ctrl.GetStringSelection().encode('UTF-8')

    def validate( self ):
        return True

class ViewPage(PagePanel):
    id_add = wx.NewId()
    id_del = wx.NewId()
    id_filename_list = wx.NewId()
    id_pattern_text = wx.NewId()

    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('View') )
        self.selected_item = None

    def initControls( self ):
        p = self.app.prefs.getView()

        self.filename_list = wx.ListCtrl( self, ViewPage.id_filename_list, wx.DefaultPosition,
                wx.Size( -1, 100 ), wx.LC_REPORT )
        self.filename_list.InsertColumn( 0, T_('Exclude filename') )
        self.filename_list.SetColumnWidth( 0, 400 )

        for index, filename in enumerate( p.excluded_filenames_list ):
            self.filename_list.InsertStringItem( index, filename )

        self.button_add = wx.Button( self, ViewPage.id_add, T_(' Add ') )
        self.button_add.Enable( False )
        self.button_del = wx.Button( self, ViewPage.id_del, T_(' Delete ') )
        self.button_del.Enable( False )
        self.pattern_text_ctrl = wx.TextCtrl( self, ViewPage.id_pattern_text, '',
                wx.DefaultPosition, wx.Size(200, -1), style=wx.TE_PROCESS_ENTER )

        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer.Add( self.button_add, 0, wx.EXPAND|wx.EAST, 15 )
        self.h_sizer.Add( self.pattern_text_ctrl, 0, wx.EXPAND|wx.EAST, 5 )
        self.h_sizer.Add( self.button_del, 0, wx.EXPAND|wx.EAST, 5 )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.filename_list, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.h_sizer, 0, wx.EXPAND|wx.EAST, 5 )

        wx.EVT_TEXT( self, ViewPage.id_pattern_text, self.OnPatternTextChanged )
        wx.EVT_TEXT_ENTER( self, ViewPage.id_pattern_text, self.OnPatternTextEnter )

        wx.EVT_BUTTON( self, ViewPage.id_add, self.OnAdd )
        wx.EVT_BUTTON( self, ViewPage.id_del, self.OnDel )

        wx.EVT_LIST_ITEM_SELECTED( self, ViewPage.id_filename_list, self.OnPatternSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self, ViewPage.id_filename_list, self.OnPatternDeselected )

        return self.v_sizer

    def sortList( self, item1, item2 ):
        return cmp( self.filename_list.GetItemText( item1 ),
                self.filename_list.GetItemText( item2 ) )

    def OnAdd( self, event ):
        pattern = self.pattern_text_ctrl.GetValue()
        if self.selected_item is None:
            self.filename_list.InsertStringItem( 0, pattern )
        else:
            self.filename_list.SetItemText( self.selected_item, pattern )
        
        self.filename_list.SortItems( self.sortList )

        self.button_add.Enable( False )

    def OnDel( self, event ):
        if self.selected_item is not None:
            self.filename_list.DeleteItem(self.selected_item )

        self.selected_item = None
        self.button_del.Enable( False )

    def OnPatternTextEnter( self, event ):
        if self.button_add.IsEnabled():
            self.OnAdd( None )

    def OnPatternTextChanged( self, event ):
        new_pattern = self.pattern_text_ctrl.GetValue()
        if len(new_pattern) == 0:
            self.button_add.Enable( False )
            return

        # enable the add button if the text is not in the list already
        for index in range( self.filename_list.GetItemCount() ):
            pattern = self.filename_list.GetItemText( index )
            if pattern == new_pattern:
                self.button_add.Enable( False )
                return

        self.button_add.Enable( True )

    def OnPatternSelected( self, event ):
        self.selected_item = event.m_itemIndex

        # put the selected text into the pattern ctrl
        pattern = self.filename_list.GetItemText( event.m_itemIndex )
        self.pattern_text_ctrl.SetValue( pattern )
        self.pattern_text_ctrl.SetSelection( -1, -1 )

        # Enable the delete button
        self.button_del.Enable( True )

    def OnPatternDeselected( self, event ):
        self.selected_item = None

        # Disable the delete button
        self.button_del.Enable( False )

    def savePreferences( self ):
        p = self.app.prefs.getView()

        filename_list = []

        for index in range( self.filename_list.GetItemCount() ):
            filename_list.append( self.filename_list.GetItemText( index ).encode('UTF-8') )

        p.excluded_filenames_list = filename_list

    def validate( self ):
        return True


class ListColumnsPage(PagePanel):
    id_exclude = wx.NewId()
    id_include = wx.NewId()
    id_move_up = wx.NewId()
    id_move_down = wx.NewId()
    id_excluded_list = wx.NewId()
    id_included_list = wx.NewId()
    id_width = wx.NewId()

    def __init__( self, notebook, app ):
        self.app = app
        self.selected_col_id = None
        self.column_info = wb_subversion_list_handler_common.ViewColumnInfo()
        PagePanel.__init__( self, notebook, T_('Columns') )

    def initControls( self ):
        p = self.app.prefs.getView()
        self.column_info.setFromPreferenceData( p )

        self.excluded_list = wx.ListCtrl( self, ListColumnsPage.id_excluded_list, wx.DefaultPosition,
                wx.Size( 200, 100 ), wx.LC_REPORT )
        self.excluded_list.InsertColumn( 0, T_('Column') )
        self.excluded_list.SetColumnWidth( 0, 100 )
        self.excluded_list.InsertColumn( 1, T_('Width'), wx.LIST_FORMAT_RIGHT )
        self.excluded_list.SetColumnWidth( 1, 80 )

        self.included_list = wx.ListCtrl( self, ListColumnsPage.id_included_list, wx.DefaultPosition,
                wx.Size( 200, 100 ), wx.LC_REPORT )
        self.included_list.InsertColumn( 0, T_('Column') )
        self.included_list.SetColumnWidth( 0, 100 )
        self.included_list.InsertColumn( 1, T_('Width'), wx.LIST_FORMAT_RIGHT )
        self.included_list.SetColumnWidth( 1, 80 )

        for name in self.column_info.getColumnOrder():
            info = self.column_info.getInfoByName( name )
            info.included =  True
            index = self.included_list.GetItemCount()

            self.included_list.InsertStringItem( index, T_( info.label ) )
            self.included_list.SetItemData( index, info.col_id )
            self.included_list.SetStringItem( index, 1, str(info.width) )
    
        for info in self.column_info.excludedInfo():
            index = self.excluded_list.GetItemCount()

            self.excluded_list.InsertStringItem( index, T_( info.label ) )
            self.excluded_list.SetItemData( index, info.col_id )
            self.excluded_list.SetStringItem( index, 1, str(info.width) )


        self.button_include = wx.Button( self, ListColumnsPage.id_include, T_(' Include --> ') )
        self.button_include.Enable( False )
        self.button_exclude = wx.Button( self, ListColumnsPage.id_exclude, T_(' <-- Exclude ') )
        self.button_exclude.Enable( False )

        self.button_up = wx.Button( self, ListColumnsPage.id_move_up, T_(' Move Up ') )
        self.button_up.Enable( False )
        self.button_down = wx.Button( self, ListColumnsPage.id_move_down, T_(' Move Down ') )
        self.button_down.Enable( False )

        self.width_text_ctrl = wx.TextCtrl( self, ListColumnsPage.id_width, '',
                wx.DefaultPosition, wx.Size(200, -1), style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT  )

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.button_include, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_exclude, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.width_text_ctrl, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_up, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_down, 0, wx.EXPAND|wx.EAST, 5 )

        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer.Add( self.excluded_list, 0, wx.EXPAND|wx.WEST, 5 )
        self.h_sizer.Add( self.v_sizer, 0, wx.EXPAND|wx.EAST, 5 )
        self.h_sizer.Add( self.included_list, 0, wx.EXPAND|wx.EAST, 5 )

        wx.EVT_BUTTON( self, ListColumnsPage.id_include, self.OnInclude )
        wx.EVT_BUTTON( self, ListColumnsPage.id_exclude, self.OnExclude )
        wx.EVT_BUTTON( self, ListColumnsPage.id_move_up, self.OnMoveUp )
        wx.EVT_BUTTON( self, ListColumnsPage.id_move_down, self.OnMoveDown )

        wx.EVT_TEXT_ENTER( self, ListColumnsPage.id_width, self.OnWidthTextEnter )

        wx.EVT_LIST_ITEM_SELECTED( self, ListColumnsPage.id_excluded_list, self.OnExcludedListItemSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self, ListColumnsPage.id_excluded_list, self.OnExcludedListItemDeselected )

        wx.EVT_LIST_ITEM_SELECTED( self, ListColumnsPage.id_included_list, self.OnIncludedListItemSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self, ListColumnsPage.id_included_list, self.OnIncludedListItemDeselected )

        return self.h_sizer

    def OnInclude( self, event ):
        self.changeInclusionColumn( True, self.excluded_list, self.included_list )

    def OnExclude( self, event ):
        self.changeInclusionColumn( False, self.included_list, self.excluded_list )

    def changeInclusionColumn( self, include, from_list, to_list ):
        info = self.column_info.getInfoById( self.selected_col_id )

        try:
            width = int(self.width_text_ctrl.GetValue())
        except ValueError:
            wx.MessageBox( T_('Width for %(name)s must be an number between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return

        if( width >= info.min_width
        and width <= info.max_width ):
            info.width = width
        else:
            wx.MessageBox( T_('Width for %(name)s must be between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return

        info.include = include

        # remove from from_list
        from_index = from_list.FindItemData( -1, info.col_id )
        from_list.DeleteItem( from_index )

        # add to end of to_list
        index = to_list.GetItemCount()

        to_list.InsertStringItem( index, T_( info.label ) )
        to_list.SetItemData( index, info.col_id )
        to_list.SetStringItem( index, 1, str(info.width) )

    def OnMoveUp( self, event ):
        self.moveColumn( -1 )

    def OnMoveDown( self, event ):
        self.moveColumn( 1 )

    def moveColumn( self, direction ):
        info = self.column_info.getInfoById( self.selected_col_id )

        index = self.included_list.FindItemData( -1, info.col_id )
        name = self.included_list.GetItemText( index )

        self.included_list.DeleteItem( index )

        index += direction
        self.included_list.InsertStringItem( index, T_( info.label ) )
        self.included_list.SetItemData( index, info.col_id )
        self.included_list.SetStringItem( index, 1, str( info.width ) )
        self.included_list.SetItemState( index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED )

        # enable up and down if not at the ends
        item_count = self.included_list.GetItemCount()
        self.button_up.Enable( item_count > 1 and index != 0 )
        self.button_down.Enable( item_count > 1 and index != (item_count-1) )


    def OnWidthTextEnter( self, event ):
        info = self.column_info.getInfoById( self.selected_col_id )
        try:
            width = int(self.width_text_ctrl.GetValue())
        except ValueError:
            wx.MessageBox( T_('Width for %(name)s must be an number between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return

        if( width >= info.min_width
        and width <= info.max_width ):
            info.width = width
            index = self.included_list.FindItemData( -1, info.col_id )
            self.included_list.SetStringItem( index, 1, str(width) )
        else:
            wx.MessageBox( T_('Width for %(name)s must be between %(min)d and %(max)d') %
                        {'name': T_( info.label ), 'min': info.min_width, 'max': info.max_width},
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
        

    def OnExcludedListItemSelected( self, event ):
        self.selected_col_id = self.excluded_list.GetItemData( event.m_itemIndex )
        info = self.column_info.getInfoById( self.selected_col_id )

        self.button_up.Enable( False )
        self.button_down.Enable( False )
        self.button_include.Enable( True )
        self.button_exclude.Enable( False )

        self.width_text_ctrl.SetValue( str(info.width) )
        self.width_text_ctrl.Enable( True )

    def OnExcludedListItemDeselected( self, event ):
        self.button_include.Enable( False )
        self.width_text_ctrl.Enable( False )
        self.button_up.Enable( False )
        self.button_down.Enable( False )

    def OnIncludedListItemSelected( self, event ):
        self.selected_col_id = self.included_list.GetItemData( event.m_itemIndex )
        info = self.column_info.getInfoById( self.selected_col_id )

        self.button_exclude.Enable( info.name != 'Name' )
        self.button_include.Enable( False )

        # enable up and down if not at the ends
        item_count = self.included_list.GetItemCount()
        self.button_up.Enable( item_count > 1 and event.m_itemIndex != 0 )
        self.button_down.Enable( item_count > 1 and event.m_itemIndex != (item_count-1) )

        self.width_text_ctrl.SetValue( str(info.width) )
        self.width_text_ctrl.Enable( True )

    def OnIncludedListItemDeselected( self, event ):
        self.button_exclude.Enable( False )
        self.width_text_ctrl.Enable( False )
        self.button_up.Enable( False )
        self.button_down.Enable( False )

    def savePreferences( self ):
        p = self.app.prefs.getView()
        column_order = []
        for index in range( self.included_list.GetItemCount() ):
            col_id = self.included_list.GetItemData( index )
            column_order.append( self.column_info.getNameById( col_id ) )

        self.column_info.setColumnOrder( column_order )
        p.column_order = self.column_info.getColumnOrder()
        p.column_widths = self.column_info.getColumnWidths()

    def validate( self ):
        info = self.column_info.getInfoByName( 'Name' )
        if self.included_list.FindItemData( -1, info.col_id ) < 0:
            wx.MessageBox( T_('You must include the %s column') % (T_( info.label ),),
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return False

        return True

class LogHistoryPage(PagePanel):
    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('Log History') )

    def initControls( self ):
        p = self.app.prefs.getLogHistory()

        self.mode_values = ['show_all', 'show_limit', 'show_since' ]
        self.mode_choice_values = [T_('Show all entries'), T_('Show only'), T_('Show since')]
        self.mode_label = wx.StaticText( self, -1, T_('Default mode: '), style=wx.ALIGN_RIGHT)
        self.mode_ctrl = wx.Choice( self, -1, choices = self.mode_choice_values )
        self.mode_ctrl.SetSelection( self.mode_values.index( p.default_mode ) )

        self.limit_label = wx.StaticText( self, -1, T_('Default limit: '), style=wx.ALIGN_RIGHT)
        self.limit_ctrl = wx.TextCtrl( self, -1, str( p.default_limit ), wx.DefaultPosition, wx.Size(415, -1) )

        self.since_label = wx.StaticText( self, -1, T_('Default since interval (days): '), style=wx.ALIGN_RIGHT)
        self.since_ctrl = wx.TextCtrl( self, -1, str( p.default_since_days_interval ), wx.DefaultPosition, wx.Size(415, -1) )

        self.tags_label = wx.StaticText( self, -1, T_('Default Include tags: '), style=wx.ALIGN_RIGHT)
        self.tags_ctrl = wx.CheckBox( self, -1, T_('Include tags in log history') )
        self.tags_ctrl.SetValue( p.default_include_tags )

        self.grid_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.grid_sizer.AddGrowableCol( 1 )

        self.grid_sizer.Add( self.mode_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.mode_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.grid_sizer.Add( self.limit_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.limit_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.grid_sizer.Add( self.since_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.since_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.grid_sizer.Add( self.tags_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.tags_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.grid_sizer.Add( (1, 1), 0, wx.EXPAND )

        return self.grid_sizer

    def savePreferences( self ):
        p = self.app.prefs.getLogHistory()

        p.default_mode = self.mode_values[ self.mode_ctrl.GetSelection() ]
        p.default_limit = int( self.limit_ctrl.GetValue() )
        p.default_since_days_interval = int( self.since_ctrl.GetValue() )
        p.default_include_tags = self.tags_ctrl.GetValue()

    def validate( self ):
        try:
            limit = int( self.limit_ctrl.GetValue() )
            if limit < 1:
                raise ValueError( 'out of range' )
        except ValueError:
            wx.MessageBox(
                T_('Limit must be greater then 0'),
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return False

        try:
            since_days = int( self.since_ctrl.GetValue() )
            if since_days < 1:
                raise ValueError( 'out of range' )
        except ValueError:
            wx.MessageBox(
                T_('Since days must be greater then 0'),
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return False

        return True

class ToolbarPage(PagePanel):
    id_exclude = wx.NewId()
    id_include = wx.NewId()
    id_move_up = wx.NewId()
    id_move_down = wx.NewId()
    id_excluded_list = wx.NewId()
    id_included_list = wx.NewId()

    def __init__( self, notebook, app ):
        self.app = app
        self.selected_name = None
        PagePanel.__init__( self, notebook, T_('Toolbar') )

    def initControls( self ):
        p = self.app.prefs.getToolbar()
        self.all_groups = wb_toolbars.toolbar_main.getAllGroupNames()
        self.group_order = p.group_order

        self.excluded_list = wx.ListCtrl( self, ToolbarPage.id_excluded_list, wx.DefaultPosition,
                wx.Size( 200, 100 ), wx.LC_REPORT )
        self.excluded_list.InsertColumn( 0, T_('Toolbar Group') )
        self.excluded_list.SetColumnWidth( 0, 100 )

        self.included_list = wx.ListCtrl( self, ToolbarPage.id_included_list, wx.DefaultPosition,
                wx.Size( 200, 100 ), wx.LC_REPORT )
        self.included_list.InsertColumn( 0, T_('Toolbar Group') )
        self.included_list.SetColumnWidth( 0, 100 )

        for name in self.group_order:
            index = self.included_list.GetItemCount()

            self.included_list.InsertStringItem( index, name )
    
        for name in [name for name in self.all_groups if name not in self.group_order]:
            index = self.excluded_list.GetItemCount()

            self.excluded_list.InsertStringItem( index, name )

        self.button_include = wx.Button( self, ToolbarPage.id_include, T_(' Include --> ') )
        self.button_include.Enable( False )
        self.button_exclude = wx.Button( self, ToolbarPage.id_exclude, T_(' <-- Exclude ') )
        self.button_exclude.Enable( False )

        self.button_up = wx.Button( self, ToolbarPage.id_move_up, T_(' Move Up ') )
        self.button_up.Enable( False )
        self.button_down = wx.Button( self, ToolbarPage.id_move_down, T_(' Move Down ') )
        self.button_down.Enable( False )

        # qqq
        self.enable_label = wx.StaticText( self, -1, T_('Display toolbar: '), style=wx.ALIGN_RIGHT )
        self.enable_ctrl = wx.CheckBox( self, -1, T_('Enabled') )
        self.enable_ctrl.SetValue( p.toolbar_enable )
        self.horizontal_label = wx.StaticText( self, -1, T_('Orientation: '), style=wx.ALIGN_RIGHT )
        self.horizontal_ctrl = wx.Choice( self, -1, choices=[T_('Horizontal'), T_('Vertical')] )
        if p.horizontal_orientation:
            self.horizontal_ctrl.SetSelection( 0 )
        else:
            self.horizontal_ctrl.SetSelection( 1 )

        sizes = [T_('Small'), T_('Large'), T_('Huge')]
        pixtoidx = {64: 2, 32: 1, 16: 0}
        self.size_label = wx.StaticText( self, -1, T_('Icon size: '), style=wx.ALIGN_RIGHT )
        self.ctrl_image_size = wx.Choice( self, -1, choices=sizes )
        self.ctrl_image_size.SetSelection( pixtoidx.get( p.bitmap_size, 1 ) )

        # build the sizers
        self.v_sizer = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer.Add( self.button_include, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_exclude, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_up, 0, wx.EXPAND|wx.EAST, 5 )
        self.v_sizer.Add( self.button_down, 0, wx.EXPAND|wx.EAST, 5 )

        self.h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.h_sizer.Add( self.excluded_list, 0, wx.EXPAND|wx.WEST, 5 )
        self.h_sizer.Add( self.v_sizer, 0, wx.EXPAND|wx.EAST, 5 )
        self.h_sizer.Add( self.included_list, 0, wx.EXPAND|wx.EAST, 5 )

        self.grid_sizer = wx.FlexGridSizer( 0, 2, 0, 0 )
        self.grid_sizer.AddGrowableCol( 1 )

        self.grid_sizer.Add( self.enable_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.enable_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.grid_sizer.Add( self.horizontal_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.horizontal_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        self.grid_sizer.Add( self.size_label, 1, wx.EXPAND|wx.ALL, 3 )
        self.grid_sizer.Add( self.ctrl_image_size, 0, wx.EXPAND|wx.ALL, 5 )

        self.v_sizer2 = wx.BoxSizer( wx.VERTICAL )
        self.v_sizer2.Add( self.grid_sizer )
        self.v_sizer2.Add( self.h_sizer )

        wx.EVT_BUTTON( self, ToolbarPage.id_include, self.OnInclude )
        wx.EVT_BUTTON( self, ToolbarPage.id_exclude, self.OnExclude )
        wx.EVT_BUTTON( self, ToolbarPage.id_move_up, self.OnMoveUp )
        wx.EVT_BUTTON( self, ToolbarPage.id_move_down, self.OnMoveDown )

        wx.EVT_LIST_ITEM_SELECTED( self, ToolbarPage.id_excluded_list, self.OnExcludeSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self, ToolbarPage.id_excluded_list, self.OnExcludeDeselected )

        wx.EVT_LIST_ITEM_SELECTED( self, ToolbarPage.id_included_list, self.OnIncludeSelected )
        wx.EVT_LIST_ITEM_DESELECTED( self, ToolbarPage.id_included_list, self.OnIncludeDeselected )

        return self.v_sizer2

    def OnInclude( self, event ):
        self.changeInclusionGroup( self.excluded_list, self.included_list )

    def OnExclude( self, event ):
        self.changeInclusionGroup( self.included_list, self.excluded_list )

    def changeInclusionGroup( self, from_list, to_list ):
        # remove from from_list
        from_index = from_list.FindItem( -1, self.selected_name )
        
        from_list.DeleteItem( from_index )

        # add to end of to_list
        index = to_list.GetItemCount()

        to_list.InsertStringItem( index, self.selected_name )

    def OnMoveUp( self, event ):
        self.moveColumn( -1 )

    def OnMoveDown( self, event ):
        self.moveColumn( 1 )

    def moveColumn( self, direction ):
        index = self.included_list.FindItem( -1, self.selected_name )

        self.included_list.DeleteItem( index )
        index += direction
        self.included_list.InsertStringItem( index, self.selected_name )
        self.included_list.SetItemState( index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED )

        # enable up and down if not at the ends
        item_count = self.included_list.GetItemCount()
        self.button_up.Enable( item_count > 1 and index != 0 )
        self.button_down.Enable( item_count > 1 and index != (item_count-1) )

    def OnExcludeSelected( self, event ):
        self.button_up.Enable( False )
        self.button_down.Enable( False )
        self.button_include.Enable( True )

        self.selected_name = self.excluded_list.GetItemText( event.m_itemIndex )

    def OnExcludeDeselected( self, event ):
        self.button_include.Enable( False )
        self.width_text_ctrl.Enable( False )

    def OnIncludeSelected( self, event ):
        self.button_exclude.Enable( True )
        self.button_include.Enable( False )

        self.selected_name = self.included_list.GetItemText( event.m_itemIndex )

        # enable up and down if no at the ends
        item_count = self.included_list.GetItemCount()
        self.button_up.Enable( item_count > 1 and event.m_itemIndex != 0 )
        self.button_down.Enable( item_count > 1 and event.m_itemIndex != (item_count-1) )

    def OnIncludeDeselected( self, event ):
        self.button_exclude.Enable( False )

    def savePreferences( self ):
        p = self.app.prefs.getToolbar()

        p.toolbar_enable = self.enable_ctrl.GetValue()

        p = self.app.prefs.getToolbar()
        group_order = []
        for index in range( self.included_list.GetItemCount() ):
            name = self.included_list.GetItemText( index )
            group_order.append( name )

        p.group_order = group_order

        p.horizontal_orientation = self.horizontal_ctrl.GetSelection() == 0

        size_to_pixels = {0:16, 1:32, 2:64}
        p.bitmap_size = size_to_pixels[ self.ctrl_image_size.GetSelection() ]

    def validate( self ):
        if self.included_list.GetItemCount() == 0:
            wx.MessageBox( T_('You must include at least one Toolbar group'),
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return False

        return True

class AdvancedPage(PagePanel):
    def __init__( self, notebook, app ):
        self.app = app
        PagePanel.__init__( self, notebook, T_('Advanced') )

    def initControls( self ):
        p = self.app.prefs.getAdvanced()

        self.v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.tagbranch_ctrl = wx.CheckBox( self, -1, T_("Allow arbitrary paths for tag/branch") )
        self.tagbranch_ctrl.SetValue( p.arbitrary_tag_branch )

        self.v_sizer.Add( self.tagbranch_ctrl, 0, wx.EXPAND|wx.ALL, 5 )

        return self.v_sizer

    def savePreferences( self ):
        p = self.app.prefs.getAdvanced()
        p.arbitrary_tag_branch = self.tagbranch_ctrl.GetValue()

    def validate( self ):
        return True
