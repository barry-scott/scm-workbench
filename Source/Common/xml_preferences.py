#
#   xml_preferences/__init__.py
#
import io

import xml.parsers.expat
import xml.dom.minidom
import xml.sax.saxutils

class ParseError(Exception):
    def __init__( self, value ):
        self.value = value

    def __str__( self ):
        return str(self.value)

    def __repr__( self ):
        return repr(self.value)

class XmlPreferences:
    def __init__( self, scheme ):
        self.scheme = scheme
        self.filename = None

    def load( self, filename ):
        # allow pathlib.Path as filename
        self.filename = str(filename)

        with open( self.filename, encoding='utf-8' ) as f:
            return self.loadString( f.read() )

    def saveAs( self, data_node, filename ):
        self.filename = str(filename)
        self.save( data_node )

    def save( self, data_node ):
        with open( self.filename, 'w', encoding='utf-8' ) as f:
            self.saveToFile( data_node, f )

    def saveToString( self, data_node ):
        with io.StringIO() as f:
            self.saveToFile( data_node, f )
            return f.getvalue()

    def saveToFile( self, data_node, f ):
        f.write( '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' )
        self.__saveNode( f, self.scheme.document_root, data_node )

    def loadString( self, text ):
        try:
            dom = xml.dom.minidom.parseString( text )

        except IOError as e:
            raise ParseError( str(e) )

        except xml.parsers.expat.ExpatError as e:
            raise ParseError( str(e) )

        return self.__loadNode( self.scheme.document_root, dom.documentElement )

    def __loadNode( self, scheme_node, xml_parent ):
        if scheme_node.key_attribute is not None:
            if not xml_parent.hasAttribute( scheme_node.key_attribute ):
                raise ParseError( 'Element %s missing mandated attribute %s' %
                        (scheme_node.element_name, scheme_node.key_attribute) )

            node = scheme_node.factory( xml_parent.getAttribute( scheme_node.key_attribute ) )

        else:
            node = scheme_node.factory()

        # load all attribute values in the node
        for attr_name, attr_type in scheme_node.all_attribute_info:
            # assume the factory creates an object that defaults all attributes
            if xml_parent.hasAttribute( attr_name ):
                node.setAttr( attr_name, attr_type( xml_parent.getAttribute( attr_name ) ) )

        children_processed = set()
        # look for supported child nodes
        for xml_child in xml_parent.childNodes:
            if xml_child.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
                if scheme_node._hasSchemeChild( xml_child.tagName ):
                    children_processed.add( xml_child.tagName )
                    scheme_child_node = scheme_node._getSchemeChild( xml_child.tagName )
                    child_node = self.__loadNode( scheme_child_node, xml_child )

                    if scheme_child_node.element_plurality:
                        if scheme_child_node.key_attribute is not None:
                            node.setChildNodeMap( scheme_child_node.collection_name, child_node.getAttr( scheme_child_node.key_attribute ), child_node )

                        else:
                            node.setChildNodeList( scheme_child_node.collection_name, child_node )

                    else:
                        node.setChildNode( scheme_child_node.store_as, child_node )

        # finalise all children that where missing from the XML
        # but marked as required
        for child_name in scheme_node._getAllSchemeChildNames():
            if child_name not in children_processed:
                scheme_child_node = scheme_node._getSchemeChild( child_name )
                # cannot default plural nodes
                if scheme_child_node.default:
                    child_node = self.__createDefaultNode( scheme_child_node )
                    node.setChildNode( scheme_child_node.store_as, child_node )

        # tell the node that it has all attributes and child nodes
        node.finaliseNode()

        return node

    def default( self ):
        return self.__createDefaultNode( self.scheme.document_root )

    def __createDefaultNode( self, scheme_node ):
        assert not scheme_node.element_plurality

        node = scheme_node.factory()

        # load all attribute values in the node from the available defaults
        for attr_name, attr_type in scheme_node.all_attribute_info:
            # assume the factory creates an object that defaults all attributes
            if attr_name in scheme_node.default_attributes:
                node.setAttr( attr_name, attr_type( scheme_node.default_attributes[ attr_name ] ) )

        for child_name in scheme_node._getAllSchemeChildNames():
            scheme_child_node = scheme_node._getSchemeChild( child_name )
            # cannot default plural nodes
            if scheme_child_node.default:
                child_node = self.__createDefaultNode( scheme_child_node )
                node.setChildNode( scheme_child_node.store_as, child_node )

        # tell the node that it has all attributes and child nodes
        node.finaliseNode()

        return node

    def __saveNode( self, f, scheme_node, data_node, indent=0 ):
        f.write( '%*s' '<%s' %
            (indent, '', scheme_node.element_name) )

        # deal with the special key_attribute
        if scheme_node.key_attribute is not None:
            value = data_node.getAttr( scheme_node.key_attribute )
            f.write( ' %s=%s' %
                (scheme_node.key_attribute
                ,xml.sax.saxutils.quoteattr( value )) )

        # save all attribute values that are not None
        for attr_name, attr_type in sorted( scheme_node.all_attribute_info ):
            value = data_node.getAttr( attr_name )
            if value is not None:
                # do simple coersion of value to str
                # if this is not what the user wants they
                # need to override the getAttr methods to
                # return a str encoding their data as they
                # require.
                if type(value) == bytes:
                    value = value.decode('utf-8')

                elif type(value) != str:
                    value = str(value)

                f.write( ' %s=%s' %
                    (attr_name
                    ,xml.sax.saxutils.quoteattr( value )) )

        if len( scheme_node.all_child_scheme_nodes ) == 0:
            f.write( '/>' '\n' )
            return

        f.write( '>' '\n' )

        # write child elements
        for child_name in sorted( scheme_node.all_child_scheme_nodes ):
            child_scheme = scheme_node.all_child_scheme_nodes[ child_name ]

            if child_scheme.element_plurality:
                if child_scheme.key_attribute is not None:
                    all_child_nodes = data_node.getChildNodeMap( child_scheme.collection_name )

                else:
                    all_child_nodes = data_node.getChildNodeList( child_scheme.collection_name )

            else:
                child_node = data_node.getChildNode( child_scheme.store_as )
                all_child_nodes = []
                if child_node is not None:
                    all_child_nodes.append( child_node )

            for child_data_node in all_child_nodes:
               self.__saveNode( f, child_scheme, child_data_node, indent+4 )

        f.write( '%*s' '</%s>' '\n' % (indent, '', scheme_node.element_name) )

