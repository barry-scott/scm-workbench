'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_frame.py

'''
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_scintilla

import wb_diff_images
import wb_diff_difflib
import wb_diff_processor

import wb_main_window
import wb_config
import wb_diff_images

class DiffSideBySideView(wb_main_window.WbMainWindow):
    def __init__( self, app, parent, file_left, title_left, file_right, title_right, ):
        super().__init__( app, wb_diff_images, app._debugDiff, parent=parent )

        prefs = self.app.prefs.diff_window
        geometry = prefs.geometry

        self.setWindowTitle( T_('Diff %(title1)s and %(title2)s') %
                                {'title1': title_left
                                ,'title2': title_right} )

        self.setWindowIcon( wb_diff_images.getQIcon( 'wb.png' ) )
        if geometry is not None:
            geometry = QtCore.QByteArray( geometry.encode('utf-8') )
            self.restoreGeometry( QtCore.QByteArray.fromHex( geometry ) )

        else:
            self.resize( 800, 600 )

        self.setupToolBar()

        if False:
            # Add the status bar
            self.status_bar_size_changed = False

            s = self.createStatusBar()

            s.SetFieldsCount( 3 )
            s.SetStatusWidths( [-1,  -1, 480] )

            s.SetStatusText( 'Ready', 0 )
            s.SetStatusText( 'Steady', 1 )
            s.SetStatusText( 'Go!', 2 )

            self.total_change_number = 0
            self.current_change_number = 0
            self.setChangeCounts( 0, 0 )

            self.status_bar_key_field = DiffBodyText( s, line_numbers=False )
            self.status_bar_key_field.insertStyledText( T_('Key: '), self.status_bar_key_field.style_line_normal )
            self.status_bar_key_field.insertStyledText( T_('Inserted text '), self.status_bar_key_field.style_line_insert )
            self.status_bar_key_field.insertStyledText( T_('Deleted text '), self.status_bar_key_field.style_line_delete )
            self.status_bar_key_field.insertStyledText( T_('Changed text'), self.status_bar_key_field.style_line_changed )
            self.status_bar_key_field.setReadOnly( True )

            wx.EVT_SIZE( s, self.onStatusBarSize )
            wx.EVT_IDLE( s, self.onStatusBarIdle )

        self.splitter = QtWidgets.QSplitter()
        self.splitter.setOrientation( QtCore.Qt.Horizontal )
        self.sash_ratio = 0.5

        self.panel_left = DiffWidget( self.splitter, title_left )
        self.panel_right = DiffWidget( self.splitter, title_right )

        self.panel_left.ed.setMirrorEditor( self.panel_right.ed )
        self.panel_right.ed.setMirrorEditor( self.panel_left.ed )

        self.splitter.addWidget( self.panel_left )
        self.splitter.addWidget( self.panel_right )

        #self.splitter.SetMinimumPaneSize( 150 )
        #self.splitter.SetSashPosition( 150 )

        # Create the editor and calculate all the differences
        self.processor = wb_diff_processor.DiffProcessor( self.panel_left.ed, self.panel_right.ed )
        self.diff = wb_diff_difflib.Difference( self.processor )

        self.files_ok = self.diff.filecompare( file_left, file_right )
        if not self.files_ok:
            return

        self.setChangeCounts( 0, self.processor.getChangeCount() )
        #self.setZoom( diff_prefs.zoom )

        if False:
            # Set up the keyboard shortcuts
            accelerator_table = wx.AcceleratorTable(
                [(wx.ACCEL_NORMAL, ord('p'), id_previous_command )
                ,(wx.ACCEL_SHIFT,  wx.WXK_F7, id_previous_command )
                ,(wx.ACCEL_NORMAL, ord('n'), id_next_command )
                ,(wx.ACCEL_NORMAL, wx.WXK_F7, id_next_command )
                ,(wx.ACCEL_NORMAL, ord(' '), id_whitespace_command )
                ,(wx.ACCEL_NORMAL, ord('e'), id_expand_folds_command )
                ,(wx.ACCEL_NORMAL, ord('c'), id_collapse_folds_command )
                ])
            self.setAcceleratorTable( accelerator_table )

        #qqq#wx.EVT_SPLITTER_SASH_POS_CHANGED( self.splitter, -1, self.onSashPositionChanged )

        # qqq # maybe zoomIn and zoomOut events?
        #self.panel_left.zoomChanged.connect( self.handleZoomChanged )
        #self.panel_right.zoomChanged.connect( self.handleZoomChanged )

        self.setCentralWidget( self.splitter )

        # show first diff
        self.actionDiffNext()

    def setupToolBar( self ):
        t = self.tool_bar_diff = self._addToolBar( T_('f') )
        self._addTool( t, T_('Expand folds'), self.actionFoldsExpand, self.enablerFoldsExpand )
        self._addTool( t, T_('Collapse folds'), self.actionFfoldsCollapse, self.enablerFoldsCollapsed )
        t.addSeparator()
        self._addTool( t, T_('Toggle White Space'), self.actionToggleWhiteSpace, self.enablerAlways )
        t.addSeparator()
        self._addTool( t, T_('Previous difference'), self.actionDiffPrev, self.enablerDiffPrev )
        self._addTool( t, T_('Next difference'), self.actionDiffNext, self.enablerDiffNext )

    def enablerAlways( self ):
        return True

    def enablerFoldsExpand( self ):
        return true

    def enablerFoldsCollapsed( self ):
        return true

    def enablerDiffPrev( self ):
        return true

    def enablerDiffNext( self ):
        return true

    #------------------------------------------------------------
    def OnStatusBarSize( self, event ):
        self._repositionStatusBar()

        # tell idle to fix up status bar
        self.status_bar_size_changed = True

    def OnStatusBarIdle( self, event ):
        if self.status_bar_size_changed:
            self._repositionStatusBar()
            self.status_bar_size_changed = False

    def setChangeCounts( self, current_change_number=None, total_change_number=None ):
        if current_change_number is not None:
            self.current_change_number = current_change_number
        if total_change_number is not None:
            self.total_change_number = total_change_number

        #self.getStatusBar().SetStatusText( T_('Diff %(change1)d of %(change2)d') %
        #                        {'change1': self.current_change_number
        #                        ,'change2': self.total_change_number}, 1 )

    #------------------------------------------------------------
    def closeEvent( self, event ):
        #qqq# save geometry

        super().closeEvent( event )

    def OnSashPositionChanged( self, event ):
        w, h = self.splitter.GetClientSizeTuple()
        self.sash_ratio = float( event.GetSashPosition() ) / float( w )
        event.Skip()

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

    def actionFfoldsCollapse( self ):
        self.showAllFolds( False )

    def showAllFolds( self, show ):
        self.panel_left.ed.showAllFolds( show )
        self.panel_right.ed.showAllFolds( show )

    def handleZoomChanged( self ):
        zoom = evt.GetEventObject().GetZoom()
        self.setZoom( zoom )
        
    def SetZoom( self, zoom ):
        if zoom != self.panel_left.ed.GetZoom():
            self.panel_left.ed.SetZoom( zoom )

        if zoom != self.panel_right.ed.GetZoom():
            self.panel_right.ed.SetZoom( zoom )

        self.panel_left.ed.diff_line_numbers.SetZoom( zoom )
        self.panel_right.ed.diff_line_numbers.SetZoom( zoom )
            
#----------------------------------------------------------------------
class DiffWidget(QtWidgets.QWidget):
    def __init__( self, parent_win, title ):
        super().__init__( parent_win )

        self.text_file_name = QtWidgets.QLineEdit()
        self.text_file_name.setText( title )
        self.text_file_name.setReadOnly( True )

        self.ed = DiffBodyText( self )

        v_layout = QtWidgets.QBoxLayout( QtWidgets.QBoxLayout.LeftToRight )
        v_layout.addWidget( self.ed.diff_line_numbers )
        v_layout.addWidget( self.ed )

        h_layout = QtWidgets.QBoxLayout( QtWidgets.QBoxLayout.TopToBottom )
        h_layout.addWidget( self.text_file_name )
        h_layout.addLayout( v_layout )

        self.setLayout( h_layout )

class DiffBodyText(wb_scintilla.WbScintilla):
    syncScroll = QtCore.pyqtSignal()

    def __init__( self, parent, line_numbers=True ):
        self.text_body_other = None

        super().__init__( parent )

        self.white_space_visible = False

        if line_numbers:
            self.diff_line_numbers = DiffLineNumbers( parent )
        else:
            self.diff_line_numbers = None

        self.fold_margin = -1
        self.fold_start = -1
        self.fold_context_border = 1
        self.fold_minimum_length = self.fold_context_border * 2 + 1

        self.style_line_normal = self.STYLE_DEFAULT
        self.style_line_insert = self.STYLE_LASTPREDEFINED
        self.style_line_delete = self.STYLE_LASTPREDEFINED + 1
        self.style_line_changed = self.STYLE_LASTPREDEFINED + 2

        self.style_replace_insert =  self.style_line_insert | self.INDIC1_MASK
        self.style_replace_delete =  self.style_line_delete | self.INDIC1_MASK
        self.style_replace_changed = self.style_line_changed | self.INDIC1_MASK
        self.style_replace_equal =   self.style_line_normal | self.INDIC1_MASK

        self.emptyUndoBuffer()

        self.setMarginWidth( 0, 0 )
        self.setMarginWidth( 1, 0 )
        self.setMarginWidth( 2, 0 )

        self.setScrollWidth( 10000 )

        # make some styles
        self.styleSetFromSpec( self.style_line_normal,
                'size:%d,face:%s,fore:#000000' % (wb_config.point_size, wb_config.face) )
        self.styleSetFromSpec( self.style_line_insert, 'fore:#008200' )
        self.styleSetFromSpec( self.style_line_delete, 'fore:#0000FF' )
        self.styleSetFromSpec( self.style_line_changed, 'fore:#FF0000' )

        # and finally, an indicator or two
        self.indicSetStyle( self.style_line_insert, self.INDIC_SQUIGGLE )
        self.indicSetFore( self.style_line_insert, '#ffb0b0' )
        self.indicSetStyle( self.style_line_delete, self.INDIC_SQUIGGLE)
        self.indicSetFore( self.style_line_delete, '#ff0000' )
        self.indicSetStyle( self.style_line_changed, self.INDIC_STRIKE )
        self.indicSetFore( self.style_line_changed, '#000000' )

        self.marginClicked.connect( self.handleMarginClicked )

        if line_numbers:
            self.setupFolding( 1 )

        #wx.EVT_SCROLLWIN( self, self.onNeedToSyncScroll )
        self.syncScroll.connect( self.onSyncScroll )
        DiffBodyText.body_count += 1
        self.body_count = DiffBodyText.body_count

    body_count = 0
    def __repr__( self ):
        return '<DiffBodyText: %d>' % (self.body_count,)

    def wheelEvent( self, event ):
        assert( self.text_body_other )
        self.syncScroll.emit()

    def onNeedToSyncScroll( self, event ):
        if self.text_body_other is not None:
            self.syncScroll.emit()

        event.Skip()

    def onSyncScroll( self ):
        line_number = self.getFirstVisibleLine()
        self.diff_line_numbers.setFirstVisibleLine( line_number )
        self.text_body_other.setFirstVisibleLine( line_number )
        self.text_body_other.diff_line_numbers.setFirstVisibleLine( line_number )

    def setMirrorEditor( self, text_body_other ):
        self.text_body_other = text_body_other

    def toggleViewWhiteSpace( self ):
        self.white_space_visible = not self.white_space_visible
        self.setViewWhiteSpace( self.white_space_visible )

    #--------------------------------------------------------------------------------
    def handleMarginClicked( self, event ):
        if event.GetMargin() == self.fold_margin:
            self.toggleFoldAtLine( self.lineFromPosition( event.GetPosition() ) )

    #--------------------------------------------------------------------------------
    def setupFolding( self, margin ):
        self.fold_margin = margin
        self.setProperty( 'fold', '1' )
        self.diff_line_numbers.setProperty( 'fold', '1' )
        self.setMarginType( self.fold_margin, self.SC_MARGIN_SYMBOL )

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
    def __init__( self, parent ):

        super().__init__( parent )

        self.style_normal = self.STYLE_DEFAULT
        self.style_line_numbers = self.STYLE_LASTPREDEFINED + 1
        self.style_line_numbers_for_diff = self.STYLE_LASTPREDEFINED

        self.emptyUndoBuffer()

        self.setMarginWidth( 0, 0 )
        self.setMarginWidth( 1, 0 )
        self.setMarginWidth( 2, 0 )


        # make some styles
        self.styleSetFromSpec( self.style_normal,
                'size:%d,face:%s,fore:#000000,back:#e0e0e0' % (wb_config.point_size, wb_config.face) )
        self.styleSetFromSpec( self.style_line_numbers,
                'size:%d,face:%s,fore:#000000,back:#f0f0f0' % (wb_config.point_size, wb_config.face) )
        self.styleSetFromSpec( self.style_line_numbers_for_diff,
                'size:%d,face:%s,fore:#000000,back:#d0d0d0' % (wb_config.point_size, wb_config.face) )

        # Calculate space for 6 digits
        font = QtGui.QFont( wb_config.face, wb_config.point_size )
        self.setFont( font )

        fontmetrics = QtGui.QFontMetrics( font )

        width = fontmetrics.width( '123456' )

        self.setScrollWidth( width )
        self.setMaximumWidth( width )
        self.setMinimumWidth( width )

        # no scroll bars on the line number control
        self.setVScrollBar( False )
        self.setHScrollBar( False )
