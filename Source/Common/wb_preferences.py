'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_preferences.py

'''
import pathlib
import sys

from  xml_preferences import XmlPreferences, Scheme, SchemeNode, PreferencesNode, PreferencesMapNode, ParseError

import wb_config

class RGB:
    def __init__( self, text ):
        if len(text) == 7 and text[0] == '#':
            self.R = int( text[1:3], 16 )
            self.G = int( text[3:5], 16 )
            self.B = int( text[5:7], 16 )

        else:
            raise ValueError( 'expecting #RRGGBB hex colour not %r' % (text,) )

    def __str__( self ):
        return '#%2.2x%2.2x%2.2x' % (self.R, self.G, self.B)

    def __repr__( self ):
        return '<RGB R:%d G:%d B:%d>' % (self.R, self.G, self.B)

class RGBA:
    def __init__( self, text ):
        if len(text) == 9 and text[0] == '#':
            self.R = int( text[1:3], 16 )
            self.G = int( text[3:5], 16 )
            self.B = int( text[5:7], 16 )
            self.A = int( text[7:9], 16 )

        else:
            raise ValueError( 'expecting #RRGGBBAA hex colour not %r' % (text,) )

    def __str__( self ):
        return '#%2.2x%2.2x%2.2x%2.2x'(self.R, self.G, self.B, self.A)

    def __repr__( self ):
        return '<RGBA R:%d G:%d B:%d, A:%d>' % (self.R, self.G, self.B, self.A)

# cannot use a class for bool as PyQt wll not use __bool__ to get its truth
def Bool( text ):
    if text.lower() == 'true':
        return True

    elif text.lower() == 'false':
        return False

    else:
        raise ValueError( 'Bool expects the string true or false' )

class Preferences(PreferencesNode):
    xml_attribute_info = tuple()

    def __init__( self ):
        super().__init__()

        self.main_window = None
        self.diff_window = None
        self.last_position_bookmark = None
        self.all_bookmarks = None
        self.all_projects = None

    def getProject( self, name ):
        return self.all_projects[ name ]

    def getAllProjects( self ):
        return self.all_projects.values()

    def addProject( self, project ):
        assert isinstance( project, Project )
        self.all_projects[ project.name ] = project

    def delProject( self, project_name ):
        del self.all_projects[ project_name ]

    def getAllBookmarks( self ):
        return self.all_bookmarks.values()

    def addBookmark( self, bookmark ):
        assert isinstance( project, Bookmark )
        self.all_bookmarks[ bookmark.name ] = bookmark

class MainWindow(PreferencesNode):
    xml_attribute_info = ('geometry',)

    def __init__( self ):
        super().__init__()

        self.geometry = None
        self.font = None
        self.all_colours = {}

    def getFrameGeometry( self ):
        return self.geometry

    def setFrameGeometry( self, geometry ):
        self.geometry = geometry.decode('utf-8')

class Font(PreferencesNode):
    xml_attribute_info = ('face', ('point_size', int))

    def __init__( self ):
        super().__init__()

        # point size and face need to chosen by platform
        if sys.platform.startswith( 'win' ):
            self.face = 'Courier New'
            self.point_size = 14

        elif sys.platform == 'darwin':
            self.face = 'Monaco'
            self.point_size = 14

        else:
            # Assuming linux/xxxBSD
            self.face = 'Liberation Mono'
            self.point_size = 11

class NamedColour(PreferencesNode):
    xml_attribute_info = (('fg', RGB), ('bg', RGB))

    def __init__( self, name, fg=None, bg=None ):
        super().__init__()

        self.name = name
        self.fg = fg
        self.bg = bg

    def __lt__( self, other ):
        return self.name < other.name

class Colour(PreferencesNode):
    xml_attribute_info = (('fg', RGB), ('bg', RGB))

    def __init__( self, fg=None, bg=None ):
        super().__init__()

        self.fg = fg
        self.bg = bg

class Editor(PreferencesNode):
    xml_attribute_info = ('program', 'options')

    def __init__( self ):
        super().__init__()

        self.program = ''
        self.options = ''

class Shell(PreferencesNode):
    xml_attribute_info = ('terminal_program', 'terminal_init', 'file_browser')

    def __init__( self ):
        super().__init__()

        self.terminal_program = ''
        self.terminal_init = ''
        self.file_browser = ''

class Bookmark(PreferencesNode):
    xml_attribute_info = ('project_name', ('path', pathlib.Path))

    def __init__( self, name=None, project_name=None, path=None ):
        super().__init__()

        assert project_name is None or isinstance( project_name, str )
        assert path is None or isinstance( path, pathlib.Path )

        self.name = name
        self.project_name = project_name
        self.path = path

class BookmarkCollection(PreferencesMapNode):
    def __init__( self ):
        super().__init__()

class Project(PreferencesNode):
    xml_attribute_info = ('scm_type', ('path', pathlib.Path))

    def __init__( self, name, scm_type=None, path=None ):
        super().__init__()

        assert path is None or isinstance( path, pathlib.Path )
        assert scm_type is None or scm_type in ('git','hg','svn')

        self.name = name
        self.scm_type = scm_type
        self.path = path

    def __lt__( self, other ):
        return self.name.lower() < other.name.lower()

    def __repr__( self ):
        return '<Project: name=%r scm=%r path=%r>' % (self.name, self.scm_type, self.path)

class ProjectCollection(PreferencesMapNode):
    def __init__( self ):
        super().__init__()

class View(PreferencesNode):
    xml_attribute_info = (('show_controlled', Bool), ('show_uncontrolled', Bool), ('show_ignored', Bool), ('show_only_changed', Bool))

    def __init__( self ):
        super().__init__()

        self.show_controlled = True
        self.show_uncontrolled = True
        self.show_ignored = False
        self.show_only_changed = False

        self.diff_style = 'side-by-side'

    def __repr__( self ):
        return ('<View: ctl=%r unctl=%r ig=%r only=%r diff=%r>' %
                (self.show_controlled, self.show_uncontrolled, self.show_ignored, self.show_only_changed, self.diff_style))

    def setDiffUnified( self ):
        self.diff_style = 'unified'

    def isDiffUnified( self ):
        return self.diff_style == 'unified'

    def setDiffSideBySide( self ):
        self.diff_style = 'side-by-side'

    def isDiffSideBySide( self ):
        return self.diff_style == 'side-by-side'

scheme_nodes = (
    (SchemeNode( Preferences, 'preferences',  )
    <<  SchemeNode( MainWindow, 'main_window' )
    <<  (SchemeNode( MainWindow, 'diff_window' )
        << SchemeNode( Colour, 'colour_normal', default_attributes={'fg': wb_config.diff_colour_normal} )
        << SchemeNode( Colour, 'colour_header', default_attributes={'fg': wb_config.diff_colour_header} )
        << SchemeNode( Colour, 'colour_insert_line', default_attributes={'fg': wb_config.diff_colour_insert_line} )
        << SchemeNode( Colour, 'colour_delete_line', default_attributes={'fg': wb_config.diff_colour_delete_line} )
        << SchemeNode( Colour, 'colour_change_line', default_attributes={'fg': wb_config.diff_colour_change_line} )
        << SchemeNode( Colour, 'colour_insert_char', default_attributes={'fg': wb_config.diff_colour_insert_char} )
        << SchemeNode( Colour, 'colour_delete_char', default_attributes={'fg': wb_config.diff_colour_delete_char} )
        << SchemeNode( Colour, 'colour_change_char', default_attributes={'fg': wb_config.diff_colour_change_char} )
        )
    <<  (SchemeNode( ProjectCollection, 'projects', store_as='all_projects' )
        << SchemeNode( Project, 'project', key_attribute='name' )
        )
    <<  (SchemeNode( BookmarkCollection, 'bookmarks', store_as='all_bookmarks' )
        << SchemeNode( Bookmark, 'bookmark', key_attribute='name')
        )
    <<  SchemeNode( Bookmark, 'last_position_bookmark', default=False )
    <<  SchemeNode( Editor, 'editor' )
    <<  SchemeNode( Shell, 'shell' )
    <<  SchemeNode( View, 'view' )
    )
)

class PreferencesManager:
    def __init__( self, log, filename, scheme, preferences_class ):
        self.log = log
        self.xml_prefs = XmlPreferences( scheme )

        self.prefs_filename = filename
        self.preferences_class = preferences_class

    def readPreferences( self ):
        try:
            self.prefs = self.xml_prefs.load( self.prefs_filename )

        except IOError as e:
            self.log.info( 'No preferences found' )
            # Assume its a missing file and default everything
            self.prefs = self.xml_prefs.default()

        except ParseError as e:
            self.log.error( 'Error parsing preferences: %s' % (str(e),) )
            self.prefs = self.xml_prefs.default()

        #self.prefs.dumpNode( sys.stdout )

    def getPreferences( self ):
        return self.prefs

    def writePreferences( self ):
        #self.prefs.dumpNode( sys.stdout )

        tmp_filename = self.prefs_filename.with_suffix( '.tmp' )

        self.xml_prefs.saveAs( self.prefs, tmp_filename )

        old_filename = self.prefs_filename.with_suffix( '.old.xml' )

        if self.prefs_filename.exists():
            if old_filename.exists():
                old_filename.unlink()

            self.prefs_filename.rename( old_filename )

        tmp_filename.rename( self.prefs_filename )