class Scheme:
    def __init__( self, document_root ):
        self.document_root = document_root

    def dumpScheme( self, f ):
        f.write( 'Scheme document root: %r' '\n' % (self.document_root,) )
        self.document_root.dumpScheme( f, 4 )

class SchemeNode:
    #
    # factory makes a class that the parser will set the values of all
    # the present attributes found in the element_name.
    #
    # plurality is False if this node can apprear only once
    # or true is many can be present.
    #
    # when plurality is true the nodes can be store in a list of a dict.
    # set the key_attribute to store in a dict
    #
    # if default is true then create this node if it is missing from from the XML
    #
    def __init__( self, factory, element_name, all_attribute_info=None,
                    element_plurality=False, key_attribute=None, collection_name=None,
                    store_as=None, default=True, default_attributes=None ):
        self.parent_node = None
        self.factory = factory
        self.element_name = element_name
        self.store_as = store_as if store_as is not None else self.element_name
        self.element_plurality = element_plurality
        self.default = default
        self.default_attributes = default_attributes if default_attributes is not None else {}

        if all_attribute_info is None:
            if hasattr( self.factory, 'xml_attribute_info' ):
                all_attribute_info = self.factory.xml_attribute_info

            else:
                all_attribute_info = tuple()

        self.all_attribute_info = []
        for info in all_attribute_info:
            if type(info) == str:
                self.all_attribute_info.append( (info, str) )

            else:
                assert len(info) == 2
                assert type(info[0]) == str
                self.all_attribute_info.append( info )

        self.key_attribute = key_attribute

        # fix up when parent is set.
        self.collection_name = collection_name

        # convient defaulting
        if self.key_attribute is not None:
            self.element_plurality = True

        if self.element_plurality:
            # collections are not defaulted
            self.default = False

        self.all_child_scheme_nodes = {}

        assert key_attribute is None or key_attribute not in [name for name, type_ in self.all_attribute_info], 'must not put key_attribute in all_attribute_info'

    def __repr__( self ):
        return '<SchemeNode: %s>' % (self.element_name,)

    def dumpScheme( self, f, indent ):
        f.write( '%*s' 'SchemeNode %s store_as %r plurality %r key %r attr %r coll %r parent %r' '\n' %
                (indent, '', self.element_name, self.store_as, self.element_plurality, self.key_attribute, self.all_attribute_info, self.collection_name, self.parent_node) )

        for child_name in self.all_child_scheme_nodes:
            child = self.all_child_scheme_nodes[ child_name ]
            child.dumpScheme( f, indent+4 )

    def addSchemeChild( self, scheme_node ):
        self.all_child_scheme_nodes[ scheme_node.element_name ] = scheme_node
        scheme_node.setParentSchemeNode( self )
        return self

    def setParentSchemeNode( self, parent_node ):
        self.parent_node = parent_node

        if issubclass( self.parent_node.factory, PreferencesCollectionNode ):
            assert self.collection_name is None, 'collection_name cannot be set if parent is a collection node.'
            self.collection_name = 'data'

        elif self.collection_name is None and self.element_plurality:
            self.collection_name = self.store_as

    def __lshift__( self, scheme_node ):
        return self.addSchemeChild( scheme_node )

    def _hasSchemeChild( self, name ):
        return name in self.all_child_scheme_nodes

    def _getSchemeChild( self, name ):
        return self.all_child_scheme_nodes[ name ]

    def _getAllSchemeChildNames( self ):
        return self.all_child_scheme_nodes.keys()

