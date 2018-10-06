'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_preferences.py

'''
from typing import Sequence, Union, Any, Iterable

import pathlib

from xml_preferences import XmlPreferences, SchemeNode, PreferencesNode, PreferencesMapNode, ParseError, Scheme

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
        return '#%2.2x%2.2x%2.2x%2.2x' % (self.R, self.G, self.B, self.A)

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
    xml_attribute_info = tuple()    # type: Sequence[Union[str,Any]]

    def __init__( self ):
        super().__init__()

        self.font_ui = None                     # type: Font
        self.font_code = None                   # type: Font
        self.main_window = None                 # type: MainWindow
        self.diff_window = None                 # type: MainWindow
        self.last_position = None               # type: LastPosition
        self.all_favorites = {}                 # type: Dict[str, Favorite]
        self.all_favorites_by_path = {}
        self.all_projects = {}                  # type: Dict[str, Project]
        self.all_projects_by_path = {}

    def finaliseNode( self ):
        # optimise project and favorites lookups

        for project in self.all_projects.values():
            self.all_projects_by_path[ project.path ] = project

        for favorite in self.all_favorites.values():
            self.all_favorites_by_path[ favorite.keyPath() ] = favorite

    # -- projects
    def getProject( self, name:str ) -> 'Project':
        return self.all_projects[ name ]

    def getProjectByPath( self, path:pathlib.Path ):
        for project in self.all_projects.values():
            if project.path == path:
                return project


        assert False, 'No project with path %r' % (path,)

    def getProjectContainingPath( self, path:pathlib.Path ):
        for project in self.all_projects.values():
            try:
                rel_path = path.relative_to( project.path )
                return project, rel_path

            except ValueError:
                pass

        return None, None

    def getAllProjects( self ) -> Iterable['Project']:
        return self.all_projects.values()

    def addProject( self, project:'Project' ) -> None:
        assert isinstance( project, Project )
        assert project.name not in self.all_projects

        self.all_projects[ project.name ] = project
        self.all_projects_by_path[ project.path ] = project

    def delProject( self, project_name:str ) -> None:
        project = self.all_projects.pop( project_name )
        del self.all_projects_by_path[ project.path ]

        # del any favorites that point to this project
        all_to_del = set()
        for favorite in self.all_favorites.values():
            if favorite.project_path == project.path:
                all_to_del.add( favorite.menu )

        for menu in all_to_del:
            self.delFavorite( menu )

    def renameProject( self, old_project_name:str, new_project_name:str ) -> None:
        # do not call delProject as it removes the favorites
        project = self.all_projects.pop( old_project_name )
        del self.all_projects_by_path[ project.path ]

        project.name = new_project_name
        self.addProject( project )

    # -- favorites
    def getFavoriteByMenu( self, menu:str ) -> 'Favorite':
        return self.all_favorites[ menu ]

    def hasFavoriteByProjectAndPath( self, project_path:pathlib.Path, path:pathlib.Path ):
        return (project_path, path) in self.all_favorites_by_path

    def getFavoriteByProjectAndPath( self, project_path:pathlib.Path, path:pathlib.Path ):
        return self.all_favorites_by_path[ (project_path, path) ]

    def hasMenu( self, menu:str ) -> Bool:
        return menu in self.all_favorites

    def getAllFavorites( self ) -> Iterable['Favorite']:
        return self.all_favorites.values()

    def addFavorite( self, favorite:'Favorite' ) -> None:
        assert isinstance( favorite, Favorite )
        self.all_favorites[ favorite.menu ] = favorite
        self.all_favorites_by_path[ favorite.keyPath() ] = favorite

    def delFavorite( self, menu:str ) -> None:
        favorite = self.all_favorites.pop( menu )
        del self.all_favorites_by_path[ favorite.keyPath() ]

    def renameFavorite( self, old_menu, new_menu ):
        favorite = self.all_favorites.pop( old_menu )
        favorite.menu = new_menu
        self.addFavorite( favorite )

class MainWindow(PreferencesNode):
    xml_attribute_info = ('geometry', 'title')

    def __init__( self ) -> None:
        super().__init__()

        self.geometry = None    # type: str
        self.all_colours = {}   # type: Dict[str, Colour]
        self.title = None

    def getFrameGeometry( self ) -> str:
        return self.geometry

    def setFrameGeometry( self, geometry:bytes ) -> None:
        self.geometry = geometry.decode('utf-8')

class Font(PreferencesNode):
    xml_attribute_info = ('face', ('point_size', int))

    def __init__( self ) -> None:
        super().__init__()

        self.face = None        # type: str
        self.point_size = None  # type: int

class NamedColour(PreferencesNode):
    xml_attribute_info = (('fg', RGB), ('bg', RGB))

    def __init__( self, name:str, fg:RGB=None, bg:RGB=None ) -> None:
        super().__init__()

        self.name = name
        self.fg = fg
        self.bg = bg

    def __lt__( self, other:'NamedColour' ):
        return self.name < other.name

class Colour(PreferencesNode):
    xml_attribute_info = (('fg', RGB), ('bg', RGB))

    def __init__( self, fg:RGB=None, bg:RGB=None ) -> None:
        super().__init__()

        self.fg = fg
        self.bg = bg

class Editor(PreferencesNode):
    xml_attribute_info = ('program', 'options')

    def __init__( self ) -> None:
        super().__init__()

        self.program = ''
        self.options = ''

class Shell(PreferencesNode):
    xml_attribute_info = ('terminal_program', 'terminal_init', 'file_browser')

    def __init__( self ) -> None:
        super().__init__()

        self.terminal_program = ''
        self.terminal_init = ''
        self.file_browser = ''

class LastPosition(PreferencesNode):
    xml_attribute_info = (('project_path', pathlib.Path), ('path', pathlib.Path))

    def __init__( self, project_path:str=None, path:pathlib.Path=None ) -> None:
        super().__init__()

        assert project_path is None or isinstance( project_path, pathlib.Path )
        assert path is None or isinstance( path, pathlib.Path )

        self.project_path = project_path
        self.path = path

class Favorite(PreferencesNode):
    xml_attribute_info = (('project_path', pathlib.Path), ('path', pathlib.Path))

    def __init__( self, menu:str=None, project_path:pathlib.Path=None, path:pathlib.Path=None ) -> None:
        super().__init__()

        assert menu is not None or isinstance( menu, str )
        assert project_path is None or isinstance( project_path, pathlib.Path )
        assert path is None or isinstance( path, pathlib.Path )

        self.menu = menu
        self.project_path = project_path
        self.path = path

    def keyPath( self ):
        return (self.project_path, self.path)

class FavoritesCollection(PreferencesMapNode):
    def __init__( self ) -> None:
        super().__init__()

class Project(PreferencesNode):
    xml_attribute_info = ('scm_type', ('path', pathlib.Path), 'tags_url', 'master_branch_name')

    def __init__( self, name:str, scm_type:str=None, path:pathlib.Path=None, tags_url:str=None, master_branch_name:str=None ) -> None:
        super().__init__()

        assert path is None or isinstance( path, pathlib.Path ), 'path is %r' % (path,)
        assert scm_type is None or scm_type in ('git','hg','svn', 'p4'), 'scm_type is %r' % (scm_type,)

        self.name = name
        self.scm_type = scm_type
        self.path = path
        self.tags_url = tags_url
        self.master_branch_name = master_branch_name

    def __lt__( self, other:'Project' ) -> bool:
        return self.name.lower() < other.name.lower()

    def __repr__( self ) -> str:
        return '<Project: name=%r scm=%r path=%r>' % (self.name, self.scm_type, self.path)

class ProjectCollection(PreferencesMapNode):
    def __init__( self ) -> None:
        super().__init__()

class View(PreferencesNode):
    xml_attribute_info = (('show_controlled', Bool), ('show_uncontrolled', Bool), ('show_ignored', Bool), ('show_only_changed', Bool))

    def __init__( self ) -> None:
        super().__init__()

        self.show_controlled = True
        self.show_uncontrolled = True
        self.show_ignored = False
        self.show_only_changed = False

        self.diff_style = 'side-by-side'

    def __repr__( self ) -> str:
        return ('<View: ctl=%r unctl=%r ig=%r only=%r diff=%r>' %
                (self.show_controlled, self.show_uncontrolled, self.show_ignored, self.show_only_changed, self.diff_style))

    def setDiffUnified( self ) -> bool:
        self.diff_style = 'unified'

    def isDiffUnified( self ) -> bool:
        return self.diff_style == 'unified'

    def setDiffSideBySide( self ) -> bool:
        self.diff_style = 'side-by-side'

    def isDiffSideBySide( self ) -> bool:
        return self.diff_style == 'side-by-side'

scheme_nodes = (
    (SchemeNode( Preferences, 'preferences',  )
    <<  SchemeNode( Font, 'font_ui' )
    <<  SchemeNode( Font, 'font_code' )
    <<  SchemeNode( MainWindow, 'main_window' )
    <<  (SchemeNode( MainWindow, 'diff_window' )
        << SchemeNode( Colour, 'colour_normal', default_attributes={'fg': wb_config.diff_light_colour_normal} )
        << SchemeNode( Colour, 'colour_header', default_attributes={'fg': wb_config.diff_light_colour_header} )
        << SchemeNode( Colour, 'colour_insert_line', default_attributes={'fg': wb_config.diff_light_colour_insert_line} )
        << SchemeNode( Colour, 'colour_delete_line', default_attributes={'fg': wb_config.diff_light_colour_delete_line} )
        << SchemeNode( Colour, 'colour_change_line', default_attributes={'fg': wb_config.diff_light_colour_change_line} )
        << SchemeNode( Colour, 'colour_insert_char', default_attributes={'fg': wb_config.diff_light_colour_insert_char} )
        << SchemeNode( Colour, 'colour_delete_char', default_attributes={'fg': wb_config.diff_light_colour_delete_char} )
        << SchemeNode( Colour, 'colour_change_char', default_attributes={'fg': wb_config.diff_light_colour_change_char} )
        )
    <<  (SchemeNode( ProjectCollection, 'projects', store_as='all_projects' )
        << SchemeNode( Project, 'project', key_attribute='name' )
        )
    <<  (SchemeNode( FavoritesCollection, 'favorites', store_as='all_favorites' )
        << SchemeNode( Favorite, 'favorite', key_attribute='menu')
        )
    <<  SchemeNode( LastPosition, 'last_position', default=False )
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
        self.prefs = None

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
