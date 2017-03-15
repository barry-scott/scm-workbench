#!/usr/bin/env python3
import sys
import os
import pathlib

import xml.parsers.expat
import xml.dom.minidom
import xml.sax.saxutils


class Main:
    def __init__( self ):
        self.all_docs = {}
        self.exit_code = 0

    def main( self, argv ):
        self.parseHtml( 'scm-workbench.html' )

        return self.exit_code

    def parseHtml( self, filename ):
        print( 'Parsing %s in %s' % (filename, pathlib.Path.cwd()) )
        checker = CheckHtml( filename )
        self.all_docs[ filename ] = checker

        if not checker.isValid():
            checker.reportErrors()
            self.exit_code = 1

        for filename_anchor in checker.all_a_href_filenames:
            filename = filename_anchor.split( '#' )[0]
            # TODO: check the anchor in the other file

            if filename not in self.all_docs:
                if filename.startswith( ('http:', 'https:') ):
                    self.all_docs[ filename ] = None
                    print( 'External reference: %s' % (filename,) )

                else:
                    self.parseHtml( filename )

class CheckHtml:
    def __init__( self, filename ):
        self.filename = filename
        self.all_errors = []

        try:
            self.dom = xml.dom.minidom.parse( filename )

        except IOError as e:
            self.all_errors.append( str(e) )

        except xml.parsers.expat.ExpatError as e:
            self.all_errors.append( str(e) )

        self.all_a_href_filenames = set()
        self.all_a_href_anchors = set()
        self.all_a_names = set()
        self.all_img_src = set()

        if self.isValid():
            self.parse()

    def isValid( self ):
        return len(self.all_errors) == 0

    def reportErrors( self ):
        for error in self.all_errors:
            print( '%s: %s' % (self.filename, error) )

    def parse( self ):
        for img in self.dom.getElementsByTagName( 'img' ):
            if img.hasAttribute( 'src' ):
                self.all_img_src.add( img.getAttribute( 'src' ) )

        for img in sorted( self.all_img_src ):
            if not os.path.exists( img ):
                self.all_errors.append( 'Missing <img src="%s" />' % (img,) )

        for a in self.dom.getElementsByTagName( 'a' ):
            if a.hasAttribute( 'name' ):
                name = a.getAttribute( 'name' )
                if name in self.all_a_names:
                    self.all_errors.append( 'Duplicate <a name="%s">' % (name,) )
                self.all_a_names.add( name )

            elif a.hasAttribute( 'href' ):
                href = a.getAttribute( 'href' )
                if href.startswith( '#' ):
                    self.all_a_href_anchors.add( href[1:] )

                else:
                    self.all_a_href_filenames.add( href )

            else:
                self.all_errors.append( '<a> without href= or name=' )

        missing_names = self.all_a_href_anchors - self.all_a_names
        for name in sorted( missing_names ):
            self.all_errors.append( 'Missing <a name="%s">' % (name,) )

if __name__ == '__main__':
    sys.exit( Main().main( sys.argv ) )