class PreferencesNode:
    def __init__( self ):
        pass

    def finaliseNode( self ):
        # called after all attributes and children have been set
        pass

    # --- load ---
    def setAttr( self, name, value ):
        setattr( self, name, value )

    def setChildNode( self, name, node ):
        setattr( self, name, node )

    def setChildNodeList( self, collection_name, node ):
        getattr( self, collection_name ).append( node )

    def setChildNodeMap( self, collection_name, key, node ):
        assert key is not None
        getattr( self, collection_name )[ key ] = node

    # --- save ---
    def getAttr( self, name ):
        return getattr( self, name )

    def getChildNode( self, name ):
        return getattr( self, name )

    def getChildNodeList( self, collection_name ):
        return getattr( self, collection_name )

    def getChildNodeMap( self, collection_name ):
        collection = getattr( self, collection_name )
        return [collection[key] for key in sorted( collection.keys() )]

    # --- debug ---
    def dumpNode( self, f, indent=0, prefix='' ):
        f.write( '%*s' '%s%r:' '\n' % (indent, '', prefix, self) )
        indent += 4
        for name in sorted( dir( self ) ):
            if name.startswith( '_' ):
                continue
            value = getattr( self, name )

            if callable( value ):
                continue

            if isinstance( value, PreferencesNode ):
                value.dumpNode( f, indent, '%s -> ' % (name,) )

            else:
                f.write( '%*s' '%s -> %r' '\n' % (indent, '', name, value) )

# implement methods common to dict() and list()
class PreferencesCollectionNode(PreferencesNode):
    def __init__( self ):
        self.data = {}

    def __len__( self ):
        return len(self.data)

    def __getitem__( self, index ):
        return self.data[ index ]

    def __setitem__( self, index, value ):
        self.data[ index ] = value

    def __delitem__( self, index ):
        del self.data[ index ]

    def __iter__( self, index ):
        return iter( self.data )

    def __contains__( self, index ):
        return index in self.data

class PreferencesMapNode(PreferencesCollectionNode):
    def __init__( self ):
        super().__init__()
        self.data = {}

        self.keys = self.data.keys
        self.values = self.data.values
        self.items = self.data.items
        self.get = self.data.get
        self.clear = self.data.clear
        self.setdefault = self.data.setdefault
        self.pop = self.data.pop
        self.popitem = self.data.popitem
        self.copy = self.data.copy
        self.update = self.data.update

    def __repr__( self ):
        return '<%s %r>' % (self.__class__.__name__, list(self.data.keys()))

class PreferencesListNode(PreferencesCollectionNode):
    def __init__( self ):
        super().__init__()

        self.append = self.data.append
        self.count = self.data.count
        self.index = self.data.index
        self.extend = self.data.extend
        self.insert = self.data.insert
        self.pop = self.data.pop
        self.remove = self.data.remove
        self.reverse = self.data.reverse
        self.sort = self.data.sort

    def __add__( self, other ):
        return operator.__add__( self.data, other )

    def __radd__( self, other ):
        return operator.__radd__( self.data, other )

    def __iadd__( self, other ):
        return operator.__iadd__( self.data, other )

    def __mul__( self, other ):
        return operator.__mul__( self.data, other )

    def __rmul__( self, other ):
        return operator.__rmul__( self.data, other )

    def __imul__( self, other ):
        return operator.__imul__( self.data, other )
