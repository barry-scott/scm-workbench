'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_frame.py

'''
from PyQt6 import QtWidgets
from PyQt6 import QtGui
from PyQt6 import QtCore

import wb_scintilla

import wb_diff_difflib
import wb_diff_processor

import wb_main_window
import wb_config
import wb_tracked_qwidget

class DiffSideBySideView(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    def __init__( self, app, parent, title, file_left, header_left, file_right, header_right, ):
        super().__init__( app, app.debug_options.debugLogDiff, parent=parent )

        geometry = self.app.prefs.diff_window.geometry

        self.setWindowTitle( title )
        icon = app.getAppQIcon()
        if icon is not None:
            self.setWindowIcon( icon )

        if geometry is not None:
            geometry = QtCore.QByteArray( geometry.encode('utf-8') )
            self.restoreGeometry( QtCore.QByteArray.fromHex( geometry ) )

        else:
            em, ex = self.app.defaultFontEmEx( 'm' )
            self.resize( 130*em, 45*ex )

        self.setupToolBar()
        self.setupStatusBar( self.statusBar() )

        self.splitter = QtWidgets.QSplitter()
        self.splitter.setOrientation( QtCore.Qt.Orientation.Horizontal )
        self.sash_ratio = 0.5

        self.panel_left = DiffWidget( app, self.splitter, header_left, name='left' )
        self.panel_right = DiffWidget( app, self.splitter, header_right, name='right' )

        self.panel_left.ed.setMirrorEditor( self.panel_right.ed )
        self.panel_right.ed.setMirrorEditor( self.panel_left.ed )

        self.panel_left.ed.setProcessKeyHandler( self.processKeyHandler )
        self.panel_right.ed.setProcessKeyHandler( self.processKeyHandler )

        self.splitter.addWidget( self.panel_left )
        self.splitter.addWidget( self.panel_right )

        # Create the editor and calculate all the differences
        self.processor = wb_diff_processor.DiffProcessor( self.panel_left.ed, self.panel_right.ed )
        self.diff = wb_diff_difflib.Difference( self.processor )

        self.files_ok = self.diff.filecompare( file_left, file_right )
        if not self.files_ok:
            return

        self.setChangeCounts( 0, self.processor.getChangeCount() )

        self.setCentralWidget( self.splitter )

        # start with folds collapsed
        self.actionFoldsCollapse()
        # show first diff
        self.actionDiffNext()

    def processKeyHandler( self, key ):
        if key in ('n', 'N'):
            self.actionDiffNext()
            return True

        elif key in ('p', 'P'):
            self.actionDiffPrev()
            return True

        elif key == '.':
            self.actionToggleWhiteSpace()
            return True

        elif key == '+':
            self.actionFoldsExpand()
            return True

        elif key == '-':
            self.actionFoldsCollapse()
            return True

        else:
            return False

    def setupToolBar( self ):
        t = self.tool_bar_diff = self._addToolBar( T_('f') )
        self._addTool( t, T_('Expand folds'), self.actionFoldsExpand, self.enablerFoldsExpand )
        self._addTool( t, T_('Collapse folds'), self.actionFoldsCollapse, self.enablerFoldsCollapsed )
        t.addSeparator()
        self._addTool( t, T_('Toggle White Space'), self.actionToggleWhiteSpace, self.enablerAlways )
        t.addSeparator()
        self._addTool( t, T_('Previous difference'), self.actionDiffPrev, self.enablerDiffPrev )
        self._addTool( t, T_('Next difference'), self.actionDiffNext, self.enablerDiffNext )

    def setupStatusBar( self, s ):
        self.status_message = QtWidgets.QLabel()
        s.addWidget( self.status_message )

        prefs = self.app.prefs.diff_window

        key = QtWidgets.QLabel()
        key.setTextFormat( QtCore.Qt.TextFormat.RichText )
        if self.app.isDarkMode():
            all_colours = {'normal': self.app.defaultFgRgb()
                          ,'insert': wb_config.diff_dark_colour_insert_line
                          ,'delete': wb_config.diff_dark_colour_delete_line
                          ,'change': wb_config.diff_dark_colour_change_line}

        else:
            all_colours = {'normal': self.app.defaultFgRgb()
                          ,'insert': wb_config.diff_light_colour_insert_line
                          ,'delete': wb_config.diff_light_colour_delete_line
                          ,'change': wb_config.diff_light_colour_change_line}


        key.setText( '<font color="%(normal)s">Key: </font>'
                     '<font color="%(insert)s">Inserted text </font>'
                     '<font color="%(delete)s">Deleted text </font>'
                     '<font color="%(change)s">Changed text </font>' % all_colours )
        key.setFrameStyle( QtWidgets.QFrame.Shape.Panel|QtWidgets.QFrame.Shadow.Sunken )

        self.status_bar_key_field = key
        s.addPermanentWidget( self.status_bar_key_field )

    #------------------------------------------------------------
    def enablerAlways( self ):
        return True

    def enablerFoldsExpand( self ):
        return True

    def enablerFoldsCollapsed( self ):
        return True

    def enablerDiffPrev( self ):
        return True

    def enablerDiffNext( self ):
        return True

    #------------------------------------------------------------
    def setChangeCounts( self, current_change_number=None, total_change_number=None ):
        if current_change_number is not None:
            self.current_change_number = current_change_number

        if total_change_number is not None:
            self.total_change_number = total_change_number

        self.status_message.setText(
            T_('Diff %(change1)d of %(change2)d') %
                {'change1': self.current_change_number
                ,'change2': self.total_change_number} )

    #------------------------------------------------------------
    def closeEvent( self, event ):
        #qqq# save geometry
        super().closeEvent( event )

    def actionDiffNext( self ):
        if self.total_change_number == 0:
            return

        self.processor.moveNextChange()
        self.setChangeCounts( self.processor.getCurrentChange() )

    def actionDiffPrev( self ):
        if self.total_change_number == 0:
            return

        self.processor.movePrevChange()
        self.setChangeCounts( self.processor.getCurrentChange() )

    def actionToggleWhiteSpace( self ):
        self.panel_left.ed.toggleViewWhiteSpace()
        self.panel_right.ed.toggleViewWhiteSpace()

    def actionFoldsExpand( self ):
        self.showAllFolds( True )
        self.processor.showCurrentChange()

    def actionFoldsCollapse( self ):
        self.showAllFolds( False )
        self.processor.showCurrentChange()

    def showAllFolds( self, show ):
        self.panel_left.ed.showAllFolds( show )
        self.panel_right.ed.showAllFolds( show )

#----------------------------------------------------------------------
class DiffWidget(QtWidgets.QWidget):
    def __init__( self, app, parent_win, title, name=None ):
        super().__init__( parent_win )

        self.name = name    # used for debug

        self.text_file_name = QtWidgets.QLineEdit()
        self.text_file_name.setText( title )
        self.text_file_name.setReadOnly( True )

        self.ed = DiffBodyText( app, self, name=self.name )

        v_layout = QtWidgets.QBoxLayout( QtWidgets.QBoxLayout.Direction.LeftToRight )
        v_layout.addWidget( self.ed.diff_line_numbers )
        v_layout.addWidget( self.ed )

        h_layout = QtWidgets.QBoxLayout( QtWidgets.QBoxLayout.Direction.TopToBottom )
        h_layout.addWidget( self.text_file_name )
        h_layout.addLayout( v_layout )

        self.setLayout( h_layout )

class DiffBodyText(wb_scintilla.WbScintilla):
    syncScroll = QtCore.pyqtSignal()

    def __init__( self, app, parent, name=None ):
        self.debugLog = app.debug_options.debugLogDiff
        self.name = name    # used for debug
        self.text_body_other = None

        self.process_key_handler = None

        super().__init__( parent )

        self.white_space_visible = False

        self.diff_line_numbers = DiffLineNumbers( app, parent, name='%s-numbers' % (self.name,) )

        self.fold_margin = -1
        self.fold_start = -1
        self.fold_context_border = 1
        self.fold_minimum_length = self.fold_context_border * 2 + 1

        self.style_line_normal = self.STYLE_DEFAULT
        self.style_line_insert = self.STYLE_LASTPREDEFINED + 1
        self.style_line_delete = self.STYLE_LASTPREDEFINED + 2
        self.style_line_change = self.STYLE_LASTPREDEFINED + 3

        # use the lexer range of indictor numbers
        self.indictor_char_insert =  8
        self.indictor_char_delete =  9
        self.indictor_char_changed = 10

        self.emptyUndoBuffer()

        self.setMarginWidth( 0, 0 )
        self.setMarginWidth( 1, 0 )
        self.setMarginWidth( 2, 0 )

        self.setScrollWidth( 10000 )

        # make some styles
        prefs = app.prefs.diff_window

        # Setting the font via the help setFont() aways works where as the low level API does not.
        self.setFont( app.codeFont() )

        if app.isDarkMode():
            self.styleSetFromSpec( self.style_line_normal,
                    'fore:%s,back:%s' % (app.defaultFgRgb(), app.defaultBgRgb()) )
            self.styleSetFromSpec( self.style_line_insert,
                    'fore:%s,back:%s' % (wb_config.diff_dark_colour_insert_line, app.defaultBgRgb()) )
            self.styleSetFromSpec( self.style_line_delete,
                    'fore:%s,back:%s' % (wb_config.diff_dark_colour_delete_line, app.defaultBgRgb()) )
            self.styleSetFromSpec( self.style_line_change,
                    'fore:%s,back:%s' % (wb_config.diff_dark_colour_change_line, app.defaultBgRgb()) )

            # and finally, an indicator or two
            self.indicSetStyle( self.indictor_char_insert,  self.INDIC_SQUIGGLE )
            self.indicSetFore( self.indictor_char_insert,   str(wb_config.diff_dark_colour_insert_line) )

            self.indicSetStyle( self.indictor_char_delete,  self.INDIC_STRIKE )
            self.indicSetFore( self.indictor_char_delete,   str(wb_config.diff_dark_colour_delete_line) )

            self.indicSetStyle( self.indictor_char_changed, self.INDIC_SQUIGGLE )
            self.indicSetFore( self.indictor_char_changed,  str(wb_config.diff_dark_colour_change_line) )

        else:
            self.styleSetFromSpec( self.style_line_normal,
                    'fore:%s,back:%s' % (app.defaultFgRgb(), app.defaultBgRgb()) )
            self.styleSetFromSpec( self.style_line_insert,
                    'fore:%s,back:%s' % (wb_config.diff_light_colour_insert_line, app.defaultBgRgb()) )
            self.styleSetFromSpec( self.style_line_delete,
                    'fore:%s,back:%s' % (wb_config.diff_light_colour_delete_line, app.defaultBgRgb()) )
            self.styleSetFromSpec( self.style_line_change,
                    'fore:%s,back:%s' % (wb_config.diff_light_colour_change_line, app.defaultBgRgb()) )

            # and finally, an indicator or two
            self.indicSetStyle( self.indictor_char_insert,  self.INDIC_SQUIGGLE )
            self.indicSetFore( self.indictor_char_insert,   str(wb_config.diff_light_colour_insert_line) )

            self.indicSetStyle( self.indictor_char_delete,  self.INDIC_STRIKE )
            self.indicSetFore( self.indictor_char_delete,   str(wb_config.diff_light_colour_delete_line) )

            self.indicSetStyle( self.indictor_char_changed, self.INDIC_SQUIGGLE )
            self.indicSetFore( self.indictor_char_changed,  str(wb_config.diff_light_colour_change_line) )

        self.marginClicked.connect( self.handleMarginClicked )
        self.cursorPositionChanged.connect( self.handleCursorPositionChanged )

        self.setupFolding( 1 )

        self.syncScroll.connect( self.onSyncScroll )
        DiffBodyText.body_count += 1
        self.body_count = DiffBodyText.body_count

    body_count = 0
    def __repr__( self ):
        return '<DiffBodyText: %d>' % (self.body_count,)

    def wheelEvent( self, event ):
        super().wheelEvent( event )

        assert self.text_body_other
        self.syncScroll.emit()

    def setProcessKeyHandler( self, handler ):
        self.process_key_handler = handler

    def keyPressEvent( self, event ):
        if self.process_key_handler( event.text() ):
            return

        super().keyPressEvent( event )

    def onNeedToSyncScroll( self, event ):
        if self.text_body_other is not None:
            self.syncScroll.emit()

    def onSyncScroll( self ):
        line_number = self.getFirstVisibleLine()
        self.debugLog( 'onSyncScroll (%s) first line is %d' % (self.name, line_number) )

        self.debugLog( 'onSyncScroll (%s) set first line %d' % (self.diff_line_numbers.name, line_number) )
        self.diff_line_numbers.setFirstVisibleLine( line_number )

        self.debugLog( 'onSyncScroll (%s) set first line %d' % (self.text_body_other.name, line_number) )
        self.text_body_other.setFirstVisibleLine( line_number )

        self.debugLog( 'onSyncScroll (%s) set first line %d' % (self.text_body_other.diff_line_numbers.name, line_number) )
        self.text_body_other.diff_line_numbers.setFirstVisibleLine( line_number )

    def setMirrorEditor( self, text_body_other ):
        self.text_body_other = text_body_other

    def toggleViewWhiteSpace( self ):
        self.white_space_visible = not self.white_space_visible
        self.setViewWhiteSpace( self.white_space_visible )

    #--------------------------------------------------------------------------------
    def handleCursorPositionChanged( self, line, index ):
        self.onSyncScroll()

    def handleMarginClicked( self, margin, line, modifiers ):
        print( 'qqq handleMarginClicked margin %r line %r modifiers %r' % (margin, line, int(modifiers)) )
        #if event.getMargin() == self.fold_margin:
        #    self.toggleFoldAtLine( self.lineFromPosition( event.GetPosition() ) )

    #--------------------------------------------------------------------------------
    def setupFolding( self, margin ):
        self.fold_margin = margin

        self.setProperty( 'fold', '1' )
        self.diff_line_numbers.setProperty( 'fold', '1' )

        self.setMarginType( self.fold_margin, self.MarginType.SymbolMargin )
        self.setMarginMask( self.fold_margin, self.SC_MASK_FOLDERS )
        self.setMarginSensitive( self.fold_margin, True )
        self.setMarginWidth( self.fold_margin, 15 )

        self.markerDefine(  self.SC_MARKNUM_FOLDEREND,     self.SC_MARK_BOXPLUSCONNECTED )
        self.markerSetFore( self.SC_MARKNUM_FOLDEREND,     'white' )
        self.markerSetBack( self.SC_MARKNUM_FOLDEREND,     'black' )
        self.markerDefine(  self.SC_MARKNUM_FOLDEROPENMID, self.SC_MARK_BOXMINUSCONNECTED)
        self.markerSetFore( self.SC_MARKNUM_FOLDEROPENMID, 'white' )
        self.markerSetBack( self.SC_MARKNUM_FOLDEROPENMID, 'black' )
        self.markerDefine(  self.SC_MARKNUM_FOLDERMIDTAIL, self.SC_MARK_TCORNER)
        self.markerSetFore( self.SC_MARKNUM_FOLDERMIDTAIL, 'white' )
        self.markerSetBack( self.SC_MARKNUM_FOLDERMIDTAIL, 'black' )
        self.markerDefine(  self.SC_MARKNUM_FOLDERTAIL,    self.SC_MARK_LCORNER)
        self.markerSetFore( self.SC_MARKNUM_FOLDERTAIL,    'white' )
        self.markerSetBack( self.SC_MARKNUM_FOLDERTAIL,    'grey' )
        self.markerDefine(  self.SC_MARKNUM_FOLDERSUB,     self.SC_MARK_VLINE)
        self.markerSetFore( self.SC_MARKNUM_FOLDERSUB,     'white' )
        self.markerSetBack( self.SC_MARKNUM_FOLDERSUB,     'grey' )
        self.markerDefine(  self.SC_MARKNUM_FOLDER,        self.SC_MARK_BOXPLUS)
        self.markerSetFore( self.SC_MARKNUM_FOLDER,        'white' )
        self.markerSetBack( self.SC_MARKNUM_FOLDER,        'black' )
        self.markerDefine(  self.SC_MARKNUM_FOLDEROPEN,    self.SC_MARK_BOXMINUS)
        self.markerSetFore( self.SC_MARKNUM_FOLDEROPEN,    'white' )
        self.markerSetBack( self.SC_MARKNUM_FOLDEROPEN,    'black' )

    def toggleFoldAtLine( self, line ):
        if self.getFoldLevel( line ) & self.SC_FOLDLEVELHEADERFLAG:
            if self.getFoldExpanded( line ):
                self.setFoldExpanded( line, False )
                self.diff_line_numbers.setFoldExpanded( line, False )
                self._ShowFoldLines( line, self.getFoldEnd( line ), False )
            else:
                self.setFoldExpanded( line, True)
                self.diff_line_numbers.setFoldExpanded( line, True )
                self._ShowFoldLines( line, self.getFoldEnd( line ), True )

    def getFoldEnd( self, fold_start_line ):
        current_fold_line = fold_start_line

        fold_level = self.getFoldLevel( current_fold_line ) & self.SC_FOLDLEVELNUMBERMASK

        while (self.getFoldLevel( current_fold_line ) & self.SC_FOLDLEVELNUMBERMASK) >= fold_level:
            current_fold_line = current_fold_line + 1

        return current_fold_line - 1

    def _ShowFoldLines( self, start_line, end_line, show_lines ):
        fold_start = start_line + self.fold_context_border
        fold_end = end_line - self.fold_context_border

        self.showFoldLines( fold_start, fold_end, show_lines )

    def showFoldLines( self, start_line, end_line, show_lines ):
        if show_lines:
            self.showLines( start_line, end_line )
            self.diff_line_numbers.showLines( start_line, end_line )
        else:
            self.hideLines( start_line, end_line )
            self.diff_line_numbers.hideLines( start_line, end_line )

    def setFoldLine( self, line_number, is_fold_line ):
        if is_fold_line:
            if self.fold_start == -1:
                self.fold_start = line_number

            elif line_number - self.fold_start == self.fold_minimum_length:
                self.setFoldLevel( self.fold_start, (self.SC_FOLDLEVELBASE+1) | self.SC_FOLDLEVELHEADERFLAG )
                self.diff_line_numbers.setFoldLevel( self.fold_start, (self.SC_FOLDLEVELBASE+1) | self.SC_FOLDLEVELHEADERFLAG )

            self.setFoldLevel( line_number, self.SC_FOLDLEVELBASE+1 )
            self.diff_line_numbers.setFoldLevel( line_number, self.SC_FOLDLEVELBASE+1 )

        else:
            self.setFoldLevel( line_number, self.SC_FOLDLEVELBASE )
            self.diff_line_numbers.setFoldLevel( line_number, self.SC_FOLDLEVELBASE )

            if self.fold_start != -1:
                self.fold_start = -1

    def showAllFolds(self, show_folds):
        for line in range( self.getLineCount() ):
            if( self.getFoldLevel( line ) & self.SC_FOLDLEVELHEADERFLAG
            and ((self.getFoldExpanded( line ) and not show_folds)
                or (not self.getFoldExpanded( line ) and show_folds)) ):
                self.toggleFoldAtLine( line )

#------------------------------------------------------------------------------------------
class DiffLineNumbers(wb_scintilla.WbScintilla):
    def __init__( self, app, parent, name=None ):
        super().__init__( parent )
        self.name = name

        self.style_normal = self.STYLE_DEFAULT
        self.style_line_numbers = self.STYLE_LASTPREDEFINED + 1
        self.style_line_numbers_for_diff = self.STYLE_LASTPREDEFINED

        self.emptyUndoBuffer()

        self.setMarginWidth( 0, 0 )
        self.setMarginWidth( 1, 0 )
        self.setMarginWidth( 2, 0 )

        # make some styles
        self.setFont( app.codeFont() )
        self.styleSetFromSpec( self.style_normal,
                'fore:%s,back:%s' % (app.defaultFgRgb(), app.defaultBgRgb()) )
        self.styleSetFromSpec( self.style_line_numbers,
                'fore:%s,back:%s' % (app.defaultFgRgb(), app.defaultBgRgb()) )
        self.styleSetFromSpec( self.style_line_numbers_for_diff,
                'fore:%s,back:%s' % (app.defaultFgRgb(), '#0d0d0d') )

        # Calculate space for 6 digits
        metrics = QtGui.QFontMetrics( app.codeFont() )
        width = metrics.horizontalAdvance( '123456' )

        self.setScrollWidth( width )
        self.setMaximumWidth( width )
        self.setMinimumWidth( width )

        # no scroll bars on the line number control
        self.setVScrollBar( False )
        self.setHScrollBar( False )
